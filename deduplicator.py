"""
Deduplication and data merge engine.

Rules:
- Same event = same normalized event name (fuzzy-ish) at same venue
- Same contact = same email address
- If event exists: update dates/URL if new info is richer
- If contact exists: merge phone/name if previously blank
- Preserves all user-entered call notes and email_sent flags
"""

import re
import json
import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "events_db.json")


# ── NORMALIZERS ───────────────────────────────────────────────────────────────

def _norm_event(name: str) -> str:
    """Normalize event name for comparison."""
    name = re.sub(r"[^a-z0-9]", "", name.lower().strip())
    # Remove common duplicates like "sports representative meeting" appearing 5x
    # If same name appears at 3+ venues, it's likely a traveling conference
    return name


def _norm_email(email: str) -> str:
    return email.lower().strip()


def _richer(a: str, b: str) -> str:
    """Return whichever string is longer/more complete."""
    return a if len(a) >= len(b) else b


# ── DB LOAD / SAVE ────────────────────────────────────────────────────────────

def load_db() -> dict:
    """Load existing events database from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Could not load DB: %s — starting fresh", exc)
    return {}  # {venue_name: [record, ...]}


def save_db(db: dict) -> None:
    """Persist database to JSON."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


# ── MERGE LOGIC ───────────────────────────────────────────────────────────────

def merge_records(existing: list[dict], new_records: list[dict]) -> tuple[list[dict], int, int]:
    """
    Merge new_records into existing list.
    Returns (merged_list, added_count, updated_count).
    """
    added = 0
    updated = 0

    # Build indexes
    by_email: dict[str, dict] = {}
    by_event: dict[str, list[dict]] = {}

    for rec in existing:
        if rec.get("email"):
            by_email[_norm_email(rec["email"])] = rec
        ek = _norm_event(rec.get("event_name", "")) + "|" + rec.get("venue_name", "")
        by_event.setdefault(ek, []).append(rec)

    for new in new_records:
        email_key = _norm_email(new.get("email", ""))
        event_key = (
            _norm_event(new.get("event_name", "")) + "|" + new.get("venue_name", "")
        )

        # Case 1: exact email match → update but preserve user data
        if email_key and email_key in by_email:
            rec = by_email[email_key]
            rec["event_dates"] = _richer(rec.get("event_dates", ""), new.get("event_dates", ""))
            rec["contact_person"] = _richer(rec.get("contact_person", ""), new.get("contact_person", ""))
            rec["contact_title"] = _richer(rec.get("contact_title", ""), new.get("contact_title", ""))
            rec["phone"] = _richer(rec.get("phone", ""), new.get("phone", ""))
            rec["event_url"] = _richer(rec.get("event_url", ""), new.get("event_url", ""))
            rec["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            updated += 1
            continue

        # Case 2: same event + venue, no email → might be same record without contact
        if event_key in by_event and not email_key:
            # Don't create a duplicate blank record
            continue

        # Case 3: brand new record
        new["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        existing.append(new)
        if email_key:
            by_email[email_key] = new
        by_event.setdefault(event_key, []).append(new)
        added += 1

    return existing, added, updated


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def upsert_records(new_records: list[dict]) -> tuple[int, int]:
    """
    Load DB, merge new_records, save, return (added, updated).
    Groups records by venue_name.
    """
    db = load_db()
    total_added = 0
    total_updated = 0

    # Group incoming records by venue
    by_venue: dict[str, list[dict]] = {}
    for r in new_records:
        by_venue.setdefault(r["venue_name"], []).append(r)

    for venue_name, records in by_venue.items():
        existing = db.get(venue_name, [])
        merged, added, updated = merge_records(existing, records)
        db[venue_name] = merged
        total_added += added
        total_updated += updated

    save_db(db)
    logger.info("DB updated: +%d added, ~%d updated", total_added, total_updated)
    return total_added, total_updated


def get_all_records() -> list[dict]:
    """Return all records flattened from DB."""
    db = load_db()
    out = []
    for records in db.values():
        out.extend(records)
    return out


def get_records_for_venue(venue_name: str) -> list[dict]:
    db = load_db()
    return db.get(venue_name, [])


def update_record_field(email: str, field: str, value: str) -> bool:
    """Update a single field on a record identified by email. Returns True on success."""
    db = load_db()
    for records in db.values():
        for rec in records:
            if _norm_email(rec.get("email", "")) == _norm_email(email):
                rec[field] = value
                rec["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_db(db)
                return True
    return False


def update_record(email: str, updates: dict) -> bool:
    """Update multiple fields on a record by email."""
    db = load_db()
    for records in db.values():
        for rec in records:
            if _norm_email(rec.get("email", "")) == _norm_email(email):
                for k, v in updates.items():
                    rec[k] = v
                rec["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_db(db)
                return True
    return False


def get_stats() -> dict:
    db = load_db()
    total_events = 0
    total_contacts = 0
    total_emailed = 0
    total_called = 0
    total_booked = 0
    venues_covered = set()

    for venue_name, records in db.items():
        venues_covered.add(venue_name)
        event_names = set()
        for r in records:
            event_names.add(_norm_event(r.get("event_name", "")))
            if r.get("email"):
                total_contacts += 1
            status = r.get("status", "").lower()
            if "email" in status:
                total_emailed += 1
            elif "call" in status or "voicemail" in status:
                total_called += 1
            elif "book" in status or "contract" in status:
                total_booked += 1
        total_events += len(event_names)

    return {
        "total_events": total_events,
        "total_contacts": total_contacts,
        "total_emailed": total_emailed,
        "total_called": total_called,
        "total_booked": total_booked,
        "venues_covered": len(venues_covered),
        "last_run": _get_last_run(),
    }


def _get_last_run() -> str:
    log_file = os.path.join(os.path.dirname(__file__), "logs", "last_run.txt")
    if os.path.exists(log_file):
        with open(log_file) as f:
            return f.read().strip()
    return "Never"


def record_run_timestamp() -> None:
    log_file = os.path.join(os.path.dirname(__file__), "logs", "last_run.txt")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M"))
