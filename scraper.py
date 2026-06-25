"""
EventBot Scraper - REAL VERSION
Actually scrapes Eventbrite and extracts real contact info
Streams results LIVE to UI as they're found
"""

import json
import os
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import re

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

def extract_contact_from_event_page(event_url):
    """Visit event page and extract contact info"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(event_url, headers=headers, timeout=10)
        text = resp.text

        contact_person = ""
        contact_email = ""
        contact_phone = ""
        contact_title = ""

        # Look for organizer section
        organizer_match = re.search(r'"organizer":\s*\{[^}]*"name":"([^"]*)"', text)
        if organizer_match:
            contact_person = organizer_match.group(1)

        # Look for email (prefer Eventbrite contact email)
        email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_matches:
            # Filter out common non-contact emails
            valid_emails = [e for e in email_matches if not any(x in e for x in ['google', 'cdn', 'analytics'])]
            if valid_emails:
                contact_email = valid_emails[0]

        # Look for phone (North American format)
        phone_matches = re.findall(r'\+?1?\s*\(?([0-9]{3})\)?[\s.-]?([0-9]{3})[\s.-]?([0-9]{4})', text)
        if phone_matches:
            area, exchange, line = phone_matches[0]
            contact_phone = f"({area}) {exchange}-{line}"

        return contact_person, contact_email, contact_phone, contact_title

    except Exception as e:
        logger.debug(f"Error extracting contact: {e}")
        return "", "", "", ""

def scrape_eventbrite(venue_name: str, city: str, start_date: str, end_date: str) -> list:
    """
    Scrape Eventbrite for REAL events in a city
    LIVE: Saves results immediately as they're found
    """
    results = load_results()

    try:
        city_slug = city.lower().replace(" ", "-")
        url = f"https://www.eventbrite.com/d/{city_slug}--{city_slug}/events/?start_date={start_date}&end_date={end_date}"

        logger.info(f"Scraping Eventbrite: {city} | {venue_name}")
        logger.info(f"URL: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.eventbrite.com/",
        }

        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=30)
        logger.info(f"Status: {resp.status_code}")

        if resp.status_code != 200:
            logger.warning(f"HTTP Error {resp.status_code}")
            return results

        soup = BeautifulSoup(resp.text, "html.parser")

        # Find event links - multiple selectors to be robust
        event_links = []

        # Selector 1: Look for event URLs
        for link in soup.find_all("a", href=re.compile(r"/e/[0-9]")):
            href = link.get("href", "")
            if href and "/e/" in href:
                event_links.append(href)

        # Selector 2: Look for data attributes
        for div in soup.find_all("div", {"data-event-id": True}):
            link = div.find("a", href=True)
            if link:
                href = link.get("href", "")
                if href and "/e/" in href:
                    event_links.append(href)

        event_links = list(set(event_links))[:20]  # Limit to 20 per search
        logger.info(f"Found {len(event_links)} event links")

        if not event_links:
            logger.warning("No event links found - trying alternative parsing...")

            # Try to extract from JSON in page
            json_match = re.search(r'<script[^>]*>.*?"events":\s*(\[.*?\])', resp.text, re.DOTALL)
            if json_match:
                try:
                    events_data = json.loads(json_match.group(1)[:2000])
                    logger.info(f"Found {len(events_data)} events in JSON")
                except:
                    pass

        # Process each event link
        for i, event_link in enumerate(event_links[:15]):  # Limit processing
            try:
                # Make absolute URL
                if not event_link.startswith("http"):
                    event_link = f"https://www.eventbrite.com{event_link}"

                logger.info(f"Processing event {i+1}/{len(event_links)}: {event_link[:80]}")

                # Get event page
                event_resp = session.get(event_link, headers=headers, timeout=15)
                event_soup = BeautifulSoup(event_resp.text, "html.parser")

                # Extract event details
                event_name = ""
                event_date = ""

                # Get event name
                title = event_soup.find("h1") or event_soup.find("h2")
                if title:
                    event_name = title.get_text(strip=True)

                # Get event date
                date_elem = event_soup.find("span", {"data-testid": "event-date-time-inner"})
                if date_elem:
                    event_date = date_elem.get_text(strip=True)
                else:
                    # Try alternative
                    date_match = re.search(r'\b\d{1,2}\/\d{1,2}\/\d{4}\b', event_resp.text)
                    if date_match:
                        event_date = date_match.group(0)

                if len(event_name) < 3:
                    continue

                # Extract contact info from event page
                contact_person, contact_email, contact_phone, contact_title = extract_contact_from_event_page(event_link)

                event = {
                    "event_name": event_name,
                    "event_dates": event_date,
                    "venue_name": venue_name,
                    "city": city,
                    "contact_person": contact_person,
                    "contact_title": contact_title,
                    "email": contact_email,
                    "phone": contact_phone,
                    "event_url": event_link,
                    "scraped_at": datetime.now().isoformat()
                }

                # Check if already exists
                existing_names = set([e["event_name"].lower() for e in results])
                if event["event_name"].lower() not in existing_names:
                    results.append(event)
                    save_results(results)  # SAVE IMMEDIATELY for live updates
                    logger.info(f"  SAVED: {event_name[:60]}")
                    time.sleep(0.5)

            except Exception as e:
                logger.warning(f"Error processing event: {e}")
                continue

        logger.info(f"Total: {len(results)} events")

    except Exception as e:
        logger.error(f"Scrape error: {e}")
        import traceback
        traceback.print_exc()

    return results

def scrape_venue_simple(venue_name: str, city: str, start_date: str, end_date: str) -> list:
    """
    Scrape one venue
    """
    logger.info(f"Scraping {venue_name} ({start_date} to {end_date})")
    return scrape_eventbrite(venue_name, city, start_date, end_date)

if __name__ == "__main__":
    # Test
    results = scrape_eventbrite("DC Convention Center", "Washington", "2026-06-01", "2026-12-31")
    print(f"Found {len(results)} events")
    for r in results[:3]:
        print(f"  {r['event_name']} - {r['contact_person']}")
