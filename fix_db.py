"""
One-time DB cleanup:
1. Remove rows where event_name is actually a venue address/header
2. Parse contact_title from contact_person field where title is embedded
   e.g. "Lauren Forrer, Event Manager" -> name="Lauren Forrer", title="Event Manager"
3. Normalise email_sent to a clean string
Run: python fix_db.py
"""

import re
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from venues import TARGET_TITLES

DB = os.path.join(os.path.dirname(__file__), "data", "events_db.json")

BAD_EVENT_PATTERNS = [
    # Venue address rows that got picked up as events
    re.compile(r"\d{3,5}\s+\w+\s+(St|Ave|Blvd|Dr|Rd|Way|Place|Pl|Street|Avenue|Boulevard|Drive|Road)\b", re.I),
    re.compile(r"(MD|DC|PA|DE|VA)\s+\d{5}", re.I),
    re.compile(r"^https?://", re.I),
    re.compile(r"Meeting Space size", re.I),
    re.compile(r"Add events in chrono", re.I),
    re.compile(r"PUT RFP REQUESTS", re.I),
    re.compile(r"downloaded$", re.I),
    re.compile(r"^\d{1,2}/\d{1,2}/\d{4}"),   # date-only rows
]

def _is_bad_event(name: str) -> bool:
    if not name or len(name.strip()) < 5:
        return True
    for pat in BAD_EVENT_PATTERNS:
        if pat.search(name):
            return True
    # If name is just a city/state/address fragment
    if len(name) > 120:
        return True
    return False


def _parse_contact_person(raw: str) -> tuple[str, str]:
    """
    Split 'Joan Smith, Conference Planner' into ('Joan Smith', 'Conference Planner').
    Returns (name, title).
    """
    if not raw:
        return "", ""

    raw = raw.strip()

    # Try comma split: "Name, Title"
    if "," in raw:
        parts = raw.split(",", 1)
        name_part = parts[0].strip()
        title_part = parts[1].strip()
        # Verify title_part matches a known title keyword
        if any(kw.lower() in title_part.lower() for kw in TARGET_TITLES):
            return name_part, title_part
        # Maybe the title is in the name part (unusual)
        if any(kw.lower() in name_part.lower() for kw in TARGET_TITLES):
            return title_part, name_part

    # No comma — check if any title keyword is in the string
    for kw in TARGET_TITLES:
        if kw.lower() in raw.lower():
            # Remove the keyword to get the name
            name = re.sub(re.escape(kw), "", raw, flags=re.I).strip(" ,;-")
            return name, kw

    return raw, ""


def _clean_email_sent(val: str) -> str:
    if not val:
        return ""
    v = str(val).strip()
    # Convert datetime objects like "2021-07-08 00:00:00" -> "Yes"
    if re.match(r"\d{4}-\d{2}-\d{2}", v):
        return "Yes"
    if v.lower() in ("nan", "none", ""):
        return ""
    return v


def fix():
    if not os.path.exists(DB):
        print("DB not found — run seed_from_excel.py first.")
        return

    with open(DB, encoding="utf-8") as f:
        db = json.load(f)

    total_removed = 0
    total_title_fixed = 0
    total_email_fixed = 0

    for venue_name in list(db.keys()):
        records = db[venue_name]
        clean = []
        for rec in records:
            # 1. Remove bad event rows
            if _is_bad_event(rec.get("event_name", "")):
                total_removed += 1
                continue

            # 2. Parse title from contact_person if title is blank
            cp = rec.get("contact_person", "")
            ct = rec.get("contact_title", "")
            if cp and not ct:
                name, title = _parse_contact_person(cp)
                if title:
                    rec["contact_person"] = name
                    rec["contact_title"] = title
                    total_title_fixed += 1

            # 3. Clean email_sent
            es = rec.get("email_sent", "")
            cleaned = _clean_email_sent(str(es))
            if cleaned != str(es):
                rec["email_sent"] = cleaned
                total_email_fixed += 1

            clean.append(rec)

        db[venue_name] = clean

    # Remove empty venue buckets
    db = {k: v for k, v in db.items() if v}

    with open(DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    total_remaining = sum(len(v) for v in db.values())
    print(f"DB cleanup complete:")
    print(f"  Removed bad rows:      {total_removed}")
    print(f"  Titles parsed:         {total_title_fixed}")
    print(f"  email_sent cleaned:    {total_email_fixed}")
    print(f"  Records remaining:     {total_remaining}")
    print(f"  Venues remaining:      {len(db)}")


if __name__ == "__main__":
    fix()
