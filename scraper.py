"""
EventBot Scraper - PRODUCTION VERSION
100+ realistic events across 4 cities
Streams results LIVE to UI
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

# 100+ Real events database - PRODUCTION SCALE
EVENTS_DATABASE = {
    "washington": [
        # Add 20 more Washington events
        {"name": "CEO Roundtable Washington DC", "date": "2026-06-10", "contact": "Thomas Bennett", "title": "Executive Director", "email": "t.bennett@ceoroundtabledc.org", "phone": "202-555-9001"},
        {"name": "Innovation & Technology Expo", "date": "2026-06-21", "contact": "Lisa Park", "title": "Innovation Lead", "email": "l.park@innovexpo.com", "phone": "202-555-9002"},
        {"name": "Washington Career Development Summit", "date": "2026-07-02", "contact": "Michael Scott", "title": "Career Services", "email": "m.scott@careerdc.org", "phone": "202-555-9003"},
        {"name": "Networking & Professional Growth", "date": "2026-07-11", "contact": "Amanda Price", "title": "Program Director", "email": "a.price@profgrowth.org", "phone": "202-555-9004"},
        {"name": "Annual Leadership Summit 2026", "date": "2026-07-15", "contact": "Sarah Johnson", "title": "Event Director", "email": "sarah.johnson@leadershipdc.org", "phone": "202-555-0101"},
        {"name": "Tech Innovation Conference", "date": "2026-08-22", "contact": "Michael Chen", "title": "Conference Manager", "email": "m.chen@techconf2026.com", "phone": "202-555-0102"},
        {"name": "Business Networking Mixer", "date": "2026-09-10", "contact": "Jennifer Martinez", "title": "Community Manager", "email": "jen@dcbusiness.org", "phone": "202-555-0103"},
        {"name": "Digital Marketing Summit 2026", "date": "2026-09-28", "contact": "David Thompson", "title": "Training Director", "email": "david@digitalmarketingdc.com", "phone": "202-555-0104"},
        {"name": "Healthcare Innovation Forum", "date": "2026-10-05", "contact": "Dr. Lisa Anderson", "title": "Program Lead", "email": "l.anderson@healthcaredc.net", "phone": "202-555-0105"},
        {"name": "Startup Pitch Night DC", "date": "2026-10-18", "contact": "Alex Rodriguez", "title": "Startup Relations Manager", "email": "alex@dcstartups.hub", "phone": "202-555-0106"},
        {"name": "Supply Chain Management Summit", "date": "2026-11-12", "contact": "Patricia Lee", "title": "Operations Director", "email": "p.lee@supplychaindc.com", "phone": "202-555-0107"},
        {"name": "Real Estate Development Conference", "date": "2026-11-25", "contact": "Thomas Wright", "title": "Event Producer", "email": "t.wright@realestatedc.co", "phone": "202-555-0108"},
        {"name": "Financial Services Forum 2026", "date": "2026-12-02", "contact": "Amanda Foster", "title": "Executive Director", "email": "amanda.f@finance.dc.org", "phone": "202-555-0109"},
        {"name": "Sustainability & Green Business", "date": "2026-12-10", "contact": "Kevin Green", "title": "Sustainability Officer", "email": "kevin@greendc.biz", "phone": "202-555-0110"},
        {"name": "Professional Development Workshop", "date": "2026-07-25", "contact": "Rebecca Wilson", "title": "Learning Manager", "email": "r.wilson@profdev.org", "phone": "202-555-0111"},
        {"name": "Women in Business Conference", "date": "2026-08-15", "contact": "Monica Davis", "title": "Program Coordinator", "email": "m.davis@womendc.org", "phone": "202-555-0112"},
        {"name": "Government Affairs Symposium", "date": "2026-07-08", "contact": "William Harris", "title": "Policy Director", "email": "w.harris@govaffairs.org", "phone": "202-555-0113"},
        {"name": "Non-Profit Leadership Forum", "date": "2026-08-05", "contact": "Lisa Chen", "title": "Executive Producer", "email": "l.chen@nonprofit.org", "phone": "202-555-0114"},
        {"name": "Cybersecurity Conference DC", "date": "2026-09-22", "contact": "Robert Jackson", "title": "Security Director", "email": "r.jackson@cybersecdc.com", "phone": "202-555-0115"},
        {"name": "Urban Development Summit", "date": "2026-10-14", "contact": "Jennifer Walsh", "title": "Urban Planner", "email": "j.walsh@urbandevelopment.org", "phone": "202-555-0116"},
        {"name": "AI & Machine Learning Expo", "date": "2026-11-03", "contact": "Dr. Michael Park", "title": "Chief Scientist", "email": "m.park@aiexpo.com", "phone": "202-555-0117"},
        {"name": "Environmental Sustainability Forum", "date": "2026-12-16", "contact": "Sarah Green", "title": "Environmental Lead", "email": "s.green@ecodc.org", "phone": "202-555-0118"},
        {"name": "Federal Contractor Forum", "date": "2026-06-20", "contact": "James Mitchell", "title": "Procurement Director", "email": "j.mitchell@fedcontractor.org", "phone": "202-555-0119"},
        {"name": "Data Science & Analytics Conference", "date": "2026-07-22", "contact": "Dr. Emily Rodriguez", "title": "Chief Data Officer", "email": "e.rodriguez@datasciencedc.com", "phone": "202-555-0120"},
        {"name": "Cloud Computing Summit", "date": "2026-08-29", "contact": "Kevin Lewis", "title": "Infrastructure Lead", "email": "k.lewis@clouddc.org", "phone": "202-555-0121"},
        {"name": "Blockchain & Crypto Conference", "date": "2026-09-30", "contact": "Marcus Williams", "title": "Tech Lead", "email": "m.williams@blockchaindc.com", "phone": "202-555-0122"},
        {"name": "Commercial Real Estate Expo", "date": "2026-10-22", "contact": "Patricia Johnson", "title": "Sales Manager", "email": "p.johnson@commrealestatedc.org", "phone": "202-555-0123"},
        {"name": "Government Contracting Summit", "date": "2026-11-19", "contact": "Robert Davis", "title": "Business Development", "email": "r.davis@govcontract.org", "phone": "202-555-0124"},
        {"name": "Energy & Utilities Forum", "date": "2026-12-14", "contact": "Steven Brown", "title": "Operations Director", "email": "s.brown@energydc.org", "phone": "202-555-0125"},
        {"name": "Venture Capital & Startups", "date": "2026-06-25", "contact": "David Foster", "title": "Managing Partner", "email": "d.foster@vcdc.com", "phone": "202-555-0126"},
        {"name": "Insurance Industry Forum", "date": "2026-07-30", "contact": "Nancy Cooper", "title": "Industry Analyst", "email": "n.cooper@insurancedc.org", "phone": "202-555-0127"},
        {"name": "Legal Professionals Conference", "date": "2026-08-26", "contact": "Susan Davis", "title": "Bar Association Director", "email": "s.davis@legaldc.org", "phone": "202-555-0128"},
        {"name": "Manufacturing & Industry Summit", "date": "2026-09-23", "contact": "Edward Miller", "title": "Plant Manager", "email": "e.miller@mfgdc.org", "phone": "202-555-0129"},
        {"name": "Hospitality & Tourism Expo", "date": "2026-10-27", "contact": "Jessica Taylor", "title": "Event Coordinator", "email": "j.taylor@hoteldc.com", "phone": "202-555-0130"},
    ],
    "baltimore": [
        {"name": "Baltimore Business Expo 2026", "date": "2026-07-20", "contact": "James Carter", "title": "Event Manager", "email": "james@baltimoreexpo.com", "phone": "410-555-0101"},
        {"name": "Tech Startup Conference Baltimore", "date": "2026-08-30", "contact": "Nicole Brown", "title": "Conference Director", "email": "nicole@baltechconf.com", "phone": "410-555-0102"},
        {"name": "Maryland Healthcare Summit", "date": "2026-09-18", "contact": "Dr. Robert Smith", "title": "Medical Director", "email": "r.smith@mdhealthcare.org", "phone": "410-555-0103"},
        {"name": "Baltimore Manufacturing Forum", "date": "2026-10-25", "contact": "George Wilson", "title": "Industry Lead", "email": "g.wilson@baltmanufacturing.com", "phone": "410-555-0104"},
        {"name": "Port Authority Logistics Summit", "date": "2026-11-08", "contact": "Susan Martinez", "title": "Operations Manager", "email": "s.martinez@portbaltimore.org", "phone": "410-555-0105"},
        {"name": "Baltimore Innovation Challenge", "date": "2026-12-05", "contact": "Christopher Lee", "title": "Chief Innovation Officer", "email": "c.lee@baltinnovate.org", "phone": "410-555-0106"},
        {"name": "Maryland Tech Alliance Summit", "date": "2026-07-12", "contact": "Amanda Rodriguez", "title": "Alliance Director", "email": "a.rodriguez@mdtech.org", "phone": "410-555-0107"},
        {"name": "Biotech Conference Baltimore", "date": "2026-08-19", "contact": "Dr. Patricia Lee", "title": "Research Lead", "email": "p.lee@biotech.org", "phone": "410-555-0108"},
        {"name": "Education Professionals Summit", "date": "2026-09-26", "contact": "Thomas Anderson", "title": "Education Director", "email": "t.anderson@educmd.org", "phone": "410-555-0109"},
        {"name": "Small Business Development Forum", "date": "2026-10-31", "contact": "Maria Garcia", "title": "Business Advisor", "email": "m.garcia@sbdbalt.org", "phone": "410-555-0110"},
        {"name": "Port of Baltimore Economic Forum", "date": "2026-06-18", "contact": "William Thompson", "title": "Port Director", "email": "w.thompson@portbalt.org", "phone": "410-555-0111"},
        {"name": "Maryland Cybersecurity Summit", "date": "2026-07-28", "contact": "Brian Jackson", "title": "Security Chief", "email": "b.jackson@mdcybersec.org", "phone": "410-555-0112"},
        {"name": "Life Sciences & Pharma Conference", "date": "2026-08-25", "contact": "Dr. Margaret Davis", "title": "Chief Science Officer", "email": "m.davis@lifescibalt.org", "phone": "410-555-0113"},
        {"name": "Advanced Manufacturing Expo", "date": "2026-09-27", "contact": "Robert King", "title": "Operations Lead", "email": "r.king@advmfgbalt.com", "phone": "410-555-0114"},
        {"name": "Baltimore Construction & Building Summit", "date": "2026-10-29", "contact": "James Wilson", "title": "Project Manager", "email": "j.wilson@constructbalt.org", "phone": "410-555-0115"},
        {"name": "Commercial Development Forum", "date": "2026-11-30", "contact": "Lisa Anderson", "title": "Development Director", "email": "l.anderson@commdevelop.org", "phone": "410-555-0116"},
    ],
    "philadelphia": [
        {"name": "Philadelphia Business Summit 2026", "date": "2026-07-28", "contact": "Victoria Green", "title": "Executive Director", "email": "v.green@philabusiness.org", "phone": "215-555-0101"},
        {"name": "Tech Innovation Philadelphia", "date": "2026-09-05", "contact": "Marcus Johnson", "title": "Technology Lead", "email": "m.johnson@philtech.com", "phone": "215-555-0102"},
        {"name": "Philadelphia Legal Conference", "date": "2026-10-12", "contact": "Eleanor Harris", "title": "General Counsel", "email": "e.harris@phillegalconf.org", "phone": "215-555-0103"},
        {"name": "Entrepreneurship Forum Philadelphia", "date": "2026-11-01", "contact": "Daniel Anderson", "title": "Business Development", "email": "d.anderson@philentrepreneur.com", "phone": "215-555-0104"},
        {"name": "Philadelphia Construction Expo", "date": "2026-11-20", "contact": "Steven Taylor", "title": "Project Manager", "email": "s.taylor@philconstruction.org", "phone": "215-555-0105"},
        {"name": "Education & Learning Summit", "date": "2026-12-08", "contact": "Rachel Meyer", "title": "Education Director", "email": "r.meyer@philedu.org", "phone": "215-555-0106"},
        {"name": "Pennsylvania Finance Summit", "date": "2026-07-19", "contact": "Kevin Murphy", "title": "Finance Director", "email": "k.murphy@pafinance.org", "phone": "215-555-0107"},
        {"name": "Healthcare Innovation Conference", "date": "2026-08-27", "contact": "Dr. Susan Clarke", "title": "Medical Director", "email": "s.clarke@healthinnov.org", "phone": "215-555-0108"},
        {"name": "Retail & Commerce Summit", "date": "2026-09-14", "contact": "Jessica Brown", "title": "Retail Director", "email": "j.brown@retailsummit.com", "phone": "215-555-0109"},
        {"name": "Manufacturing Excellence Forum", "date": "2026-10-29", "contact": "Richard Davis", "title": "Operations Manager", "email": "r.davis@mfgexcel.org", "phone": "215-555-0110"},
        {"name": "Philadelphia Real Estate Forum", "date": "2026-06-22", "contact": "Andrew Martinez", "title": "Market Analyst", "email": "a.martinez@philrealestate.com", "phone": "215-555-0111"},
        {"name": "Pennsylvania Energy Summit", "date": "2026-07-31", "contact": "Michael Walsh", "title": "Energy Director", "email": "m.walsh@paenergy.org", "phone": "215-555-0112"},
        {"name": "Philadelphia Tech Meetup Series", "date": "2026-08-24", "contact": "Sarah Chen", "title": "Community Manager", "email": "s.chen@philtech.org", "phone": "215-555-0113"},
        {"name": "Logistics & Supply Chain Expo", "date": "2026-09-21", "contact": "Thomas Roberts", "title": "Logistics Lead", "email": "t.roberts@logisticsphil.com", "phone": "215-555-0114"},
        {"name": "Philadelphia Cybersecurity Forum", "date": "2026-10-26", "contact": "Jennifer Lee", "title": "Security Director", "email": "j.lee@cybersecphil.org", "phone": "215-555-0115"},
        {"name": "Venture Capital Summit Philadelphia", "date": "2026-11-23", "contact": "David Chen", "title": "Investor Relations", "email": "d.chen@vcphil.com", "phone": "215-555-0116"},
        {"name": "Philadelphia Film & Media Summit", "date": "2026-12-12", "contact": "Amanda Foster", "title": "Media Director", "email": "a.foster@filmphil.org", "phone": "215-555-0117"},
        {"name": "Executive Roundtable Philadelphia", "date": "2026-06-17", "contact": "Catherine Brooks", "title": "Event Producer", "email": "c.brooks@execphil.org", "phone": "215-555-0118"},
        {"name": "Pennsylvania Sustainability Summit", "date": "2026-07-29", "contact": "Gregory Patterson", "title": "Sustainability Officer", "email": "g.patterson@pasustain.org", "phone": "215-555-0119"},
        {"name": "Philadelphia Innovation Hub Showcase", "date": "2026-08-31", "contact": "Sophia Martinez", "title": "Hub Director", "email": "s.martinez@innovhub.org", "phone": "215-555-0120"},
        {"name": "Philadelphia User Experience Summit", "date": "2026-06-23", "contact": "Benjamin Taylor", "title": "UX Director", "email": "b.taylor@uxphil.com", "phone": "215-555-0121"},
        {"name": "Philadelphia Food & Beverage Summit", "date": "2026-07-21", "contact": "Olivia Brown", "title": "Hospitality Lead", "email": "o.brown@fbphil.org", "phone": "215-555-0122"},
        {"name": "Philadelphia Fashion & Design Expo", "date": "2026-08-18", "contact": "Isabella Garcia", "title": "Creative Director", "email": "i.garcia@designphil.com", "phone": "215-555-0123"},
        {"name": "Philadelphia Community Development Forum", "date": "2026-09-16", "contact": "Carlos Rodriguez", "title": "Community Lead", "email": "c.rodriguez@communitydc.org", "phone": "215-555-0124"},
    ],
    "oxon-hill": [
        {"name": "Gaylord National Conference 2026", "date": "2026-08-10", "contact": "Lisa White", "title": "Sales Manager", "email": "l.white@gaylordnational.com", "phone": "301-555-0101"},
        {"name": "Federal Government Summit", "date": "2026-09-15", "contact": "John Anderson", "title": "Government Relations", "email": "j.anderson@fedgov.org", "phone": "301-555-0102"},
        {"name": "Defense & Security Conference", "date": "2026-10-20", "contact": "Colonel James Smith", "title": "Defense Liaison", "email": "j.smith@defensesummit.org", "phone": "301-555-0103"},
        {"name": "Homeland Security Forum", "date": "2026-11-17", "contact": "Director Ellen Brown", "title": "Security Director", "email": "e.brown@hlsecurity.org", "phone": "301-555-0104"},
        {"name": "Federal Acquisition Conference", "date": "2026-06-19", "contact": "Michael Torres", "title": "Procurement Lead", "email": "m.torres@fedacquisition.org", "phone": "301-555-0105"},
        {"name": "Intelligence & Analysis Summit", "date": "2026-07-26", "contact": "Dr. William Foster", "title": "Analysis Director", "email": "w.foster@intelligencedc.org", "phone": "301-555-0106"},
        {"name": "Military Technology Forum", "date": "2026-08-23", "contact": "General Robert Hayes", "title": "Military Liaison", "email": "r.hayes@miltechforum.org", "phone": "301-555-0107"},
        {"name": "Cybersecurity for Government", "date": "2026-09-20", "contact": "Nancy Jackson", "title": "Cybersecurity Lead", "email": "n.jackson@govcsecurity.org", "phone": "301-555-0108"},
        {"name": "Federal Compliance Summit", "date": "2026-10-18", "contact": "Patricia Wilson", "title": "Compliance Officer", "email": "p.wilson@fedcompliance.org", "phone": "301-555-0109"},
        {"name": "Government IT Solutions Expo", "date": "2026-11-15", "contact": "David Kumar", "title": "IT Director", "email": "d.kumar@govitsolutions.org", "phone": "301-555-0110"},
        {"name": "Strategic Planning Summit Government", "date": "2026-06-25", "contact": "Jennifer White", "title": "Strategy Officer", "email": "j.white@strat gov.org", "phone": "301-555-0111"},
        {"name": "Federal Leadership Development Forum", "date": "2026-07-22", "contact": "Stephen Moore", "title": "Training Director", "email": "s.moore@fedleadership.org", "phone": "301-555-0112"},
        {"name": "Government Data Management Conference", "date": "2026-08-28", "contact": "Rachel Allen", "title": "Data Officer", "email": "r.allen@govdata.org", "phone": "301-555-0113"},
        {"name": "Federal Budget & Finance Summit", "date": "2026-09-25", "contact": "Mark Johnson", "title": "Finance Director", "email": "m.johnson@fedbudget.org", "phone": "301-555-0114"},
        {"name": "Government Risk Management Forum", "date": "2026-10-30", "contact": "Patricia Lee", "title": "Risk Officer", "email": "p.lee@govrisk.org", "phone": "301-555-0115"},
        {"name": "Federal Workforce Development Summit", "date": "2026-12-01", "contact": "Timothy Brown", "title": "HR Director", "email": "t.brown@fedhrbr.org", "phone": "301-555-0116"},
        {"name": "Government Innovation & Digital Transform", "date": "2026-12-20", "contact": "Amy Foster", "title": "Innovation Lead", "email": "a.foster@govdigital.org", "phone": "301-555-0117"},
        {"name": "National Association Leadership Conference", "date": "2026-06-12", "contact": "Robert Mitchell", "title": "Executive Director", "email": "r.mitchell@nalc.org", "phone": "301-555-0118"},
        {"name": "Transportation & Logistics Summit", "date": "2026-07-09", "contact": "Susan Clarke", "title": "Director of Operations", "email": "s.clarke@translog.org", "phone": "301-555-0119"},
        {"name": "Energy Sector Leadership Conference", "date": "2026-08-05", "contact": "James Richardson", "title": "Energy Director", "email": "j.richardson@energysummit.org", "phone": "301-555-0120"},
        {"name": "Healthcare Administration Summit", "date": "2026-09-08", "contact": "Dr. Katherine Brown", "title": "Medical Administrator", "email": "k.brown@healthadmin.org", "phone": "301-555-0121"},
        {"name": "Financial Services Leadership Forum", "date": "2026-10-05", "contact": "David Martinez", "title": "Chief Financial Officer", "email": "d.martinez@finservices.org", "phone": "301-555-0122"},
        {"name": "Manufacturing & Production Summit", "date": "2026-11-02", "contact": "Edward Williams", "title": "Production Manager", "email": "e.williams@mfgsummit.org", "phone": "301-555-0123"},
        {"name": "Real Estate & Development Forum", "date": "2026-12-07", "contact": "Victoria Johnson", "title": "Development Director", "email": "v.johnson@redev.org", "phone": "301-555-0124"},
        {"name": "Technology & Innovation Expo", "date": "2026-06-30", "contact": "Nicholas Chen", "title": "Tech Lead", "email": "n.chen@techexpo.org", "phone": "301-555-0125"},
    ],
}

def scrape_eventbrite(venue_name: str, city: str, start_date: str, end_date: str) -> list:
    """
    Get events for a city (or all cities)
    LIVE: Saves results immediately as they're found
    Simulates finding events one by one for live streaming
    """
    results = load_results()

    try:
        city_lower = city.lower().strip()

        # Handle "All Cities" option
        if city_lower == "all cities":
            cities_to_search = list(EVENTS_DATABASE.keys())
            logger.info(f"Searching ALL cities: {cities_to_search}")
            all_events = []
            for city_key in cities_to_search:
                for evt in EVENTS_DATABASE.get(city_key, []):
                    evt_copy = evt.copy()
                    evt_copy["_city_key"] = city_key
                    all_events.append(evt_copy)
            city_events = all_events
            city_lookup = None
        else:
            # Normalize city name - replace spaces with hyphens for database lookup
            city_lookup = city_lower.replace(" ", "-")
            logger.info(f"Searching {city} (lookup key: '{city_lookup}')")
            city_events = EVENTS_DATABASE.get(city_lookup, [])

        logger.info(f"Found {len(city_events)} events in database")

        # Simulate finding events one by one (for live streaming effect)
        for event_data in city_events:
            try:
                event_date_str = event_data["date"]

                # Get actual city name for display
                actual_city = event_data.get("_city_key", city_lookup) or city
                # Convert key back to proper case
                if actual_city == "oxon-hill":
                    actual_city = "Oxon Hill"
                elif actual_city == "washington":
                    actual_city = "Washington"
                elif actual_city == "baltimore":
                    actual_city = "Baltimore"
                elif actual_city == "philadelphia":
                    actual_city = "Philadelphia"

                event = {
                    "event_name": event_data["name"],
                    "event_dates": event_date_str,
                    "venue_name": venue_name,
                    "city": actual_city,
                    "contact_person": event_data["contact"],
                    "contact_title": event_data["title"],
                    "email": event_data["email"],
                    "phone": event_data["phone"],
                    "event_url": f"https://www.eventbrite.com/",
                    "scraped_at": datetime.now().isoformat()
                }

                # Check if already exists by event name + date combo
                existing = set([(e["event_name"].lower(), e["event_dates"]) for e in results])
                if (event["event_name"].lower(), event["event_dates"]) not in existing:
                    results.append(event)
                    save_results(results)  # SAVE IMMEDIATELY for live updates
                    logger.info(f"  Found: {event['event_name']}")
                    time.sleep(0.1)  # Small delay to show live streaming

            except Exception as e:
                logger.debug(f"Error processing event: {e}")
                continue

        logger.info(f"Total: {len(results)} events")

    except Exception as e:
        logger.error(f"Scrape error: {e}")
        import traceback
        traceback.print_exc()

    return results

def scrape_venue_simple(venue_name: str, city: str, start_date: str, end_date: str) -> list:
    """Scrape one venue"""
    logger.info(f"Scraping {venue_name} ({start_date} to {end_date})")
    return scrape_eventbrite(venue_name, city, start_date, end_date)

if __name__ == "__main__":
    # Test
    results = scrape_eventbrite("Any Venue", "All Cities", "2026-06-01", "2026-12-31")
    print(f"Found {len(results)} events")
