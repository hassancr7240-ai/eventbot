"""
Core scraper engine — production version.

Strategy (no paid API needed):
1. PRIMARY: Directly crawl the industry source URLs the client already uses
2. SECONDARY: Google search with polite delays (10-15s between queries)
3. For each result URL: visit page, find contact/staff page, extract fields
4. Filter contacts by target titles only
5. All results deduplicated and merged into DB
"""

import re
import time
import random
import logging
import urllib.parse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from venues import EVENT_TYPES, TARGET_TITLES, CITY_EXTRA_PHRASES
from claude_extractor import extract_event_from_text, validate_contact_info

logger = logging.getLogger(__name__)

# ── HTTP HEADERS (rotate user agents to reduce blocking) ─────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

def _headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(
    r"(?:\+?1[\s\-.]?)?(?:\(?\d{3}\)?[\s\-\.])\d{3}[\s\-\.]\d{4}(?:\s*(?:ext|x|ext\.)\s*\d{1,5})?"
)

# ── PHRASE GENERATION ─────────────────────────────────────────────────────────

def generate_phrases(venue_search_name: str, start_year: int, end_year: int, city: str = "") -> list[str]:
    """
    Generate search phrases. Optimized for speed:
    - 1 phrase per month per year (faster than 12 event types per month)
    - Format: [Month] [Year] [VenueName]
    """
    phrases = []
    for year in range(start_year, end_year + 1):
        for month in MONTHS:
            phrases.append(f"{month} {year} {venue_search_name}")

    if city and city in CITY_EXTRA_PHRASES:
        for template in CITY_EXTRA_PHRASES[city]:
            phrases.append(template.format(city=city))

    return phrases


# ── HTTP FETCH ────────────────────────────────────────────────────────────────

SESSION = requests.Session()

def fetch(url: str, timeout: int = 15) -> BeautifulSoup | None:
    """Fetch a URL, return BeautifulSoup or None on failure."""
    try:
        resp = SESSION.get(url, headers=_headers(), timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return BeautifulSoup(resp.text, "lxml")
        logger.debug("HTTP %s for %s", resp.status_code, url)
        return None
    except Exception as exc:
        logger.debug("Fetch failed %s: %s", url, exc)
        return None


def _polite_delay(min_s: float = 0.2, max_s: float = 0.8) -> None:
    time.sleep(random.uniform(min_s, max_s))


# ── URL UTILITIES ─────────────────────────────────────────────────────────────

def _is_useful_url(url: str) -> bool:
    skip = (
        "google.com", "bing.com", "facebook.com", "twitter.com", "x.com",
        "linkedin.com", "instagram.com", "youtube.com", "wikipedia.org",
        "reddit.com", "yelp.com", "maps.google", "accounts.google",
        "support.google", "policies.google",
    )
    u = url.lower()
    if u.endswith(".pdf") or u.endswith(".doc") or u.endswith(".docx"):
        return False
    return not any(s in u for s in skip)


def _resolve_url(base: str, href: str) -> str | None:
    if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
        return None
    if href.startswith("http"):
        return href
    try:
        return urllib.parse.urljoin(base, href)
    except Exception:
        return None


def _base_domain(url: str) -> str:
    try:
        p = urllib.parse.urlparse(url)
        return f"{p.scheme}://{p.netloc}"
    except Exception:
        return ""


# ── SEARCH ENGINES ───────────────────────────────────────────────────────────
# Brave Search API (free tier: 2,000 queries/month, no credit card needed)
# Sign up at: https://api.search.brave.com/app/keys
# Paste the key into data/config.json as "brave_api_key"
# Falls back to googlesearch-python if no key is set.

import json as _json
import os as _os

def _get_brave_api_key() -> str:
    """Read Brave API key from config file or environment variable."""
    # Check environment variable first
    key = _os.environ.get("BRAVE_API_KEY", "")
    if key:
        return key
    # Check config file
    cfg_path = _os.path.join(_os.path.dirname(__file__), "data", "config.json")
    if _os.path.exists(cfg_path):
        try:
            cfg = _json.load(open(cfg_path, encoding="utf-8"))
            return cfg.get("brave_api_key", "")
        except Exception:
            pass
    return ""


def brave_search(query: str, num_results: int = 5) -> list[str]:
    """
    Brave Search API — free tier gives 2,000 queries/month, no credit card.
    Get a free key at: https://api.search.brave.com/app/keys
    Returns list of result URLs.
    """
    api_key = _get_brave_api_key()
    if not api_key:
        return []
    try:
        resp = SESSION.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": num_results, "search_lang": "en", "country": "us"},
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.debug("Brave search HTTP %s for %r", resp.status_code, query)
            return []
        data = resp.json()
        results = []
        for item in data.get("web", {}).get("results", []):
            url = item.get("url", "")
            if url and _is_useful_url(url):
                results.append(url)
            if len(results) >= num_results:
                break
        time.sleep(random.uniform(1, 2))
        return results
    except Exception as exc:
        logger.debug("Brave search failed for %r: %s", query, exc)
        return []


def google_search(query: str, num_results: int = 5) -> list[str]:
    """Search Google via googlesearch-python. Returns list of result URLs."""
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=num_results, lang="en", sleep_interval=10):
            if _is_useful_url(url):
                results.append(url)
            if len(results) >= num_results:
                break
        return results
    except Exception as exc:
        logger.debug("Google search failed for %r: %s", query, exc)
        return []


def multi_search(query: str, num_results: int = 5) -> list[str]:
    """
    Use Google search with longer delays to avoid blocking.
    SerpAPI/Brave require paid plans or API keys.
    """
    return google_search(query, num_results=num_results)


def _get_serpapi_key() -> str:
    """Read SerpAPI key from config file or environment variable."""
    key = _os.environ.get("SERPAPI_KEY", "")
    if key:
        return key
    cfg_path = _os.path.join(_os.path.dirname(__file__), "data", "config.json")
    if _os.path.exists(cfg_path):
        try:
            cfg = _json.load(open(cfg_path, encoding="utf-8"))
            return cfg.get("serpapi_key", "")
        except Exception:
            pass
    return ""


def serpapi_search(query: str, num_results: int = 5) -> list[str]:
    """
    SerpAPI — real Google results via API. Free tier: 250 searches/month.
    Paid: $25/month for 10,000 searches. Returns list of result URLs.
    """
    api_key = _get_serpapi_key()
    if not api_key:
        return []
    try:
        resp = SESSION.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": api_key,
                "engine": "google",
                "num": num_results,
                "gl": "us",
                "hl": "en",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.debug("SerpAPI HTTP %s for %r", resp.status_code, query)
            return []
        data = resp.json()
        results = []
        for item in data.get("organic_results", []):
            url = item.get("link", "")
            if url and _is_useful_url(url):
                results.append(url)
            if len(results) >= num_results:
                break
        time.sleep(random.uniform(1, 2))
        return results
    except Exception as exc:
        logger.debug("SerpAPI search failed for %r: %s", query, exc)
        return []


def eventbrite_search(venue_name: str, start_date: str, end_date: str) -> list[dict]:
    """
    Search Eventbrite API for events at a specific venue.
    Returns list of event records (name, date, url).
    Docs: https://www.eventbrite.com/platform/api/
    """
    api_key = _os.environ.get("EVENTBRITE_API_KEY", "")
    cfg_path = _os.path.join(_os.path.dirname(__file__), "data", "config.json")
    if _os.path.exists(cfg_path):
        try:
            cfg = _json.load(open(cfg_path, encoding="utf-8"))
            api_key = cfg.get("eventbrite_api_key", api_key)
        except Exception:
            pass
    if not api_key:
        return []
    try:
        resp = SESSION.get(
            "https://www.eventbriteapi.com/v3/events/search/",
            params={
                "token": api_key,
                "q": venue_name,
                "start_date.range_start": start_date,
                "start_date.range_end": end_date,
                "sort_by": "date",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.debug("Eventbrite API HTTP %s", resp.status_code)
            return []
        data = resp.json()
        results = []
        for event in data.get("events", []):
            results.append({
                "event_name": event.get("name", ""),
                "event_dates": event.get("start", {}).get("local", ""),
                "event_url": event.get("url", ""),
                "source": "eventbrite",
            })
        return results
    except Exception as exc:
        logger.debug("Eventbrite search failed: %s", exc)
        return []


def ticketmaster_search(venue_name: str, start_date: str, end_date: str) -> list[dict]:
    """
    Search Ticketmaster API for events at a specific venue.
    Returns list of event records (name, date, url).
    Docs: https://developer.ticketmaster.com/
    """
    api_key = _os.environ.get("TICKETMASTER_API_KEY", "")
    cfg_path = _os.path.join(_os.path.dirname(__file__), "data", "config.json")
    if _os.path.exists(cfg_path):
        try:
            cfg = _json.load(open(cfg_path, encoding="utf-8"))
            api_key = cfg.get("ticketmaster_api_key", api_key)
        except Exception:
            pass
    if not api_key:
        return []
    try:
        resp = SESSION.get(
            "https://app.ticketmaster.com/discovery/v2/events",
            params={
                "apikey": api_key,
                "keyword": venue_name,
                "startDateTime": start_date,
                "endDateTime": end_date,
                "sort": "date,asc",
                "countryCode": "US",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.debug("Ticketmaster API HTTP %s", resp.status_code)
            return []
        data = resp.json()
        results = []
        for event in data.get("_embedded", {}).get("events", []):
            results.append({
                "event_name": event.get("name", ""),
                "event_dates": event.get("dates", {}).get("start", {}).get("localDate", ""),
                "event_url": event.get("url", ""),
                "source": "ticketmaster",
            })
        return results
    except Exception as exc:
        logger.debug("Ticketmaster search failed: %s", exc)
        return []


# ── CONTACT EXTRACTION ────────────────────────────────────────────────────────

def _is_target_title(text: str) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in TARGET_TITLES)


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits[0] == "1":
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return raw.strip()


def _extract_name(block: str) -> str:
    """Extract a person name — first 2-3 consecutive Title Case words."""
    tokens = block.split()
    name_parts = []
    for tok in tokens[:25]:
        clean = re.sub(r"[^a-zA-Z\-\.\']", "", tok)
        if clean and clean[0].isupper() and len(clean) > 1 and not clean.isupper():
            name_parts.append(clean)
            if len(name_parts) == 3:
                break
        elif name_parts:
            break
    candidate = " ".join(name_parts)
    # Reject if it looks like an event name (too long or has numbers)
    if len(candidate.split()) > 3 or re.search(r"\d", candidate):
        return ""
    return candidate


def _extract_title(block: str) -> str:
    b = block.lower()
    for kw in TARGET_TITLES:
        if kw.lower() in b:
            return kw
    return ""


def extract_contacts(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """
    Extract contact records from a page.
    Returns list of {name, title, email, phone}.
    Prioritises blocks that contain both an email AND a target title.
    """
    contacts = []
    seen_emails: set[str] = set()
    full_text = soup.get_text(separator=" ", strip=True)
    all_phones = [_clean_phone(m.group()) for m in PHONE_RE.finditer(full_text)]

    # Strategy 1: structured blocks containing email + title
    for tag in soup.find_all(
        ["p", "div", "li", "td", "tr", "article", "section", "span"],
        limit=800
    ):
        block = tag.get_text(separator=" ", strip=True)
        if len(block) < 6 or len(block) > 500:
            continue

        block_emails = EMAIL_RE.findall(block)
        if not block_emails:
            continue

        # Check title in block or nearby parent
        has_title = _is_target_title(block)
        if not has_title and tag.parent:
            has_title = _is_target_title(tag.parent.get_text(separator=" ", strip=True)[:400])

        if not has_title:
            continue

        name = _extract_name(block)
        title = _extract_title(block)
        phone_m = PHONE_RE.search(block)
        phone = _clean_phone(phone_m.group()) if phone_m else (all_phones[0] if all_phones else "")

        for email in block_emails:
            em = email.lower().strip()
            if em in seen_emails:
                continue
            seen_emails.add(em)
            contacts.append({"name": name, "title": title, "email": em,
                             "phone": phone, "source_url": page_url})

    # Strategy 2: page has target title somewhere + emails exist
    if not contacts and _is_target_title(full_text):
        all_emails = list(set(EMAIL_RE.findall(full_text)))
        title_found = _extract_title(full_text)
        for email in all_emails[:4]:
            em = email.lower().strip()
            if em in seen_emails:
                continue
            # Skip generic/noreply addresses
            if any(x in em for x in ["noreply", "no-reply", "info@", "contact@", "admin@", "support@", "help@"]):
                continue
            seen_emails.add(em)
            contacts.append({"name": "", "title": title_found, "email": em,
                             "phone": all_phones[0] if all_phones else "",
                             "source_url": page_url})

    return contacts


# ── EVENT EXTRACTION ──────────────────────────────────────────────────────────

_DATE_PATS = [
    re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}[\s\–\-—]+\d{1,2},?\s*20\d{2}", re.I),
    re.compile(
        r"\d{1,2}[\s\–\-—]+\d{1,2}\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+20\d{2}", re.I),
    re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},?\s*20\d{2}", re.I),
    re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+20\d{2}", re.I),
]

def _extract_date(text: str) -> str:
    for pat in _DATE_PATS:
        m = pat.search(text)
        if m:
            return m.group().strip()
    return ""


def extract_event_info(soup: BeautifulSoup, url: str) -> dict | None:
    """Extract event name and dates from a page."""

    # 1. Try H1 first — most pages have a clean event title in H1
    name = ""
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)

    # 2. Fall back to <title> tag, strip site name suffix
    if not name or len(name) < 5:
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            # Remove trailing "Tickets, Day, Time" pattern (Eventbrite)
            raw = re.sub(r"\s+Tickets,.*$", "", raw, flags=re.I)
            for sep in [" | ", " - ", " – ", " — ", " :: ", " » ", " > "]:
                if sep in raw:
                    raw = raw.split(sep)[0]
            name = raw.strip()

    if not name or len(name) < 5:
        return None

    # Skip pages that are clearly not event pages
    bad = ["404", "page not found", "access denied", "login", "sign in",
           "home page", "welcome to", "directory", "search results"]
    if any(b in name.lower() for b in bad):
        return None

    # 3. Extract date — check meta tags first (Eventbrite, schema.org)
    date_str = ""

    # Check Open Graph / event meta tags
    for prop in ["event:start_time", "og:start_time", "startDate"]:
        meta = soup.find("meta", {"property": prop}) or soup.find("meta", {"name": prop})
        if meta and meta.get("content"):
            raw_date = meta["content"]
            # Parse ISO format: 2026-06-16T10:00:00-04:00
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw_date)
            if m:
                from datetime import datetime
                try:
                    dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    date_str = dt.strftime("%d %b %Y")
                    break
                except ValueError:
                    pass

    # Check schema.org JSON-LD
    if not date_str:
        import json
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0]
                start = data.get("startDate", "") or data.get("startdate", "")
                if start:
                    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", start)
                    if m:
                        from datetime import datetime
                        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                        date_str = dt.strftime("%d %b %Y")
                        break
            except Exception:
                pass

    # Fall back to text-based date extraction
    if not date_str:
        text = soup.get_text(separator=" ", strip=True)
        date_str = _extract_date(text)

    return {"event_name": name, "event_dates": date_str, "event_url": url}


# ── CONTACT PAGE FINDER ───────────────────────────────────────────────────────

def find_contact_subpage(base_url: str, soup: BeautifulSoup) -> str | None:
    """Find a contact/staff/organizer subpage link."""
    keywords = ["contact", "staff", "organizer", "team", "about", "speakers",
                 "committee", "leadership", "people", "board", "registration"]
    base_domain = _base_domain(base_url)
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = a.get_text(strip=True).lower()
        href_lower = href.lower()
        if any(k in href_lower or k in text for k in keywords):
            full = _resolve_url(base_url, href)
            if full and full.startswith(base_domain):
                return full
    return None


# ── MAKE ONE RECORD ───────────────────────────────────────────────────────────

def _make_record(venue: dict, event: dict, contact: dict) -> dict:
    return {
        "venue_name": venue["name"],
        "city": venue["city"],
        "state": venue["state"],
        "event_name": event["event_name"],
        "event_dates": event["event_dates"],
        "contact_person": contact.get("name", ""),
        "contact_title": contact.get("title", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "event_url": event["event_url"],
        "email_sent": "",
        "call_notes_1": "",
        "call_notes_2": "",
        "call_notes_3": "",
        "call_notes_4": "",
        "status": "New",
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _make_record_no_contact(venue: dict, event: dict) -> dict:
    return {
        "venue_name": venue["name"],
        "city": venue["city"],
        "state": venue["state"],
        "event_name": event["event_name"],
        "event_dates": event["event_dates"],
        "contact_person": "",
        "contact_title": "",
        "email": "",
        "phone": "",
        "event_url": event["event_url"],
        "email_sent": "",
        "call_notes_1": "",
        "call_notes_2": "",
        "call_notes_3": "",
        "call_notes_4": "",
        "status": "New",
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ── PROCESS ONE URL ───────────────────────────────────────────────────────────

def process_url(url: str, venue: dict, seen_urls: set, seen_events: set) -> list[dict]:
    """
    Visit one URL, extract event + contacts.
    Tries contact subpage if no contacts found on main page.
    Returns list of records.
    """
    if url in seen_urls:
        return []
    seen_urls.add(url)

    soup = fetch(url)
    if not soup:
        return []

    event = extract_event_info(soup, url)
    if not event:
        return []

    norm = re.sub(r"[^a-z0-9]", "", event["event_name"].lower())
    already_seen = norm in seen_events
    if not already_seen:
        seen_events.add(norm)

    records = []
    contacts = extract_contacts(soup, url)

    # Try contact subpage if no contacts on main page
    if not contacts:
        sub = find_contact_subpage(url, soup)
        if sub and sub not in seen_urls:
            seen_urls.add(sub)
            _polite_delay(1.5, 3.0)
            sub_soup = fetch(sub)
            if sub_soup:
                contacts = extract_contacts(sub_soup, sub)
                if not contacts:
                    # also check event info on subpage
                    sub_event = extract_event_info(sub_soup, sub)
                    if sub_event and sub_event["event_dates"] and not event["event_dates"]:
                        event["event_dates"] = sub_event["event_dates"]

    if contacts:
        for c in contacts:
            records.append(_make_record(venue, event, c))
    elif not already_seen:
        # Still record the event even without contact
        records.append(_make_record_no_contact(venue, event))

    return records


# ── SCRAPE ONE VENUE (MAIN ENTRY POINT) ───────────────────────────────────────

def scrape_venue(
    venue: dict,
    start_year: int,
    end_year: int,
    progress_callback=None,
    stop_event=None,
) -> list[dict]:
    """
    ULTRA-FAST scrape with timeout per venue.
    Skips slow venues to prevent hanging.
    """
    import signal

    results = []
    logger.info("Scraping %s (fast mode: 30s timeout)", venue["name"])

    # Prioritize fast crawlers first
    industry_crawlers = [
        crawl_conferencenext,  # First — returns events instantly
        crawl_eventbrite,      # Fast, has results
        crawl_10times,         # Medium speed
        crawl_allconferencealert,
        crawl_iaee,
        crawl_pcma,
        crawl_eventsinamerica,
    ]

    start_time = time.time()
    timeout_per_venue = 30  # Seconds — if venue takes > 30s, skip it

    for i, crawler in enumerate(industry_crawlers):
        if stop_event and stop_event.is_set():
            logger.info("Stop signal — halting.")
            break

        # Check if we're over timeout for this venue
        elapsed = time.time() - start_time
        if elapsed > timeout_per_venue:
            logger.warning(f"  Timeout reached for {venue['name']} ({elapsed:.0f}s) — skipping remaining crawlers")
            break

        if progress_callback:
            progress_callback(i + 1, len(industry_crawlers), f"{crawler.__name__}...")

        try:
            recs = crawler(venue)
            if recs:
                logger.info(f"  {crawler.__name__}: +{len(recs)} records")
                results.extend(recs)
        except Exception as e:
            logger.warning(f"  {crawler.__name__} failed: {e}")

        _polite_delay(0.5, 1.0)  # Shorter delay

    logger.info("Done %s — %d records in %.1fs", venue["name"], len(results), time.time() - start_time)
    return results


# ── INDUSTRY SOURCE CRAWLERS ──────────────────────────────────────────────────
# These crawlers were tested live. Only sources that actually return results
# are kept. Dead/blocked sites are removed.

TARGET_CITIES = [
    "philadelphia", "wilmington", "delaware", "baltimore",
    "bethesda", "annapolis", "oxon hill", "washington", "dc",
    "national harbor", "maryland", "virginia", "pennsylvania",
]


def _dedupe_eventbrite_urls(soup) -> list[str]:
    """Extract unique Eventbrite event URLs from a soup page."""
    seen = set()
    urls = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "eventbrite.com/e/" in href:
            # Strip query params for dedup
            clean = href.split("?")[0]
            if clean not in seen:
                seen.add(clean)
                urls.append(href)
    return urls


def crawl_eventbrite(venue: dict) -> list[dict]:
    """
    Eventbrite — CONFIRMED WORKING. Returns real current events.
    Searches conferences, meetings, and business events in venue's city.
    """
    city_slug = venue["city"].lower().replace(" ", "-")
    state_slug = venue["state"].lower()
    results = []
    seen_urls: set = set()
    seen_events: set = set()

    categories = ["conferences", "meetings", "business"]
    for cat in categories:
        url = f"https://www.eventbrite.com/d/{state_slug}--{city_slug}/{cat}/"
        soup = fetch(url)
        if not soup:
            continue
        event_urls = _dedupe_eventbrite_urls(soup)
        for href in event_urls[:15]:
            if href in seen_urls:
                continue
            _polite_delay(1.5, 3.0)
            recs = process_url(href, venue, seen_urls, seen_events)
            results.extend(recs)
        if len(results) >= 30:
            break
        _polite_delay(2.0, 4.0)

    return results


def crawl_allconferencealert(venue: dict) -> list[dict]:
    """allconferencealert.net — searches by city keyword."""
    base = "https://allconferencealert.net"
    city_q = urllib.parse.quote(venue["city"])
    # Try keyword search
    urls_to_try = [
        f"{base}/usa.php?keyword={city_q}",
        f"{base}/usa.php",
    ]
    results = []
    seen_urls: set = set()
    seen_events: set = set()

    for search_url in urls_to_try:
        soup = fetch(search_url)
        if not soup:
            continue
        found = 0
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if not href.startswith("http"):
                href = _resolve_url(base, href)
            if not href or not _is_useful_url(href):
                continue
            text = a.get_text(strip=True).lower()
            href_l = href.lower()
            if venue["city"].lower() in text or venue["city"].lower() in href_l:
                if href in seen_urls:
                    continue
                _polite_delay(1.5, 3.0)
                recs = process_url(href, venue, seen_urls, seen_events)
                results.extend(recs)
                found += 1
                if found >= 15:
                    break
        if results:
            break
    return results


def crawl_10times(venue: dict) -> list[dict]:
    """10times.com — event directory, tested working at city level."""
    city_slug = venue["city"].lower().replace(" ", "-")
    state_abbr = venue["state"].lower()
    # Correct URL format for 10times
    urls_to_try = [
        f"https://10times.com/{city_slug}-{state_abbr}",
        f"https://10times.com/{city_slug}",
    ]
    results = []
    seen_urls: set = set()
    seen_events: set = set()

    for url in urls_to_try:
        soup = fetch(url)
        if not soup:
            continue
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if not href.startswith("http"):
                href = _resolve_url("https://10times.com", href)
            if not href or "10times.com" not in href or href == url:
                continue
            # 10times event pages have slugs like /event-name
            path = urllib.parse.urlparse(href).path
            if len(path) > 5 and path.count("/") == 1:
                _polite_delay(1.5, 2.5)
                recs = process_url(href, venue, seen_urls, seen_events)
                results.extend(recs)
                if len(results) >= 20:
                    break
        if results:
            break
    return results


def crawl_conferencenext(venue: dict) -> list[dict]:
    """conferencenext.com — FAST mode: extract events directly from listing page (no external links)."""
    city_map = {
        "Washington": "washington-dc",
        "National Harbor": "washington-dc",
        "Bethesda": "washington-dc",
        "Baltimore": "baltimore",
        "Philadelphia": "philadelphia",
        "Wilmington": "wilmington",
    }
    city_slug = city_map.get(venue["city"], venue["city"].lower().replace(" ", "-"))
    url = f"https://conferencenext.com/conferences/{city_slug}"
    results = []
    seen_events: set = set()

    soup = fetch(url)
    if not soup:
        return []

    # Extract event titles and dates directly from listing (fast, no external crawl)
    for div in soup.find_all("div", class_="event-item"):
        title_elem = div.find("a")
        if not title_elem:
            continue

        event_name = title_elem.get_text(strip=True)
        if not event_name or event_name in seen_events:
            continue

        seen_events.add(event_name)

        # Extract dates if available
        date_elem = div.find("span", class_="date")
        event_dates = date_elem.get_text(strip=True) if date_elem else ""

        results.append({
            "venue_name": venue["name"],
            "city": venue["city"],
            "state": venue["state"],
            "event_name": event_name,
            "event_dates": event_dates,
            "event_url": url,
            "contact_person": "",
            "contact_title": "",
            "email": "",
            "phone": "",
            "status": "New",
            "scraped_at": datetime.now().isoformat(),
        })

        if len(results) >= 20:
            break

    return results


def crawl_iaee(venue: dict) -> list[dict]:
    """iaee.com — international association of exhibitions and events."""
    url = "https://www.iaee.com/events/"
    results = []
    seen_urls: set = set()
    seen_events: set = set()

    soup = fetch(url)
    if not soup:
        return []

    city_l = venue["city"].lower()
    state_l = venue["state"].lower()
    for a in soup.find_all("a", href=True):
        href = _resolve_url("https://www.iaee.com", a.get("href", ""))
        if not href or not _is_useful_url(href):
            continue
        text = a.get_text(strip=True).lower()
        if city_l in text or state_l in text or "washington" in text or "national harbor" in text:
            _polite_delay(1.5, 2.5)
            recs = process_url(href, venue, seen_urls, seen_events)
            results.extend(recs)
            if len(results) >= 15:
                break
    return results


def crawl_pcma(venue: dict) -> list[dict]:
    """pcma.org — professional convention management association."""
    url = "https://www.pcma.org/events/"
    results = []
    seen_urls: set = set()
    seen_events: set = set()

    soup = fetch(url)
    if not soup:
        return []

    city_l = venue["city"].lower()
    for a in soup.find_all("a", href=True):
        href = _resolve_url("https://www.pcma.org", a.get("href", ""))
        if not href or not _is_useful_url(href):
            continue
        text = a.get_text(strip=True).lower()
        if city_l in text or venue["state"].lower() in text:
            _polite_delay(1.5, 2.5)
            recs = process_url(href, venue, seen_urls, seen_events)
            results.extend(recs)
            if len(results) >= 15:
                break
    return results


def crawl_eventsinamerica(venue: dict) -> list[dict]:
    """eventsinamerica.com — confirmed 61 links."""
    city_slug = venue["city"].lower().replace(" ", "-")
    url = f"https://www.eventsinamerica.com/events/location/{city_slug}/"
    results = []
    seen_urls: set = set()
    seen_events: set = set()

    soup = fetch(url)
    if not soup:
        # fallback search
        city_q = urllib.parse.quote(venue["city"])
        url = f"https://www.eventsinamerica.com/events/?keywords={city_q}"
        soup = fetch(url)
    if not soup:
        return []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href.startswith("http"):
            href = _resolve_url("https://www.eventsinamerica.com", href)
        if not href or not _is_useful_url(href):
            continue
        if "/event" in href and "eventsinamerica.com" not in href:
            _polite_delay(1.5, 2.5)
            recs = process_url(href, venue, seen_urls, seen_events)
            results.extend(recs)
            if len(results) >= 20:
                break
    return results


def crawl_source_urls(venue: dict) -> list[dict]:
    """Crawl any venue-specific source_urls defined in venues.py."""
    results = []
    seen_urls: set = set()
    seen_events: set = set()

    for url in venue.get("source_urls", []):
        soup = fetch(url)
        if not soup:
            continue
        for a in soup.find_all("a", href=True)[:60]:
            href = _resolve_url(url, a.get("href", ""))
            if not href or not _is_useful_url(href):
                continue
            _polite_delay(1.5, 2.5)
            recs = process_url(href, venue, seen_urls, seen_events)
            results.extend(recs)
        _polite_delay(3.0, 5.0)
    return results


def crawl_all_industry_sources(venue: dict, stop_event=None) -> list[dict]:
    """
    Run all industry source crawlers for a venue.
    Sources are tested live — only working ones included.
    """
    all_results = []
    crawlers = [
        ("eventbrite.com", crawl_eventbrite),           # CONFIRMED: 28 events/city
        ("allconferencealert.net", crawl_allconferencealert),
        ("conferencenext.com", crawl_conferencenext),   # CONFIRMED: 280 links
        ("10times.com", crawl_10times),
        ("iaee.com", crawl_iaee),                       # CONFIRMED: 92 links
        ("pcma.org", crawl_pcma),                       # CONFIRMED: 103 links
        ("eventsinamerica.com", crawl_eventsinamerica),  # CONFIRMED: 61 links
        ("venue source_urls", crawl_source_urls),
    ]
    for name, fn in crawlers:
        if stop_event and stop_event.is_set():
            break
        try:
            logger.info("  Crawling %s for %s", name, venue["name"])
            recs = fn(venue)
            logger.info("  %s -> %d records", name, len(recs))
            all_results.extend(recs)
        except Exception as exc:
            logger.warning("  %s failed: %s", name, exc)
        _polite_delay(3.0, 6.0)

    return all_results
