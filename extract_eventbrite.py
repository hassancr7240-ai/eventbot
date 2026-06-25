#!/usr/bin/env python3
"""Extract actual event data from Eventbrite HTML"""

import requests
import json
import re

city = "washington"
start_date = "2026-06-01"
end_date = "2026-12-31"

url = f"https://www.eventbrite.com/d/{city}--{city}/events/?start_date={start_date}&end_date={end_date}"

print(f"Fetching: {url}\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

resp = requests.get(url, headers=headers, timeout=20)
print(f"Status: {resp.status_code}, Size: {len(resp.text)} bytes\n")

html = resp.text

# Look for JavaScript data in script tags
script_pattern = r'<script[^>]*>\s*window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*</script>'
matches = re.findall(script_pattern, html, re.DOTALL)

if matches:
    print(f"Found {len(matches)} script blocks")
    try:
        data = json.loads(matches[0][:5000])  # First 5000 chars to inspect
        print(json.dumps(data, indent=2)[:2000])
    except:
        print("Could not parse JSON from script")
else:
    print("No __INITIAL_STATE__ found")

# Alternative: Look for Next.js data
next_pattern = r'<script id="__NEXT_DATA__"[^>]*>\s*(\{.*?\})\s*</script>'
matches = re.findall(next_pattern, html, re.DOTALL)

if matches:
    print(f"\nFound {len(matches)} Next.js data blocks")
    try:
        data = json.loads(matches[0][:2000])
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"Error: {e}")
else:
    print("\nNo __NEXT_DATA__ found")

# Look for event cards in HTML directly
print("\n--- Searching for event HTML patterns ---")

# Look for links with event IDs
event_links = re.findall(r'/events/(\d+)[^>]*>([^<]*)<', html)
print(f"Found {len(event_links)} event links")
for eid, name in event_links[:5]:
    print(f"  {eid}: {name[:60]}")

# Look for data attributes
data_attrs = re.findall(r'data-event-id="(\d+)"[^>]*title="([^"]*)"', html)
print(f"\nFound {len(data_attrs)} data-event-id attributes")
for eid, name in data_attrs[:5]:
    print(f"  {eid}: {name[:60]}")
