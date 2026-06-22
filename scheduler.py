"""
Scheduler — runs the bot automatically on a daily or weekly schedule.
Run this as a background process: python scheduler.py
Configurable via command-line args or config.json.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from venues import VENUES, INDUSTRY_SOURCES
from scraper import scrape_venue, crawl_all_industry_sources
from deduplicator import upsert_records, record_run_timestamp
from excel_writer import build_excel
from google_sheets_writer import write_to_sheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "logs", "scheduler.log"),
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "data", "scheduler_config.json")

DEFAULT_CONFIG = {
    "enabled": True,
    "frequency": "daily",       # "daily" or "weekly"
    "run_hour": 6,              # 6 AM
    "run_day_of_week": 1,       # Monday (0=Sun, 1=Mon, ..., 6=Sat) — only used when weekly
    "start_year_offset": 0,     # 0 = current year (2026)
    "end_year_offset": 0,       # ONLY 2026 — no 2027, 2028, 2029
    "use_industry_sources": True,
    "auto_export_excel": True,
    "venues": "all",            # "all" or list of venue names
}


def load_config() -> dict:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        # Fill in any missing keys with defaults
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    # Write defaults
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def run_once(cfg: dict | None = None) -> None:
    """Execute a full scrape run for all configured venues."""
    if cfg is None:
        cfg = load_config()

    now = datetime.now()
    start_year = now.year + cfg["start_year_offset"]
    end_year = now.year + cfg["end_year_offset"]

    if cfg["venues"] == "all":
        venues = VENUES
    else:
        venue_names = cfg["venues"]
        venues = [v for v in VENUES if v["name"] in venue_names]

    logger.info(
        "=== EventBot Run Started === venues=%d years=%d-%d",
        len(venues), start_year, end_year,
    )

    total_new = 0
    total_updated = 0

    for venue in venues:
        try:
            logger.info("Scraping: %s", venue["name"])
            records = scrape_venue(venue, start_year, end_year)

            if cfg.get("use_industry_sources"):
                extra = crawl_all_industry_sources(venue)
                records.extend(extra)

            if records:
                added, updated = upsert_records(records)
                total_new += added
                total_updated += updated
                logger.info(
                    "  %s: +%d new, ~%d updated",
                    venue["name"], added, updated,
                )
            else:
                logger.info("  %s: no records found", venue["name"])

        except Exception as exc:
            logger.error("Error scraping %s: %s", venue["name"], exc, exc_info=True)

    record_run_timestamp()

    if cfg.get("auto_export_excel"):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            out_dir = os.path.join(os.path.dirname(__file__), "output")
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, f"EventBot_Tracker_{ts}.xlsx")
            build_excel(path)
            logger.info("Excel exported: %s", path)
        except Exception as exc:
            logger.warning("Excel export failed: %s", exc)

    # Upload to Google Sheets
    try:
        from deduplicator import load_db
        records = load_db()
        write_to_sheet(records)
    except Exception as exc:
        logger.warning("Google Sheets upload failed: %s", exc)

    logger.info(
        "=== Run Complete === +%d new | ~%d updated",
        total_new, total_updated,
    )


def _next_run_time(cfg: dict) -> datetime:
    """Calculate the next scheduled run datetime."""
    now = datetime.now()
    hour = cfg["run_hour"]
    freq = cfg["frequency"]

    if freq == "daily":
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    if freq == "weekly":
        target_dow = cfg["run_day_of_week"]
        days_ahead = (target_dow - now.isoweekday() % 7) % 7
        if days_ahead == 0:
            # Same day — check if we're past the hour
            candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if candidate <= now:
                days_ahead = 7
            else:
                return candidate
        candidate = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
        return candidate

    # Fallback: 24h from now
    return now + timedelta(hours=24)


def run_scheduler() -> None:
    """Main scheduler loop. Sleeps until next run time then executes."""
    logger.info("EventBot Scheduler started.")
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)

    while True:
        cfg = load_config()
        if not cfg.get("enabled", True):
            logger.info("Scheduler disabled — sleeping 60s then checking again.")
            time.sleep(60)
            continue

        next_run = _next_run_time(cfg)
        wait_secs = max(0, (next_run - datetime.now()).total_seconds())
        logger.info(
            "Next run: %s (in %.0f minutes)",
            next_run.strftime("%Y-%m-%d %H:%M"),
            wait_secs / 60,
        )

        time.sleep(wait_secs)

        # Re-read config in case it changed while sleeping
        cfg = load_config()
        if cfg.get("enabled", True):
            try:
                run_once(cfg)
            except Exception as exc:
                logger.error("Scheduler run failed: %s", exc, exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EventBot Scheduler")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run a single scrape immediately and exit",
    )
    parser.add_argument(
        "--years",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Override year range, e.g. --years 2026 2029",
    )
    args = parser.parse_args()

    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)

    if args.run_now:
        cfg = load_config()
        if args.years:
            now = datetime.now()
            cfg["start_year_offset"] = args.years[0] - now.year
            cfg["end_year_offset"] = args.years[1] - now.year
        run_once(cfg)
    else:
        run_scheduler()
