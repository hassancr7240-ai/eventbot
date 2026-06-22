"""
Write event records to Google Sheets automatically.
Creates a new tab for each bot run with a timestamp.
"""

import json
import os
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SHEET_ID = "1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "data", "google_token.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "data", "google_credentials.json")

def get_service():
    """Authenticate with Google Sheets API using OAuth2."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            creds_data = json.load(f)
            # Try to create credentials from saved token
            try:
                creds = service_account.Credentials.from_service_account_info(creds_data, scopes=SCOPES)
            except:
                creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # First time: use OAuth2 flow
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            json.dump(json.loads(creds.to_json()), f)

    return build("sheets", "v4", credentials=creds)

def create_run_tab(service):
    """Create a new tab for this run with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tab_name = f"Run_{timestamp}"

    request_body = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": tab_name,
                        "gridProperties": {"rowCount": 1000, "columnCount": 15}
                    }
                }
            }
        ]
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body=request_body
    ).execute()

    return tab_name

def write_to_sheet(records):
    """Write all event records to a new Google Sheet tab."""
    try:
        service = get_service()
        tab_name = create_run_tab(service)

        # Prepare data
        headers = [
            "Venue Name", "City", "State", "Event Name", "Event Dates",
            "Contact Person", "Contact Title", "Email", "Phone", "Event URL",
            "Email Sent", "Call Notes 1", "Call Notes 2", "Call Notes 3", "Call Notes 4",
            "Status", "Scraped At", "Last Updated"
        ]

        rows = [headers]
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

        # Write to sheet
        body = {"values": rows}
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        print(f"✅ Uploaded {len(rows)-1} events to Google Sheet (tab: {tab_name})")
        return True

    except FileNotFoundError:
        print("⚠️  Google credentials not found. Skipping sheet upload.")
        return False
    except Exception as e:
        print(f"❌ Google Sheets error: {e}")
        return False

if __name__ == "__main__":
    # Test: load local events and upload
    db_file = os.path.join(os.path.dirname(__file__), "data", "events_db.json")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        write_to_sheet(records)
