"""
Upload event data to Google Sheets automatically.
Uses OAuth token saved by setup_google_oauth.py
"""

import os
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SHEET_ID = "1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "data", "google_token.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "data", "oauth_credentials.json")

def get_sheets_service():
    """Get authenticated Google Sheets service using saved OAuth token."""
    creds = None

    # Load saved token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If token expired or doesn't exist, refresh or re-authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print("❌ OAuth credentials not set up. Run: python setup_google_oauth.py")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=8080)

        # Save refreshed token
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)

def upload_to_google_sheets(records):
    """Upload all event records to a new Google Sheets tab."""
    service = get_sheets_service()
    if not service:
        print("⚠️  Could not connect to Google Sheets. Skipping upload.")
        return False

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tab_name = f"Run {timestamp}"

        # Create new sheet tab
        requests = [
            {
                "addSheet": {
                    "properties": {
                        "title": tab_name,
                        "gridProperties": {"rowCount": 5000, "columnCount": 18}
                    }
                }
            }
        ]

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": requests}
        ).execute()

        # Prepare headers and data
        headers = [
            "Venue Name", "City", "State", "Event Name", "Event Dates",
            "Contact Person", "Contact Title", "Email", "Phone", "Event URL",
            "Email Sent", "Call Notes 1", "Call Notes 2", "Call Notes 3", "Call Notes 4",
            "Status", "Scraped At", "Last Updated"
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

        # Write data to sheet
        body = {"values": rows}
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        print(f"✅ Uploaded {total_events} events to Google Sheet")
        print(f"   Tab: {tab_name}")
        print(f"   Link: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        return True

    except Exception as e:
        print(f"❌ Google Sheets upload failed: {e}")
        return False

if __name__ == "__main__":
    # Test
    db_file = os.path.join(os.path.dirname(__file__), "data", "events_db.json")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        upload_to_google_sheets(records)
