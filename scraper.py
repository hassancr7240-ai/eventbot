"""
HYBRID Scraper v3 - Smart Google Search + Industry Sources
Searches: "conference October 2026 [Venue Name] [City]"
Result: Real events + Clean deduplication
"""

import re
import time
import random
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from venues import VENUES, EVENT_TYPES
from deduplicator import upsert_records

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
        logger.debug(f"Fetch error {url}: {e}")
    return None

def _polite_delay(min_s=0.5, max_s=1.5):
    time.sleep(random.uniform(min_s, max_s))

# ═══════════════════════════════════════════════════════════════════════════════
# SMART GOOGLE SEARCH FOR REAL EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

def google_search_events(query: str, num_results: int = 5) -> list[str]:
    """
    Google search with long delays to avoid blocking
    Returns list of URLs
    """
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=num_results, lang="en", sleep_interval=10):
            # Filter out junk domains
            if any(x in url.lower() for x in ["facebook", "twitter", "instagram", "linkedin", "youtube", "reddit", "wikipedia"]):
                continue
            results.append(url)
            if len(results) >= num_results:
                break
        return results
    except Exception as e:
        logger.debug(f"Google search failed for '{query}': {e}")
        return []

def extract_event_from_page(soup: BeautifulSoup, url: str, venue_name: str) -> dict | None:
    """
    Try to extract event details from a page
    Returns event dict or None
    """
    if not soup:
        return None

    try:
        # Extract event name (look for h1, h2, title)
        event_name = ""
        for tag in soup.find_all(["h1", "h2", "title"]):
            text = tag.get_text(strip=True)
            if len(text) > 5 and len(text) < 200:
                event_name = text
                break

        if not event_name:
            return None

        # Skip junk patterns
        skip_patterns = ["404", "error", "not found", "log in", "sign up", "confirm email"]
        if any(p in event_name.lower() for p in skip_patterns):
            return None

        # Try to find dates in page
        full_text = soup.get_text()
        date_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}", full_text, re.IGNORECASE)
        event_dates = date_match.group(0) if date_match else ""

        # Try to find email
        emails = EMAIL_RE.findall(full_text)
        email = emails[0].lower() if emails else ""

        # Try to find phone
        phones = PHONE_RE.findall(full_text)
        phone = phones[0] if phones else ""

        return {
            "venue_name": venue_name,
            "city": venue_name.split()[-1] if venue_name else "",
            "state": "MD",  # Default, could extract better
            "event_name": event_name[:200],
            "event_dates": event_dates,
            "event_url": url,
            "contact_person": "",
            "contact_title": "",
            "email": email,
            "phone": phone,
            "status": "New",
            "scraped_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.debug(f"Error extracting from {url}: {e}")

    return None

# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY INDUSTRY SOURCES (FAST)
# ═══════════════════════════════════════════════════════════════════════════════

def crawl_conferencenext_clean(venue: dict) -> list[dict]:
    """Extract real conference events from ConferenceNext"""
    city_map = {
        "Washington": "washington-dc",
        "National Harbor": "washington-dc",
        "Bethesda": "washington-dc",
        "Baltimore": "baltimore",
        "Philadelphia": "philadelphia",
        "Wilmington": "wilmington",
    }
    city_slug = city_map.get(venue["city"], venue["city"].lower().replace(" ", "-"))
    url = f"https://conferencenext.com/conferences/{city_slug}"

    soup = fetch(url)
    if not soup:
        return []

    results = []
    seen = set()

    for div in soup.find_all("div", class_="item"):
        link = div.find("a")
        if not link:
            continue

        event_name = link.get_text(strip=True)
        if not event_name or len(event_name) < 5:
            continue

        # Skip junk
        if any(x in event_name.lower() for x in ["upcoming", "conference next", "podcast", "美国", "中国"]):
            continue

        if event_name in seen:
            continue
        seen.add(event_name)

        href = link.get("href", "")
        event_url = href if href.startswith("http") else url

        results.append({
            "venue_name": venue["name"],
            "city": venue["city"],
            "state": venue["state"],
            "event_name": event_name,
            "event_dates": "",
            "event_url": event_url,
            "contact_person": "",
            "contact_title": "",
            "email": "",
            "phone": "",
            "status": "New",
            "scraped_at": datetime.now().isoformat(),
        })

        if len(results) >= 15:
            break

    _polite_delay()
    return results

def crawl_eventbrite_clean(venue: dict) -> list[dict]:
    """Extract real conference events from Eventbrite"""
    city_slug = venue["city"].lower().replace(" ", "-")
    state_slug = venue["state"].lower()
    url = f"https://www.eventbrite.com/d/{state_slug}--{city_slug}/conferences/"

    soup = fetch(url)
    if not soup:
        return []

    results = []
    seen = set()

    for div in soup.find_all("div", {"data-testid": "event-card"}):
        title_elem = div.find("h3")
        if not title_elem:
            continue

        event_name = title_elem.get_text(strip=True)
        if not event_name or len(event_name) < 5:
            continue

        # Skip obvious junk
        skip = ["concert", "party", "glow-up", "soirée", "mixer", "workshop", "networking event"]
        if any(x in event_name.lower() for x in skip):
            continue

        if event_name in seen:
            continue
        seen.add(event_name)

        date_elem = div.find("span", {"data-testid": "event-date-time-inner"})
        event_dates = date_elem.get_text(strip=True) if date_elem else ""

        results.append({
            "venue_name": venue["name"],
            "city": venue["city"],
            "state": venue["state"],
            "event_name": event_name,
            "event_dates": event_dates,
            "event_url": url,
            "contact_person": "",
            "contact_title": "",
            "email": "",
            "phone": "",
            "status": "New",
            "scraped_at": datetime.now().isoformat(),
        })

        if len(results) >= 15:
            break

    _polite_delay()
    return results

# ═══════════════════════════════════════════════════════════════════════════════
# HYBRID SCRAPE - SMART GOOGLE SEARCH + INDUSTRY SOURCES
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_venue(venue: dict, start_year: int, end_year: int, progress_callback=None, stop_event=None) -> list[dict]:
    """
    HYBRID approach:
    1. Try smart Google searches: "conference [Month] [Year] [Venue Name] [City]"
    2. Fallback to industry sources (ConferenceNext, Eventbrite)
    3. Global dedup at end
    """
    results = []
    logger.info(f"Scraping {venue['name']} (hybrid: Google + industry)")

    start_time = time.time()
    timeout = 45  # Extended for Google searches

    # PHASE 1: Smart Google searches
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    search_phrases = []

    for year in range(start_year, end_year + 1):
        for month in months:
            search_phrases.append(f"conference {month} {year} {venue['search_name']} {venue['city']}")

    logger.info(f"  Searching {len(search_phrases)} Google queries...")

    seen_events = set()

    for i, phrase in enumerate(search_phrases):
        if stop_event and stop_event.is_set():
            break

        elapsed = time.time() - start_time
        if elapsed > timeout:
            logger.warning(f"  Timeout reached ({elapsed:.0f}s), skipping remaining searches")
            break

        if progress_callback:
            progress_callback(i + 1, len(search_phrases), f"Searching: {phrase[:50]}...")

        logger.info(f"  [{i+1}/{len(search_phrases)}] {phrase}")

        urls = google_search_events(phrase, num_results=3)

        for url in urls:
            if stop_event and stop_event.is_set():
                break

            _polite_delay(2, 4)

            soup = fetch(url, timeout=15)
            if not soup:
                continue

            event = extract_event_from_page(soup, url, venue["name"])
            if event and event["event_name"] not in seen_events:
                seen_events.add(event["event_name"])
                results.append(event)
                logger.info(f"    Found: {event['event_name'][:60]}")

        _polite_delay(10, 15)  # Respect Google's rate limits

    # PHASE 2: Fallback to industry sources
    logger.info(f"  Checking industry sources...")

    for crawler in [crawl_conferencenext_clean, crawl_eventbrite_clean]:
        if stop_event and stop_event.is_set():
            break

        elapsed = time.time() - start_time
        if elapsed > timeout:
            break

        try:
            recs = crawler(venue)
            for r in recs:
                if r["event_name"] not in seen_events:
                    seen_events.add(r["event_name"])
                    results.append(r)
                    logger.info(f"    {crawler.__name__}: {r['event_name'][:60]}")
        except Exception as e:
            logger.warning(f"  {crawler.__name__} error: {e}")

    logger.info(f"Done {venue['name']}: {len(results)} unique events in {time.time() - start_time:.1f}s")
    return results

def scrape_all_venues(start_year: int = 2026, end_year: int = 2026, progress_callback=None):
    """Scrape all venues using hybrid method"""
    all_records = []

    for i, venue in enumerate(VENUES):
        if progress_callback:
            progress_callback(i + 1, len(VENUES), f"Scraping {venue['name']}...")

        logger.info(f"[{i+1}/{len(VENUES)}] {venue['name']}")

        try:
            recs = scrape_venue(venue, start_year, end_year, progress_callback)
            all_records.extend(recs)
        except Exception as e:
            logger.error(f"Error scraping {venue['name']}: {e}")

    # Global dedup
    final_records = []
    seen_global = set()

    for r in all_records:
        event_key = r["event_name"].lower().strip()
        if event_key not in seen_global:
            seen_global.add(event_key)
            final_records.append(r)

    logger.info(f"Total unique events: {len(final_records)}")
    return final_records

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    recs = scrape_all_venues()
    print(f"Found {len(recs)} events")
    added, updated = upsert_records(recs)
    print(f"Added: {added}, Updated: {updated}")
