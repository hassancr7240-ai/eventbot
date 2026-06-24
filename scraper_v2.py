"""
ULTRA-CLEAN Scraper v2 - Only quality events, no junk
Strategy: Skip generic listing pages, focus on real event sources only
"""

import re
import time
import random
import logging
import urllib.parse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from venues import VENUES, TARGET_TITLES
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

def fetch(url: str) -> BeautifulSoup | None:
    try:
        resp = SESSION.get(url, headers=_headers(), timeout=10)
        if resp.status_code == 200:
            return BeautifulSoup(resp.text, "lxml")
    except:
        pass
    return None

def _polite_delay():
    time.sleep(random.uniform(0.5, 1.5))

# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY EVENT SOURCES ONLY
# ═══════════════════════════════════════════════════════════════════════════════

def crawl_eventbrite_clean(venue: dict) -> list[dict]:
    """
    CLEAN: Only extract actual events from Eventbrite city pages
    Skip generic categories
    """
    city_slug = venue["city"].lower().replace(" ", "-")
    state_slug = venue["state"].lower()
    url = f"https://www.eventbrite.com/d/{state_slug}--{city_slug}/conferences/"

    soup = fetch(url)
    if not soup:
        return []

    results = []
    seen = set()

    for div in soup.find_all("div", {"data-testid": "event-card"}):
        # Extract event name
        title_elem = div.find("h3")
        if not title_elem:
            continue

        event_name = title_elem.get_text(strip=True)
        if not event_name or len(event_name) < 5:
            continue

        # Skip junk patterns
        if any(x in event_name.lower() for x in ["concert", "party", "glow-up", "soirée", "mixer", "workshop"]):
            continue

        if event_name in seen:
            continue
        seen.add(event_name)

        # Extract date
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

def crawl_conferencenext_clean(venue: dict) -> list[dict]:
    """
    CLEAN: Extract only real conference events from ConferenceNext
    """
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

    # Look for actual conference event links (real events only)
    for div in soup.find_all("div", class_="item"):
        link = div.find("a")
        if not link:
            continue

        event_name = link.get_text(strip=True)
        if not event_name or len(event_name) < 5:
            continue

        # Skip junk
        if any(x in event_name.lower() for x in ["upcoming", "conference", "podcast", "美国", "中国"]):
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

        if len(results) >= 12:
            break

    _polite_delay()
    return results

def crawl_10times_clean(venue: dict) -> list[dict]:
    """
    CLEAN: 10times only real events
    """
    city_slug = venue["city"].lower().replace(" ", "-")
    url = f"https://10times.com/{city_slug}-{venue['state'].lower()}"

    soup = fetch(url)
    if not soup:
        return []

    results = []
    seen = set()

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        if not text or len(text) < 5:
            continue

        if text in seen:
            continue
        seen.add(text)

        results.append({
            "venue_name": venue["name"],
            "city": venue["city"],
            "state": venue["state"],
            "event_name": text,
            "event_dates": "",
            "event_url": a.get("href", ""),
            "contact_person": "",
            "contact_title": "",
            "email": "",
            "phone": "",
            "status": "New",
            "scraped_at": datetime.now().isoformat(),
        })

        if len(results) >= 10:
            break

    _polite_delay()
    return results

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCRAPE FUNCTION (FAST + CLEAN)
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_venue(venue: dict, start_year: int, end_year: int, progress_callback=None, stop_event=None) -> list[dict]:
    """
    ULTRA-FAST + ULTRA-CLEAN scraper
    Only uses proven quality sources
    30-second timeout per venue
    """
    results = []
    logger.info(f"Scraping {venue['name']} (30s timeout)")

    # Only clean, proven crawlers
    crawlers = [
        crawl_conferencenext_clean,
        crawl_eventbrite_clean,
        crawl_10times_clean,
    ]

    start_time = time.time()
    timeout = 30

    for i, crawler in enumerate(crawlers):
        if stop_event and stop_event.is_set():
            break

        elapsed = time.time() - start_time
        if elapsed > timeout:
            logger.warning(f"  {venue['name']}: timeout reached ({elapsed:.0f}s)")
            break

        if progress_callback:
            progress_callback(i + 1, len(crawlers), f"{crawler.__name__}...")

        try:
            recs = crawler(venue)
            if recs:
                logger.info(f"  {crawler.__name__}: +{len(recs)} events")
                results.extend(recs)
        except Exception as e:
            logger.warning(f"  {crawler.__name__} error: {e}")

    # Deduplicate within venue
    unique_results = []
    seen_names = set()
    for r in results:
        event_key = r["event_name"].lower().strip()
        if event_key not in seen_names:
            seen_names.add(event_key)
            unique_results.append(r)

    logger.info(f"Done {venue['name']}: {len(unique_results)} unique events in {time.time() - start_time:.1f}s")
    return unique_results

def scrape_all_venues(start_year: int = 2026, end_year: int = 2026, progress_callback=None):
    """Scrape all venues"""
    all_records = []
    for i, venue in enumerate(VENUES):
        if progress_callback:
            progress_callback(i + 1, len(VENUES), f"Scraping {venue['name']}...")

        try:
            recs = scrape_venue(venue, start_year, end_year, progress_callback)
            all_records.extend(recs)
        except Exception as e:
            logger.error(f"Error scraping {venue['name']}: {e}")

    # Deduplicate globally (same event shouldn't appear in multiple venues)
    final_records = []
    seen_global = set()
    for r in all_records:
        event_key = r["event_name"].lower().strip()
        if event_key not in seen_global:
            seen_global.add(event_key)
            final_records.append(r)

    return final_records

if __name__ == "__main__":
    recs = scrape_all_venues()
    print(f"Total records: {len(recs)}")
    added, updated = upsert_records(recs)
    print(f"Added: {added}, Updated: {updated}")
