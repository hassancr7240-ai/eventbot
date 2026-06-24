"""
FINAL Scraper - Smart Search for REAL Events
Strategy: Search by CITY + MONTH + YEAR (not venue)
Then filter results to only include conferences/events at that venue
"""

import re
import time
import random
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from venues import VENUES

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

SESSION = requests.Session()
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[\s\-.]?)?(?:\(?\d{3}\)?[\s\-\.])\d{3}[\s\-\.]\d{4}")

def _headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

def fetch(url: str, timeout: int = 10) -> BeautifulSoup | None:
    try:
        resp = SESSION.get(url, headers=_headers(), timeout=timeout)
        if resp.status_code == 200:
            return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.debug(f"Fetch error: {e}")
    return None

def _polite_delay(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))

# ═══════════════════════════════════════════════════════════════════════════════
# GOOGLE SEARCH - SMART QUERIES
# ═══════════════════════════════════════════════════════════════════════════════

def google_search_events(query: str, num_results: int = 5) -> list[str]:
    """
    Google search - simple queries that work
    """
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=num_results, lang="en", sleep_interval=10):
            # Skip obvious junk domains
            if any(x in url.lower() for x in ["facebook.com", "twitter.com", "instagram.com", "linkedin.com", "youtube.com"]):
                continue
            results.append(url)
            if len(results) >= num_results:
                break
        return results
    except Exception as e:
        logger.debug(f"Google search error: {e}")
        return []

def extract_events_from_page(soup: BeautifulSoup, venue_name: str, city: str) -> list[dict]:
    """
    Extract ALL event-like text from a page
    Look for patterns like:
    - Event name + date
    - Event name + "@ [venue]"
    - Structured event listings
    """
    if not soup:
        return []

    events = []
    seen_events = set()

    try:
        # Get full page text
        full_text = soup.get_text(separator=" ", strip=True)

        # Look for date patterns: "October 15", "Nov 2026", etc
        date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,?\s+20\d{2})?"
        dates = re.findall(date_pattern, full_text, re.IGNORECASE)

        # Look for event name patterns (text before/after dates)
        lines = full_text.split(".")
        for line in lines:
            line = line.strip()
            if len(line) < 5 or len(line) > 500:
                continue

            # Check if line contains date AND venue name (good signal)
            has_date = any(d in line for d in dates)
            has_venue = any(vpart in line.lower() for vpart in [venue_name.lower(), city.lower()])

            if not (has_date and has_venue):
                continue

            # Extract potential event name
            # Remove common junk patterns
            event_name = line
            event_name = re.sub(r"^(the|a)\s+", "", event_name, flags=re.IGNORECASE)

            # Skip if too short or obvious junk
            if len(event_name) < 5:
                continue
            if any(x in event_name.lower() for x in ["cookie", "policy", "terms", "copyright", "privacy", "contact us"]):
                continue

            event_key = event_name.lower().strip()
            if event_key in seen_events:
                continue
            seen_events.add(event_key)

            # Extract date from this line
            event_date_match = re.search(date_pattern, line, re.IGNORECASE)
            event_date = event_date_match.group(0) if event_date_match else ""

            events.append({
                "venue_name": venue_name,
                "city": city,
                "state": "MD",
                "event_name": event_name[:200],
                "event_dates": event_date,
                "event_url": "",
                "contact_person": "",
                "contact_title": "",
                "email": "",
                "phone": "",
                "status": "New",
                "scraped_at": datetime.now().isoformat(),
            })

            if len(events) >= 5:
                break

    except Exception as e:
        logger.debug(f"Error extracting events: {e}")

    return events

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCRAPE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_venue(venue: dict, start_year: int, end_year: int, progress_callback=None, stop_event=None) -> list[dict]:
    """
    Search for events at this venue:
    1. Search by city + month + year (broad)
    2. Extract events from pages
    3. Filter to only this venue
    """
    results = []
    logger.info(f"Scraping {venue['name']}")

    start_time = time.time()
    timeout = 60  # 1 minute per venue

    # Build search queries: "conference [Month] [Year] [City] [State]"
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    seen_global = set()

    queries = []
    for year in range(start_year, end_year + 1):
        for month in months:
            # Search by city + month + year (NOT venue-specific, broader results)
            query = f"conference {month} {year} {venue['city']} {venue['state']}"
            queries.append(query)

    logger.info(f"  {len(queries)} Google searches for {venue['name']}")

    for i, query in enumerate(queries):
        if stop_event and stop_event.is_set():
            break

        elapsed = time.time() - start_time
        if elapsed > timeout:
            logger.warning(f"  Timeout ({elapsed:.0f}s) - skipping remaining searches")
            break

        if progress_callback:
            progress_callback(i + 1, len(queries), f"{query[:50]}...")

        logger.info(f"  [{i+1}/{len(queries)}] {query}")

        # Search Google
        urls = google_search_events(query, num_results=5)
        logger.info(f"    Found {len(urls)} URLs")

        for url in urls:
            if stop_event and stop_event.is_set():
                break

            _polite_delay(2, 4)

            soup = fetch(url, timeout=15)
            if not soup:
                continue

            # Extract events from this page
            page_events = extract_events_from_page(soup, venue["name"], venue["city"])
            logger.info(f"    Extracted {len(page_events)} events from URL")

            for event in page_events:
                event_key = event["event_name"].lower().strip()
                if event_key not in seen_global:
                    seen_global.add(event_key)
                    results.append(event)

        # Longer delay between Google searches
        _polite_delay(10, 15)

    logger.info(f"Done {venue['name']}: {len(results)} unique events")
    return results

def scrape_all_venues(start_year: int = 2026, end_year: int = 2026):
    """Scrape all venues"""
    from deduplicator import upsert_records

    all_records = []

    for i, venue in enumerate(VENUES):
        logger.info(f"[{i+1}/{len(VENUES)}] {venue['name']}")

        try:
            recs = scrape_venue(venue, start_year, end_year)
            all_records.extend(recs)
            logger.info(f"  Total so far: {len(all_records)} events")
        except Exception as e:
            logger.error(f"Error: {e}")

    # Final global dedup
    final = []
    seen = set()
    for r in all_records:
        key = r["event_name"].lower().strip()
        if key not in seen:
            seen.add(key)
            final.append(r)

    logger.info(f"\n{'='*60}")
    logger.info(f"FINAL: {len(final)} unique events from all venues")
    logger.info(f"{'='*60}\n")

    # Save to database
    added, updated = upsert_records(final)
    logger.info(f"Database: +{added} added, ~{updated} updated")

    return final

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    scrape_all_venues(2026, 2026)
