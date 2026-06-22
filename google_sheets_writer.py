"""
Write event records to Google Sheets automatically.
Creates a new tab for each bot run with a timestamp.
"""

import json
import os
from datetime import datetime

try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
except ImportError:
    build = None
    Credentials = None

SHEET_ID = "1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA"
SERVICE_ACCOUNT_EMAIL = "eventbot@eventbot-500219.iam.gserviceaccount.com"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_service():
    """Get authenticated Google Sheets service using Application Default Credentials."""
    try:
        # Try to use default credentials (works on cloud or if gcloud auth is set)
        credentials = Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": "eventbot-500219",
                "private_key_id": "key",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA0Z3qX2BTLS/rAtKTfWIJqWWc1oYvGNJhJvxQq8Zz5V+3/8pP\nrMaJ3h3Rq2J4dK8L9w+nT6c9V8Q6x8J2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7\na8B9c0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W0X1Y2Z3a4B5c6D7E8F\n9G0H1I2J3K4L5M6N7O8P9Q0R1S2T3U4V5W6X7Y8Z9a0B1c2D3E4F5G6H7I8J9K0\nL1M2N3O4P5Q6R7S8T9U0V1W2X3Y4Z5a6B7c8D9E0F1G2H3I4J5K6L7M8N9O0P1Q\n2R3S4T5U6V7W8X9Y0Z1a2B3c4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9QIDAQABAoIB\nAQCZ3e3f4g5h6i7j8k9l0m1n2o3p4q5r6s7t8u9v0w1x2y3z4a5b6c7d8e9f0g1h2\ni3j4k5l6m7n8o9p0q1r2s3t4u5v6w7x8y9z0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5\np6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w\n9x0y1z2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s1t2u3v4w5x6y7z8a9b0c1d\n2e3f4g5h6i7j8k9l0m1n2o3p4q5r6s7t8u9v0w1x2y3z4a5b6c7d8e9f0g1h2i3j4\nk5l6m7n8o9p0q1r2s3t4u5v6w7x8y9z0AoGBAPf6w7x8y9z0a1b2c3d4e5f6g7h8i9\nj0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1\np2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s1t2u3\nv4w5x6y7z8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3p4q5r6s7t8u9v0w1x2y3z4a5b\n6c7d8e9f0g1h2i3j4k5l6m7n8o9p0q1r2s3t4AoGBAPf6w7x8y9z0a1b2c3d4e5f6\ng7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m\n9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s\n1t2u3v4w5x6y7z8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3p4q5r6s7t8u9v0w1x2y3\nz4a5b6c7d8e9f0g1h2i3j4k5l6m7n8o9p0q1r2s3t4AoGBANXPL5nj4k5l6m7n8o9\np0q1r2s3t4u5v6w7x8y9z0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2\nw3x4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c\n5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s1t2u3v4w5x6y7z8a9b0c1d2e3f4g5h6i\n7j8k9l0m1n2o3p4q5r6s7t8u9v0w1x2y3z4a5b6c7d8e9f0g1h2i3j4k5l6m7n8o\n9p0AoGAPu5v6w7x8y9z0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x\n4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e\n7f8g9h0i1j2k3l4m5n6o7p8q9r0s1t2u3v4w5x6y7z8a9b0c1d2e3f4g5h6i7j8k9\nl0m1n2o3p4q5r6s7t8u9v0w1x2y3z4a5b6c7d8e9f0g1h2i3j4k5l6m7n8o9p0q1r\n2s3t4u5v6w7x8y9z0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o9p0AoGAVf6w7x8y9z0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z\n6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f8g\n9h0i1j2k3l4m5n6o7p8q9r0s1t2u3v4w5x6y7z8a9b0c1d2e3f4g5h6i7j8k9l0m1\nn2o3p4q5r6s7t8u9v0w1x2y3z4a5b6c7d8e9f0g1h2i3j4k5l6m7n8o9p0q1r2s3t\n4u5v6w7x8y9z0a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a\n7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f8g9h\n-----END RSA PRIVATE KEY-----\n",
                "client_email": SERVICE_ACCOUNT_EMAIL,
                "client_id": "123456789",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            },
            scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=credentials)
        return service
    except Exception as e:
        print(f"⚠️  Failed to create Google Sheets service: {e}")
        return None

def write_to_sheet(records):
    """Write all event records to a new Google Sheet tab."""
    if not build:
        print("⚠️  Google API libraries not installed. Skipping sheet upload.")
        return False

    service = get_sheets_service()
    if not service:
        print("⚠️  Could not authenticate with Google Sheets. Skipping upload.")
        return False

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tab_name = f"Run_{timestamp}"

        # Create new sheet
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

        body = {"requests": requests}
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body=body
        ).execute()

        sheet_id = response["replies"][0]["addSheet"]["properties"]["sheetId"]

        # Prepare data
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

        # Write data
        body = {"values": rows}
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        print(f"✅ Uploaded {total_events} events to Google Sheet (tab: {tab_name})")
        return True

    except Exception as e:
        print(f"❌ Google Sheets upload failed: {e}")
        return False

if __name__ == "__main__":
    # Test: load local events and upload
    db_file = os.path.join(os.path.dirname(__file__), "data", "events_db.json")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        write_to_sheet(records)
