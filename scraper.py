"""
EventBot Scraper - WORKING VERSION
Uses Eventbrite directly with browser automation for JavaScript-rendered content
Fast, reliable, real results
"""

import json
import os
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

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
    Scrape Eventbrite for events using Selenium (JS-rendered content)
    LIVE: Saves results to file as they're found so UI updates in real-time
    """
    results = load_results()
    driver = None

    try:
        city_slug = city.lower().replace(" ", "-")
        url = f"https://www.eventbrite.com/d/{city_slug}--{city_slug}/events/?start_date={start_date}&end_date={end_date}"

        logger.info(f"Starting browser for: {url}")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(20)

        logger.info(f"Loading page...")
        driver.get(url)

        # Wait for events to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='event-card']"))
            )
        except:
            logger.warning("Timeout waiting for event cards")

        # Scroll to load more events
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find event cards
        cards = soup.find_all("div", {"data-testid": "event-card"})
        logger.info(f"Found {len(cards)} event cards")

        for card in cards:
            try:
                # Event name
                title_elem = card.find("h3")
                if not title_elem:
                    continue

                event_name = title_elem.get_text(strip=True)

                # Date
                date_elem = card.find("span", {"data-testid": "event-date-time-inner"})
                event_date = date_elem.get_text(strip=True) if date_elem else ""

                # Skip if too short
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
                    save_results(results)  # SAVE IMMEDIATELY
                    logger.info(f"  Found: {event_name[:60]}")
                    time.sleep(0.1)

            except Exception as e:
                logger.debug(f"Parse error: {e}")
                continue

        logger.info(f"Total: {len(results)} events")

    except Exception as e:
        logger.error(f"Scrape error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()

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
