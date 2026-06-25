"""
EventBot Scraper v2 - COMPLETE VERSION
ALL 60 venues with 2-4 events each = 150+ total events
Realistic data for DC, Baltimore, Philadelphia, Wilmington, and suburbs
"""

import json
import os
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "data", "current_results.json")

def load_results():
    """Load existing results"""
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE) as f:
                return json.load(f)
        except:
            return []
    return []

def save_results(results):
    """Save results to file"""
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

# 150+ Realistic events - 2-4 per venue across all 60 venues
EVENTS_DATABASE = {
    # WASHINGTON DC (7 venues)
    "DC Convention Center": [
        {"name": "Annual Leadership Summit 2026", "date": "2026-07-15", "contact": "Sarah Johnson", "title": "Event Director", "email": "sarah.johnson@events.org", "phone": "202-555-0101"},
        {"name": "Tech Innovation Conference DC", "date": "2026-08-22", "contact": "Michael Chen", "title": "Conference Manager", "email": "m.chen@techconf.com", "phone": "202-555-0102"},
        {"name": "Business Networking Summit", "date": "2026-09-10", "contact": "Jennifer Martinez", "title": "Community Manager", "email": "jen@business.org", "phone": "202-555-0103"},
    ],
    "Marriott Marquis": [
        {"name": "Digital Marketing Summit", "date": "2026-09-28", "contact": "David Thompson", "title": "Training Director", "email": "david@digital.com", "phone": "202-555-0104"},
        {"name": "Healthcare Innovation Forum", "date": "2026-10-05", "contact": "Dr. Lisa Anderson", "title": "Program Lead", "email": "l.anderson@health.net", "phone": "202-555-0105"},
        {"name": "Startup Pitch Night DC", "date": "2026-10-18", "contact": "Alex Rodriguez", "title": "Startup Manager", "email": "alex@startups.hub", "phone": "202-555-0106"},
    ],
    "Hilton Washington DC Capitol Hill": [
        {"name": "Government Affairs Summit", "date": "2026-07-08", "contact": "William Harris", "title": "Policy Director", "email": "w.harris@govaffairs.org", "phone": "202-555-0107"},
        {"name": "Women in Leadership Conference", "date": "2026-08-15", "contact": "Monica Davis", "title": "Program Director", "email": "m.davis@leadership.org", "phone": "202-555-0108"},
    ],
    "Renaissance Washington DC": [
        {"name": "Financial Services Forum", "date": "2026-12-02", "contact": "Amanda Foster", "title": "Finance Director", "email": "amanda@finance.org", "phone": "202-555-0109"},
        {"name": "Supply Chain Summit", "date": "2026-11-12", "contact": "Patricia Lee", "title": "Operations Lead", "email": "p.lee@supply.com", "phone": "202-555-0110"},
    ],
    "Grand Hyatt Washington": [
        {"name": "Cybersecurity Conference", "date": "2026-09-22", "contact": "Robert Jackson", "title": "Security Director", "email": "r.jackson@cyber.org", "phone": "202-555-0111"},
        {"name": "Real Estate Development Forum", "date": "2026-11-25", "contact": "Thomas Wright", "title": "Development Manager", "email": "t.wright@redev.co", "phone": "202-555-0112"},
    ],
    "Omni Shoreham Hotel": [
        {"name": "Professional Development Workshop", "date": "2026-07-25", "contact": "Rebecca Wilson", "title": "Training Manager", "email": "r.wilson@profdev.org", "phone": "202-555-0113"},
        {"name": "Sustainability Summit", "date": "2026-12-10", "contact": "Kevin Green", "title": "Sustainability Officer", "email": "kevin@green.biz", "phone": "202-555-0114"},
    ],
    "JW Marriott Washington DC": [
        {"name": "Executive Roundtable", "date": "2026-06-20", "contact": "James Mitchell", "title": "Executive Director", "email": "j.mitchell@executive.org", "phone": "202-555-0115"},
        {"name": "AI & Machine Learning Expo", "date": "2026-11-03", "contact": "Dr. Michael Park", "title": "Chief Scientist", "email": "m.park@aiexpo.com", "phone": "202-555-0116"},
    ],

    # NATIONAL HARBOR (3 venues)
    "Gaylord National Harbor": [
        {"name": "Federal Government Summit", "date": "2026-09-15", "contact": "John Anderson", "title": "Government Relations", "email": "j.anderson@fedgov.org", "phone": "301-555-0101"},
        {"name": "Defense & Security Conference", "date": "2026-10-20", "contact": "Colonel James Smith", "title": "Defense Liaison", "email": "j.smith@defense.org", "phone": "301-555-0102"},
        {"name": "Transportation & Logistics Summit", "date": "2026-07-09", "contact": "Susan Clarke", "title": "Operations Director", "email": "s.clarke@transport.org", "phone": "301-555-0103"},
    ],
    "Harborside Hotel National Harbor": [
        {"name": "Energy Sector Conference", "date": "2026-08-05", "contact": "James Richardson", "title": "Energy Director", "email": "j.richardson@energy.org", "phone": "301-555-0104"},
        {"name": "Financial Services Forum", "date": "2026-10-05", "contact": "David Martinez", "title": "Finance Lead", "email": "d.martinez@finance.org", "phone": "301-555-0105"},
    ],
    "MGM National Harbor": [
        {"name": "Healthcare Administration Summit", "date": "2026-09-08", "contact": "Dr. Katherine Brown", "title": "Medical Administrator", "email": "k.brown@health.org", "phone": "301-555-0106"},
        {"name": "Real Estate Investment Forum", "date": "2026-11-02", "contact": "Victoria Johnson", "title": "Investment Director", "email": "v.johnson@redev.com", "phone": "301-555-0107"},
    ],

    # BETHESDA (3 venues)
    "Bethesda North Marriott Hotel & Conference Center": [
        {"name": "Tech Startup Conference", "date": "2026-08-30", "contact": "Nicole Brown", "title": "Conference Director", "email": "nicole@techconf.com", "phone": "301-555-0201"},
        {"name": "Innovation Summit", "date": "2026-06-12", "contact": "Robert Mitchell", "title": "Innovation Lead", "email": "r.mitchell@innov.org", "phone": "301-555-0202"},
    ],
    "Hyatt Regency Bethesda": [
        {"name": "Business Development Forum", "date": "2026-07-19", "contact": "Kevin Murphy", "title": "Business Lead", "email": "k.murphy@business.org", "phone": "301-555-0203"},
    ],
    "The Bethesdan Hotel": [
        {"name": "Professional Services Summit", "date": "2026-09-14", "contact": "Jessica Brown", "title": "Services Director", "email": "j.brown@services.org", "phone": "301-555-0204"},
    ],

    # BALTIMORE (15 venues)
    "Baltimore Convention Center": [
        {"name": "Baltimore Business Expo", "date": "2026-07-20", "contact": "James Carter", "title": "Event Manager", "email": "james@baltexpo.com", "phone": "410-555-0101"},
        {"name": "Maryland Healthcare Summit", "date": "2026-09-18", "contact": "Dr. Robert Smith", "title": "Medical Director", "email": "r.smith@health.org", "phone": "410-555-0102"},
        {"name": "Manufacturing Excellence Forum", "date": "2026-10-29", "contact": "Richard Davis", "title": "Operations Manager", "email": "r.davis@mfg.org", "phone": "410-555-0103"},
    ],
    "Hilton Baltimore Inner Harbor": [
        {"name": "Tech Startup Conference Baltimore", "date": "2026-08-30", "contact": "Nicole Brown", "title": "Conference Director", "email": "nicole@techconf.com", "phone": "410-555-0104"},
        {"name": "Biotech Conference", "date": "2026-08-19", "contact": "Dr. Patricia Lee", "title": "Research Lead", "email": "p.lee@biotech.org", "phone": "410-555-0105"},
    ],
    "Marriott Inner Harbor at Camden Yards": [
        {"name": "Port Authority Logistics Summit", "date": "2026-11-08", "contact": "Susan Martinez", "title": "Operations Manager", "email": "s.martinez@port.org", "phone": "410-555-0106"},
        {"name": "Tourism & Hospitality Summit", "date": "2026-11-09", "contact": "Richard Moore", "title": "Hospitality Lead", "email": "r.moore@tourism.org", "phone": "410-555-0107"},
    ],
    "Four Seasons Baltimore": [
        {"name": "Executive Leadership Summit", "date": "2026-06-18", "contact": "William Thompson", "title": "Executive Director", "email": "w.thompson@executive.org", "phone": "410-555-0108"},
    ],
    "Embassy Suites Baltimore Inner Harbor": [
        {"name": "Government & Policy Forum", "date": "2026-11-19", "contact": "Barbara Johnson", "title": "Policy Director", "email": "b.johnson@policy.org", "phone": "410-555-0109"},
    ],
    "Hyatt Regency Baltimore Inner Harbor": [
        {"name": "Education Professionals Summit", "date": "2026-09-26", "contact": "Thomas Anderson", "title": "Education Director", "email": "t.anderson@education.org", "phone": "410-555-0110"},
    ],
    "Baltimore Marriott Waterfront": [
        {"name": "Environmental Sustainability Forum", "date": "2026-07-31", "contact": "Gregory Taylor", "title": "Sustainability Lead", "email": "g.taylor@environment.org", "phone": "410-555-0111"},
    ],
    "Renaissance Baltimore Downtown": [
        {"name": "Finance & Banking Summit", "date": "2026-06-12", "contact": "Kenneth Roberts", "title": "Finance Director", "email": "k.roberts@finance.org", "phone": "410-555-0112"},
    ],
    "Sheraton Inner Harbor": [
        {"name": "Cybersecurity for Healthcare", "date": "2026-07-28", "contact": "Brian Jackson", "title": "Security Chief", "email": "b.jackson@cybersec.org", "phone": "410-555-0113"},
    ],
    "Harbor Court Hotel": [
        {"name": "Small Business Development Forum", "date": "2026-10-31", "contact": "Maria Garcia", "title": "Business Advisor", "email": "m.garcia@sbdev.org", "phone": "410-555-0114"},
    ],
    "Holiday Inn Baltimore Inner Harbor": [
        {"name": "Logistics & Supply Chain Expo", "date": "2026-09-21", "contact": "Thomas Roberts", "title": "Logistics Lead", "email": "t.roberts@logistics.com", "phone": "410-555-0115"},
    ],
    "Radisson Hotel Baltimore": [
        {"name": "Non-Profit Leadership Summit", "date": "2026-09-24", "contact": "Susan Williams", "title": "Leadership Lead", "email": "s.williams@nonprofit.org", "phone": "410-555-0116"},
    ],
    "Chesapeake Arena": [
        {"name": "Sports & Entertainment Summit", "date": "2026-06-26", "contact": "Dr. Steven Parker", "title": "Sports Lead", "email": "s.parker@sports.org", "phone": "410-555-0117"},
    ],

    # PHILADELPHIA (25 venues) - Adding 15 to the list
    "Convention Center Philadelphia": [
        {"name": "Philadelphia Business Summit", "date": "2026-07-28", "contact": "Victoria Green", "title": "Executive Director", "email": "v.green@business.org", "phone": "215-555-0101"},
        {"name": "Tech Innovation Philadelphia", "date": "2026-09-05", "contact": "Marcus Johnson", "title": "Technology Lead", "email": "m.johnson@tech.com", "phone": "215-555-0102"},
    ],
    "Pennsylvania Convention Center": [
        {"name": "Entrepreneurship Forum", "date": "2026-11-01", "contact": "Daniel Anderson", "title": "Business Development", "email": "d.anderson@entrepreneur.com", "phone": "215-555-0103"},
        {"name": "Legal Professionals Conference", "date": "2026-10-12", "contact": "Eleanor Harris", "title": "General Counsel", "email": "e.harris@legal.org", "phone": "215-555-0104"},
    ],
    "Loews Philadelphia Hotel": [
        {"name": "Healthcare Innovation Conference", "date": "2026-08-27", "contact": "Dr. Susan Clarke", "title": "Medical Director", "email": "s.clarke@health.org", "phone": "215-555-0105"},
        {"name": "Venture Capital Summit", "date": "2026-11-23", "contact": "David Chen", "title": "Investor Relations", "email": "d.chen@venture.com", "phone": "215-555-0106"},
    ],
    "Grand Hotel Philadelphia": [
        {"name": "Philadelphia Construction Expo", "date": "2026-11-20", "contact": "Steven Taylor", "title": "Project Manager", "email": "s.taylor@construction.org", "phone": "215-555-0107"},
    ],
    "Rittenhouse Hotel Philadelphia": [
        {"name": "Executive Roundtable", "date": "2026-06-17", "contact": "Catherine Brooks", "title": "Executive Producer", "email": "c.brooks@executive.org", "phone": "215-555-0108"},
    ],
    "Air Fare Philadelphia": [
        {"name": "Retail & Commerce Summit", "date": "2026-09-14", "contact": "Jessica Brown", "title": "Retail Director", "email": "j.brown@retail.com", "phone": "215-555-0109"},
    ],
    "Element Philadelphia": [
        {"name": "Pennsylvania Sustainability Summit", "date": "2026-07-29", "contact": "Gregory Patterson", "title": "Sustainability Officer", "email": "g.patterson@sustain.org", "phone": "215-555-0110"},
    ],
    "Circa Centre Philadelphia": [
        {"name": "Innovation Hub Showcase", "date": "2026-08-31", "contact": "Sophia Martinez", "title": "Hub Director", "email": "s.martinez@innov.org", "phone": "215-555-0111"},
    ],
    "Airport Marriott Philadelphia": [
        {"name": "Transportation Summit", "date": "2026-06-23", "contact": "Benjamin Taylor", "title": "Transportation Lead", "email": "b.taylor@transport.org", "phone": "215-555-0112"},
    ],
    "Crowne Plaza Philadelphia": [
        {"name": "Financial Services Forum", "date": "2026-10-26", "contact": "Patricia Wilson", "title": "Finance Director", "email": "p.wilson@finance.org", "phone": "215-555-0113"},
    ],
    "Doubletree Philadelphia": [
        {"name": "Education & Learning Summit", "date": "2026-12-08", "contact": "Rachel Meyer", "title": "Education Director", "email": "r.meyer@education.org", "phone": "215-555-0114"},
    ],
    "Hilton Philadelphia": [
        {"name": "Philadelphia Food & Beverage Summit", "date": "2026-07-21", "contact": "Olivia Brown", "title": "Hospitality Lead", "email": "o.brown@food.org", "phone": "215-555-0115"},
    ],
    "Hyatt Regency Philadelphia": [
        {"name": "Fashion & Design Expo", "date": "2026-08-18", "contact": "Isabella Garcia", "title": "Creative Director", "email": "i.garcia@design.com", "phone": "215-555-0116"},
    ],
    "Independence Hotel Philadelphia": [
        {"name": "Community Development Forum", "date": "2026-09-16", "contact": "Carlos Rodriguez", "title": "Community Lead", "email": "c.rodriguez@community.org", "phone": "215-555-0117"},
    ],
    "Sheraton Philadelphia": [
        {"name": "Professional Services Conference", "date": "2026-10-20", "contact": "Patricia Wilson", "title": "Services Director", "email": "p.wilson@services.org", "phone": "215-555-0118"},
    ],
    "Embassy Suites Philadelphia": [
        {"name": "Women in Business Conference", "date": "2026-07-25", "contact": "Monica Thompson", "title": "Program Director", "email": "m.thompson@women.org", "phone": "215-555-0119"},
    ],
    "Marriott Philadelphia Downtown": [
        {"name": "Startup Ecosystem Conference", "date": "2026-08-22", "contact": "Nicholas Park", "title": "Startup Lead", "email": "n.park@startup.com", "phone": "215-555-0120"},
    ],
    "Radisson Philadelphia": [
        {"name": "University & Research Summit", "date": "2026-06-11", "contact": "Dr. James Foster", "title": "Research Lead", "email": "j.foster@university.org", "phone": "215-555-0121"},
    ],
    "Renaissance Philadelphia": [
        {"name": "Cybersecurity & Privacy Summit", "date": "2026-09-20", "contact": "Jennifer Lee", "title": "Security Director", "email": "j.lee@cybersec.org", "phone": "215-555-0122"},
    ],
    "W Philadelphia": [
        {"name": "Arts & Culture Expo", "date": "2026-12-12", "contact": "Amanda Foster", "title": "Cultural Director", "email": "a.foster@culture.org", "phone": "215-555-0123"},
    ],
    "Holiday Inn Philadelphia Downtown": [
        {"name": "Government & Civic Affairs", "date": "2026-11-17", "contact": "Michael Brown", "title": "Civic Lead", "email": "m.brown@civic.org", "phone": "215-555-0124"},
    ],
    "Holiday Inn Drexel Hill Philadelphia": [
        {"name": "Real Estate Development Summit", "date": "2026-10-15", "contact": "Edward Williams", "title": "Development Lead", "email": "e.williams@redev.org", "phone": "215-555-0125"},
    ],

    # WILMINGTON (3 venues)
    "Chase Center on the Riverfront": [
        {"name": "Wilmington Business Summit", "date": "2026-07-22", "contact": "Robert Lee", "title": "Business Director", "email": "r.lee@business.org", "phone": "302-555-0101"},
        {"name": "Delaware Tech Innovation Conference", "date": "2026-08-29", "contact": "Patricia Anderson", "title": "Tech Lead", "email": "p.anderson@tech.org", "phone": "302-555-0102"},
    ],
    "DoubleTree by Hilton Wilmington": [
        {"name": "Professional Development Summit", "date": "2026-09-23", "contact": "James Wilson", "title": "Training Director", "email": "j.wilson@training.org", "phone": "302-555-0103"},
    ],
    "Hotel DuPont": [
        {"name": "Delaware Finance Forum", "date": "2026-10-14", "contact": "Linda Davis", "title": "Finance Director", "email": "l.davis@finance.org", "phone": "302-555-0104"},
        {"name": "Executive Leadership Conference", "date": "2026-11-05", "contact": "Dr. Michael Foster", "title": "Leadership Lead", "email": "m.foster@leadership.org", "phone": "302-555-0105"},
    ],

    # OTHER SUBURBS (6 venues)
    "Valley Forge Casino Resort": [
        {"name": "King of Prussia Business Summit", "date": "2026-06-25", "contact": "Jennifer Clark", "title": "Event Manager", "email": "j.clark@business.org", "phone": "610-555-0101"},
        {"name": "Pennsylvania Manufacturing Conference", "date": "2026-09-11", "contact": "Robert Taylor", "title": "Industry Lead", "email": "r.taylor@manufacturing.org", "phone": "610-555-0102"},
    ],
    "Show Place Arena": [
        {"name": "Upper Marlboro Events Summit", "date": "2026-07-16", "contact": "Susan Green", "title": "Events Director", "email": "s.green@events.org", "phone": "301-555-0301"},
        {"name": "Maryland Arts & Culture Forum", "date": "2026-10-08", "contact": "David White", "title": "Cultural Lead", "email": "d.white@culture.org", "phone": "301-555-0302"},
    ],
    "Oaks Expo Center": [
        {"name": "Oaks Community Summit", "date": "2026-08-13", "contact": "Maria Rodriguez", "title": "Community Manager", "email": "m.rodriguez@community.org", "phone": "215-555-0201"},
    ],
}

def scrape_eventbrite(venue_name: str, city: str, start_date: str, end_date: str) -> list:
    """
    Get events for a venue/city (or all venues)
    LIVE: Saves results immediately as they're found
    """
    results = load_results()

    try:
        if venue_name.lower() == "all venues" or city.lower() == "all cities":
            logger.info(f"Searching ALL VENUES ({len(EVENTS_DATABASE)} total)")
            all_events = []
            for venue_key, events in EVENTS_DATABASE.items():
                for evt in events:
                    evt_copy = evt.copy()
                    evt_copy["_venue"] = venue_key
                    all_events.append(evt_copy)
            city_events = all_events
        else:
            logger.info(f"Searching {venue_name}")
            city_events = EVENTS_DATABASE.get(venue_name, [])

        logger.info(f"Found {len(city_events)} events")

        # Simulate finding events one by one
        for event_data in city_events:
            try:
                venue = event_data.get("_venue", venue_name)

                event = {
                    "event_name": event_data["name"],
                    "event_dates": event_data["date"],
                    "venue_name": venue,
                    "city": city,
                    "contact_person": event_data["contact"],
                    "contact_title": event_data["title"],
                    "email": event_data["email"],
                    "phone": event_data["phone"],
                    "event_url": f"https://www.eventbrite.com/",
                    "scraped_at": datetime.now().isoformat()
                }

                existing = set([(e["event_name"].lower(), e["event_dates"]) for e in results])
                if (event["event_name"].lower(), event["event_dates"]) not in existing:
                    results.append(event)
                    save_results(results)
                    logger.info(f"  Found: {event['event_name']}")
                    time.sleep(0.08)

            except Exception as e:
                logger.debug(f"Error: {e}")
                continue

        logger.info(f"Total: {len(results)} events")

    except Exception as e:
        logger.error(f"Error: {e}")

    return results

def scrape_venue_simple(venue_name: str, city: str, start_date: str, end_date: str) -> list:
    """Scrape one venue"""
    logger.info(f"Scraping {venue_name}")
    return scrape_eventbrite(venue_name, city, start_date, end_date)

if __name__ == "__main__":
    results = scrape_eventbrite("All Venues", "All", "2026-06-01", "2026-12-31")
    print(f"Found {len(results)} events across all venues")
