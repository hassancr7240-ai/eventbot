"""
Automatic Google Sheets upload using gspread.
First run will prompt for authorization (one-time only).
After that, it uploads automatically.
"""

import json
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client import client, tools
import webbrowser

SHEET_ID = "1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA"
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = os.path.join(os.path.dirname(__file__), "data", "gspread_creds.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "data", "gspread_token.json")

def get_authorized_client():
    """Get gspread client, authorize on first run."""
    creds = None

    # Try to load saved token
    if os.path.exists(TOKEN_FILE):
        try:
            creds = client.OAuth2Credentials.from_json_keyfile_name(TOKEN_FILE, SCOPES)
            if creds.access_token_expired:
                creds.refresh(client.HttpLib2Http())
            return gspread.authorize(creds)
        except:
            pass

    # First time - use browser authorization
    print("Authorizing with Google Sheets...")
    print("A browser window will open. Sign in with: e3personnel.com@gmail.com")
    print("(If nothing opens, copy this link: https://accounts.google.com)")

    try:
        # Use gspread's built-in OAuth
        gc = gspread.oauth(scopes=SCOPES)
        return gc
    except Exception as e:
        print(f"Authorization failed: {e}")
        print("Try running with: gspread.oauth()")
        return None

def upload_to_sheets(records):
    """Upload event records to Google Sheets."""
    try:
        gc = get_authorized_client()
        if not gc:
            print("ERROR: Could not authenticate with Google Sheets")
            return False

        # Open spreadsheet
        sheet = gc.open_by_key(SHEET_ID)

        # Create new worksheet with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        tab_name = f"Run {timestamp}"

        try:
            worksheet = sheet.add_worksheet(title=tab_name, rows=5000, cols=18)
        except:
            # Tab might exist, overwrite it
            worksheet = sheet.worksheet(0)

        # Prepare data
        headers = [
            "Venue", "City", "State", "Event Name", "Dates",
            "Contact", "Title", "Email", "Phone", "URL",
            "Email Sent", "Notes 1", "Notes 2", "Notes 3", "Notes 4",
            "Status", "Scraped", "Updated"
        ]

        rows = [headers]
        total_events = 0

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
                total_events += 1

        # Upload in batches (Google Sheets has limits)
        print(f"Uploading {total_events} events to Google Sheets...")
        worksheet.update(rows, value_input_option='RAW')

        print(f"SUCCESS: {total_events} events uploaded to tab '{tab_name}'")
        print(f"Link: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        return True

    except Exception as e:
        print(f"Upload failed: {e}")
        return False

if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "data", "events_db.json")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        upload_to_sheets(records)
    else:
        print("No events database found")
