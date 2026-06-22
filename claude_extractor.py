"""
Use Claude AI to extract and validate event information from search results.
Improves accuracy and reduces manual processing.
"""

import json
import os
from anthropic import Anthropic

# Load API key from environment or config file
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
if not CLAUDE_API_KEY:
    config_file = os.path.join(os.path.dirname(__file__), "data", "config.json")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            CLAUDE_API_KEY = config.get("claude_api_key")

if CLAUDE_API_KEY:
    client = Anthropic(api_key=CLAUDE_API_KEY)
else:
    client = None

def extract_event_from_text(text: str, venue_name: str) -> dict | None:
    """
    Use Claude to extract structured event data from unstructured text.
    Returns a dict with event details or None if no valid event found.
    """
    if not client:
        return None

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract event information from this text. Return ONLY valid JSON (no markdown, no extra text).

Venue: {venue_name}
Text: {text}

Return JSON with these fields (use empty string "" for missing data):
{{
  "event_name": "event title",
  "event_dates": "dates or month/year",
  "contact_person": "person name or empty",
  "contact_title": "their title or empty",
  "email": "email address or empty",
  "phone": "phone number or empty",
  "event_url": "website or empty",
  "event_type": "Conference/Meeting/Expo/Tradeshow/Summit/Other"
}}

If the text doesn't describe a valid event, return: {{"event_name": ""}}
"""
                }
            ]
        )

        response_text = message.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        data = json.loads(response_text)

        # Only return if we got a valid event name
        if data.get("event_name", "").strip():
            return data
        return None

    except Exception as e:
        print(f"Claude extraction error: {e}")
        return None

def validate_contact_info(email: str, phone: str) -> dict:
    """
    Use Claude to validate and clean contact information.
    """
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": f"""Validate and clean this contact info. Return ONLY valid JSON (no markdown, no extra text).

Email: {email}
Phone: {phone}

Return JSON:
{{
  "email": "cleaned email or empty string",
  "phone": "cleaned phone or empty string",
  "is_valid": true/false
}}

Rules:
- Email must have @ and domain
- Phone must have at least 7 digits
- Return empty string if invalid
"""
                }
            ]
        )

        response_text = message.content[0].text.strip()

        # Remove markdown
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        return json.loads(response_text)

    except Exception as e:
        print(f"Claude validation error: {e}")
        return {"email": email, "phone": phone, "is_valid": False}

def deduplicate_events(events: list[dict]) -> list[dict]:
    """
    Use Claude to identify and remove duplicate events.
    """
    if len(events) <= 1:
        return events

    try:
        event_summaries = []
        for i, evt in enumerate(events):
            summary = f"{i}: {evt.get('event_name', '')} | {evt.get('event_dates', '')} | {evt.get('email', '')}"
            event_summaries.append(summary)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": f"""Identify duplicate or near-duplicate events. Return ONLY a JSON array (no markdown, no extra text).

Events:
{chr(10).join(event_summaries)}

Return JSON array of indices to KEEP (remove duplicates, keep the best one):
[0, 2, 5]

If no clear duplicates, return all indices.
"""
                }
            ]
        )

        response_text = message.content[0].text.strip()

        # Remove markdown
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        indices = json.loads(response_text)
        return [events[i] for i in indices if i < len(events)]

    except Exception as e:
        print(f"Claude deduplication error: {e}")
        return events

if __name__ == "__main__":
    # Test
    test_text = "TechConf 2026 - July 15-17, Washington DC. Contact: John Smith (john@techconf.org, 202-555-1234)"
    result = extract_event_from_text(test_text, "DC Convention Center")
    print(json.dumps(result, indent=2))
