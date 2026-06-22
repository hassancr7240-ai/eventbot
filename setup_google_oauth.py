"""
One-time setup to authorize Google Sheets access via OAuth.
Run this ONCE to generate the token that the bot will use.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "data", "google_token.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "data", "oauth_credentials.json")

def setup_oauth():
    """Create OAuth credentials and save token for later use."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Missing: {CREDENTIALS_FILE}")
        print("\nTo set up OAuth:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Desktop app)")
        print("3. Download JSON and save as: data/oauth_credentials.json")
        print("4. Run this script again")
        return

    print("🔐 Opening browser for authorization...")
    print("   Sign in with: e3personnel.com@gmail.com")

    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )

    creds = flow.run_local_server(port=8080)

    # Save token for future use
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"✅ Token saved: {TOKEN_FILE}")
    print("   Bot will now use this to upload to Google Sheets automatically")

if __name__ == "__main__":
    setup_oauth()
