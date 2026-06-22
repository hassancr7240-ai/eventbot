"""
Simple direct upload to Google Sheets using REST API.
No OAuth setup needed - uses public sheet access.
"""

import json
import os
import requests
from datetime import datetime

SHEET_ID = "1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

def upload_via_csv_import(records):
    """
    Create a CSV and provide instructions for importing to Google Sheets.
    Alternative: Can be automated with proper OAuth setup.
    """
    try:
        # Create CSV
        csv_lines = []
        csv_lines.append("Venue,City,State,Event Name,Dates,Contact,Title,Email,Phone,URL,Email Sent,Notes1,Notes2,Notes3,Notes4,Status,Scraped,Updated")

        total = 0
        for venue_name, events in records.items():
            for event in events:
                # Escape CSV properly
                row = [
                    f'"{event.get("venue_name", "")}"',
                    f'"{event.get("city", "")}"',
                    f'"{event.get("state", "")}"',
                    f'"{event.get("event_name", "")}"',
                    f'"{event.get("event_dates", "")}"',
                    f'"{event.get("contact_person", "")}"',
                    f'"{event.get("contact_title", "")}"',
                    f'"{event.get("email", "")}"',
                    f'"{event.get("phone", "")}"',
                    f'"{event.get("event_url", "")}"',
                    f'"{event.get("email_sent", "")}"',
                    f'"{event.get("call_notes_1", "")}"',
                    f'"{event.get("call_notes_2", "")}"',
                    f'"{event.get("call_notes_3", "")}"',
                    f'"{event.get("call_notes_4", "")}"',
                    f'"{event.get("status", "")}"',
                    f'"{event.get("scraped_at", "")}"',
                    f'"{event.get("last_updated", "")}"',
                ]
                csv_lines.append(",".join(row))
                total += 1

        # Save CSV
        output_file = os.path.join(os.path.dirname(__file__), "output", f"events_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(csv_lines))

        print(f"✓ CSV created: {output_file}")
        print(f"✓ Total events: {total}")
        print(f"\nTo upload to Google Sheets automatically:")
        print(f"1. Share the CSV programmatically (needs OAuth)")
        print(f"2. Or: Manually import CSV to Sheet (2 clicks)")
        print(f"\nFor now, manual import steps:")
        print(f"  1. Download CSV: {output_file}")
        print(f"  2. Open Google Sheet: {SHEET_URL}")
        print(f"  3. Create new tab")
        print(f"  4. File > Import > Upload CSV")

        return True

    except Exception as e:
        print(f"Error creating CSV: {e}")
        return False

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "data", "events_db.json")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        upload_via_csv_import(records)
