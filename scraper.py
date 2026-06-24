"""
EventBot Scraper - WORKING VERSION
Uses Eventbrite directly (no Google search timeouts)
Fast, reliable, real results
"""

import json
import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "data", "current_results.json")

def load_results():
    """Load existing results"""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return []

def save_results(results):
    """Save results to file"""
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

def scrape_eventbrite(venue_name: str, city: str, start_date: str, end_date: str) -> list:
    """
    Scrape Eventbrite for events
    LIVE: Saves results to file as they're found so UI updates in real-time
    """
    results_file = os.path.join(os.path.dirname(__file__), "data", "current_results.json")
    results = load_results()

    try:
        # Eventbrite API-like URL construction
        city_slug = city.lower().replace(" ", "-")

        # Search URL
        url = f"https://www.eventbrite.com/d/{city_slug}--{city_slug}/events/?start_date={start_date}&end_date={end_date}"

        logger.info(f"Fetching: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"HTTP {resp.status_code}")
            return results

        soup = BeautifulSoup(resp.text, "html.parser")

        # Find event cards
        for card in soup.find_all("div", {"data-testid": "event-card"}):
            try:
                # Event name
                title_elem = card.find("h3")
                if not title_elem:
                    continue

                event_name = title_elem.get_text(strip=True)

                # Date
                date_elem = card.find("span", {"data-testid": "event-date-time-inner"})
                event_date = date_elem.get_text(strip=True) if date_elem else ""

                # Skip if no name
                if len(event_name) < 3:
                    continue

                event = {
                    "event_name": event_name,
                    "event_dates": event_date,
                    "venue_name": venue_name,
                    "city": city,
                    "contact_person": "",
                    "contact_title": "",
                    "email": "",
                    "phone": "",
                    "event_url": url,
                    "scraped_at": datetime.now().isoformat()
                }

                # Check if already exists
                existing_names = set([e["event_name"].lower() for e in results])
                if event_name.lower() not in existing_names:
                    results.append(event)
                    save_results(results)  # SAVE IMMEDIATELY so UI sees it
                    logger.info(f"  Found & saved: {event_name[:60]}")

            except Exception as e:
                logger.debug(f"Error parsing card: {e}")
                continue

        logger.info(f"Total from Eventbrite: {len(results)}")

    except Exception as e:
        logger.error(f"Eventbrite scrape error: {e}")

    return results

def scrape_venue_simple(venue_name: str, city: str, start_date: str, end_date: str) -> list:
    """
    Simple fast scrape for one venue
    """
    logger.info(f"Scraping {venue_name} ({start_date} to {end_date})")

    # Load existing results
    current = load_results()

    # Scrape Eventbrite
    new_events = scrape_eventbrite(venue_name, city, start_date, end_date)

    # Add new events (avoid duplicates by name)
    existing_names = set([e["event_name"].lower() for e in current])

    added = 0
    for event in new_events:
        if event["event_name"].lower() not in existing_names:
            current.append(event)
            existing_names.add(event["event_name"].lower())
            added += 1

    # Save
    save_results(current)

    logger.info(f"Added {added} new events | Total: {len(current)}")

    return current

if __name__ == "__main__":
    # Test
    results = scrape_venue_simple("DC Convention Center", "Washington", "2026-06-01", "2026-12-31")
    print(f"Found {len(results)} events")
