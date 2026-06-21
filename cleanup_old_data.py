"""
Delete all events before 2026 from the database.
Run this once: python cleanup_old_data.py
"""

import json
import os
import re

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "events_db.json")

def extract_year(date_str: str) -> int | None:
    """Extract year from date string. Returns None if no year found."""
    if not date_str:
        return None
    match = re.search(r"20(\d{2})", str(date_str))
    if match:
        return int("20" + match.group(1))
    return None

def cleanup():
    if not os.path.exists(DATA_FILE):
        print("No database file found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)

    total_before = sum(len(records) for records in db.values())
    total_deleted = 0

    for venue_name in db:
        original_count = len(db[venue_name])
        db[venue_name] = [
            rec for rec in db[venue_name]
            if extract_year(rec.get("event_dates", "")) is None
            or extract_year(rec.get("event_dates", "")) >= 2026
        ]
        deleted = original_count - len(db[venue_name])
        if deleted > 0:
            print(f"  {venue_name}: deleted {deleted} old records")
            total_deleted += deleted

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    total_after = sum(len(records) for records in db.values())
    print(f"\n✅ Cleanup complete!")
    print(f"  Before: {total_before} records")
    print(f"  Deleted: {total_deleted} records (pre-2026)")
    print(f"  After: {total_after} records (2026+)")

if __name__ == "__main__":
    cleanup()
