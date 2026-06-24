"""
Quick upload to Google Sheets using gspread (simpler than OAuth).
Needs: pip install gspread
"""

import json
import os
from datetime import datetime

try:
    import gspread
except ImportError:
    print("Install gspread: pip install gspread")
    exit(1)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA/edit"
SHEET_ID = "1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA"

def upload_with_gspread(records):
    """
    Upload using gspread (requires user to authorize once).
    """
    try:
        # This will open a browser for authorization on first run
        gc = gspread.oauth()
        sheet = gc.open_by_key(SHEET_ID)

        # Create new worksheet
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        tab_name = f"Run {timestamp}"

        try:
            new_ws = sheet.add_worksheet(title=tab_name, rows=5000, cols=18)
        except:
            # Tab might already exist, just use it
            new_ws = sheet.worksheet(tab_name)

        # Prepare data
        headers = [
            "Venue", "City", "State", "Event Name", "Dates",
            "Contact", "Title", "Email", "Phone", "URL",
            "Email Sent", "Notes 1", "Notes 2", "Notes 3", "Notes 4",
            "Status", "Scraped", "Updated"
        ]

        rows = [headers]
        total = 0

        for venue_name, events in records.items():
            for event in events:
                rows.append([
                    event.get("venue_name", ""),
                    event.get("city", ""),
                    event.get("state", ""),
                    event.get("event_name", ""),
                    event.get("event_dates", ""),
                    event.get("contact_person", ""),
                    event.get("contact_title", ""),
                    event.get("email", ""),
                    event.get("phone", ""),
                    event.get("event_url", ""),
                    event.get("email_sent", ""),
                    event.get("call_notes_1", ""),
                    event.get("call_notes_2", ""),
                    event.get("call_notes_3", ""),
                    event.get("call_notes_4", ""),
                    event.get("status", ""),
                    event.get("scraped_at", ""),
                    event.get("last_updated", ""),
                ])
                total += 1

        # Upload
        new_ws.update(rows)
        print(f"SUCCESS: Uploaded {total} events to Google Sheet")
        print(f"Tab: {tab_name}")
        print(f"Sheet: {SHEET_URL}")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "data", "events_db.json")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        upload_with_gspread(records)
