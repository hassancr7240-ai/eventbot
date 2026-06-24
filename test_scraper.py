#!/usr/bin/env python3
"""Test scraper to debug Eventbrite parsing"""

import requests
from bs4 import BeautifulSoup
import json

city = "washington"
start_date = "2026-06-01"
end_date = "2026-12-31"

url = f"https://www.eventbrite.com/d/{city}--{city}/events/?start_date={start_date}&end_date={end_date}"

print(f"Testing URL: {url}\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    resp = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Content length: {len(resp.text)} bytes\n")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Check for event cards with various selectors
    print("Looking for event cards...")

    # Selector 1
    cards = soup.find_all("div", {"data-testid": "event-card"})
    print(f"  [1] div[data-testid='event-card']: {len(cards)} found")

    # Selector 2
    cards = soup.find_all("article", class_="event-card")
    print(f"  [2] article.event-card: {len(cards)} found")

    # Selector 3
    cards = soup.find_all("div", class_=lambda x: x and "event" in x.lower())
    print(f"  [3] div[class*='event']: {len(cards)} found")

    # Print first 2000 chars of HTML to debug
    print("\n--- First 2000 chars of response ---")
    print(resp.text[:2000])

    # Look for JSON in page
    if "window.__SERVER_DATA__" in resp.text:
        print("\n✓ Found window.__SERVER_DATA__ (likely has event data)")
    else:
        print("\n✗ No window.__SERVER_DATA__ found")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
