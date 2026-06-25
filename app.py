"""
EventBot Pro - COMPLETE VERSION
Date picker | Real-time progress | Export visible | Venue management | Working scraper
"""

import streamlit as st
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import subprocess
import threading
import time
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title="EventBot Pro", layout="wide", initial_sidebar_state="collapsed")

# ═══════════════════════════════════════════════════════════════════════════════
# THEME
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
body { background: #f5f5f5; font-family: 'Segoe UI', sans-serif; }
.main { background: #ffffff; }
h1 { color: #1a1a1a; }

.stat-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; padding: 25px; border-radius: 10px; text-align: center;
}
.stat-num { font-size: 2.2rem; font-weight: bold; }
.stat-label { font-size: 0.85rem; opacity: 0.9; }

.status-running { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 5px; }
.status-done { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 5px; }

.stButton > button { background: linear-gradient(135deg, #667eea, #764ba2); color: white; width: 100%; }

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; margin-top: 15rem;'>🔒 EventBot Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if pwd == "workrbee2026":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Wrong password")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "data", "current_results.json")
VENUES_FILE = os.path.join(os.path.dirname(__file__), "data", "custom_venues.json")

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return []

def save_results(results):
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

def load_custom_venues():
    if os.path.exists(VENUES_FILE):
        with open(VENUES_FILE) as f:
            return json.load(f)
    return []

def save_custom_venues(venues):
    os.makedirs(os.path.dirname(VENUES_FILE), exist_ok=True)
    with open(VENUES_FILE, "w") as f:
        json.dump(venues, f, indent=2)

def add_venue(name, city):
    venues = load_custom_venues()
    if {"name": name, "city": city} not in venues:
        venues.append({"name": name, "city": city})
        save_custom_venues(venues)
        return True
    return False

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("# 🤖 EventBot Pro")
st.markdown("**Conference & Event Discovery**")
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────────────────────

# Initialize session state for fresh start
if "results_shown" not in st.session_state:
    st.session_state.results_shown = False
    # Delete old results file on first load
    try:
        os.remove(RESULTS_FILE)
    except:
        pass

# Show metrics - display 0 until search starts
try:
    if st.session_state.results_shown:
        results = load_results()
    else:
        results = []
except:
    results = []

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num">{len(results)}</div>
        <div class="stat-label">Events Found</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    with_contact = len([r for r in results if r.get("contact_person")])
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num">{with_contact}</div>
        <div class="stat-label">With Contacts</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    with_email = len([r for r in results if r.get("email")])
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num">{with_email}</div>
        <div class="stat-label">With Emails</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    venues = len(set([r.get("venue_name", "") for r in results if r.get("venue_name")]))
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num">{venues}</div>
        <div class="stat-label">Venues</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab_search, tab_results, tab_manage = st.tabs(["🔍 Search", "📊 Results", "⚙️ Manage"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: SEARCH
# ─────────────────────────────────────────────────────────────────────────────

with tab_search:
    st.markdown("## 🔍 Search Events")

    col_settings, col_info = st.columns([1, 2])

    with col_settings:
        st.markdown("### Settings")

        # Venue selection - MULTI-SELECT from all 80+ venues
        from scraper import VENUES_DATABASE
        all_venues = []
        for city_venues in VENUES_DATABASE.values():
            all_venues.extend(city_venues.keys())
        all_venues += [v["name"] for v in load_custom_venues()]
        all_venues = sorted(list(set(all_venues)))

        # Multi-select venues
        st.markdown("**Select Venues (Check multiple to search together)**")
        selected_venues = st.multiselect("Venues", all_venues, default=[all_venues[0]] if all_venues else [], key="search_venue_key")

        # City selection
        cities = ["Washington", "Baltimore", "Philadelphia", "Oxon Hill", "All Cities"]
        selected_city = st.selectbox("City", cities, key="search_city_key")

        st.markdown("**Date Range**")

        # Start date
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("From", value=datetime(2026, 6, 1))

        with col_d2:
            end_date = st.date_input("To", value=datetime(2026, 12, 31))

        st.markdown("---")

        # Search controls
        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("▶️ START SEARCH", use_container_width=True):
                if not selected_venues:
                    st.error("Please select at least one venue!")
                else:
                    save_results([])  # FRESH START - clear old results
                    st.session_state.results_shown = True  # Now show metrics
                    st.session_state.searching = True
                    st.session_state.search_venues = selected_venues
                    st.rerun()

        with col_btn2:
            if st.session_state.get("searching", False):
                if st.button("⏹ STOP SEARCH", use_container_width=True):
                    st.session_state.searching = False
                    st.success("✅ Search stopped! All results saved.")
                    st.rerun()

    with col_info:
        st.markdown("### ℹ️ How It Works")
        st.info("""
        1️⃣ Select venue and dates
        2️⃣ Click START SEARCH
        3️⃣ Results appear LIVE
        4️⃣ Go to Results tab
        5️⃣ Download Excel

        ⏱️ Takes 2-5 min per venue

        **Results show as bot finds them!**
        """)

    # Status message
    if st.session_state.get("searching", False):
        st.markdown("""
        <div class="status-running">
        <strong>⏳ Searching...</strong><br>
        Results appear below as they are discovered.
        </div>
        """, unsafe_allow_html=True)

        # Run search in background - MULTIPLE VENUES
        def run_search_live():
            try:
                from scraper import scrape_eventbrite

                venues_to_search = st.session_state.get("search_venues", [])
                # Map venue name to city (from VENUES_DATABASE)
                from scraper import VENUES_DATABASE

                for venue in venues_to_search:
                    if not st.session_state.get("searching", False):
                        break  # Stop if user clicked STOP

                    # Find city for this venue
                    venue_city = selected_city
                    for city_key, city_venues in VENUES_DATABASE.items():
                        if venue in city_venues:
                            venue_city = city_key.replace("-", " ").title()
                            break

                    logger.info(f"Searching {venue} in {venue_city}...")

                    # Scrape this venue (generates 30+ events)
                    scrape_eventbrite(venue, venue_city,
                                     start_date.strftime("%Y-%m-%d"),
                                     end_date.strftime("%Y-%m-%d"))

                st.session_state.searching = False

            except Exception as e:
                st.session_state.search_error = str(e)
                st.session_state.searching = False

        # Start search thread if not already running
        if "search_thread" not in st.session_state or not st.session_state.search_thread.is_alive():
            thread = threading.Thread(target=run_search_live, daemon=True)
            thread.start()
            st.session_state.search_thread = thread

        # Show live results - load from file
        current_results = load_results()

        if current_results:
            st.markdown(f"**✅ Found {len(current_results)} events so far**")

            df_live = []
            for r in current_results[-10:]:  # Show last 10
                df_live.append({
                    "Event": r.get("event_name", "")[:50],
                    "Date": r.get("event_dates", ""),
                    "Venue": r.get("venue_name", "")
                })

            if df_live:
                st.dataframe(df_live, use_container_width=True, height=300)
        else:
            st.info("Waiting for first results... (may take 30 seconds)")

        # Auto-refresh UI every 200ms while searching (FAST updates)
        if st.session_state.get("searching", False):
            time.sleep(0.2)
            st.rerun()
        else:
            st.success("✅ Search complete! View all results in the Results tab.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: RESULTS
# ─────────────────────────────────────────────────────────────────────────────

with tab_results:
    st.markdown("## 📊 Results")

    try:
        if st.session_state.get("results_shown", False):
            results = load_results()
        else:
            results = []
    except:
        results = []

    if results:
        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            search_text = st.text_input("🔍 Search", placeholder="Event name...")

        with col_f2:
            cities = list(set([r.get("city", "") for r in results if r.get("city")]))
            selected_city_filter = st.multiselect("Cities", cities, default=cities, key="results_cities_key")

        with col_f3:
            has_contact = st.checkbox("Has contact", key="results_contact_key")
            has_email = st.checkbox("Has email", key="results_email_key")

        # Filter results
        filtered = results

        if search_text:
            filtered = [r for r in filtered if search_text.lower() in str(r).lower()]

        if selected_city_filter:
            filtered = [r for r in filtered if r.get("city", "") in selected_city_filter]

        if has_contact:
            filtered = [r for r in filtered if r.get("contact_person")]

        if has_email:
            filtered = [r for r in filtered if r.get("email")]

        # Display table
        st.markdown(f"**{len(filtered)} of {len(results)} events**")

        if filtered:
            df_data = [{
                "Date": r.get("event_dates", ""),
                "Event": r.get("event_name", "")[:70],
                "Venue": r.get("venue_name", ""),
                "City": r.get("city", ""),
                "Contact": r.get("contact_person", ""),
                "Title": r.get("contact_title", ""),
                "Email": r.get("email", ""),
                "Phone": r.get("phone", ""),
            } for r in filtered]

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, height=400)

            st.markdown("---")

            # EXPORT SECTION
            st.markdown("### 📥 Export")

            col_exp1, col_exp2 = st.columns(2)

            # Excel export
            with col_exp1:
                try:
                    from openpyxl import Workbook
                    from openpyxl.styles import Font, PatternFill

                    wb = Workbook()
                    ws = wb.active
                    ws.title = "Events"

                    headers = ["Date", "Event", "Venue", "City", "Contact", "Title", "Email", "Phone"]
                    ws.append(headers)

                    for cell in ws[1]:
                        cell.fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
                        cell.font = Font(color="FFFFFF", bold=True)

                    for r in filtered:
                        ws.append([
                            r.get("event_dates", ""),
                            r.get("event_name", ""),
                            r.get("venue_name", ""),
                            r.get("city", ""),
                            r.get("contact_person", ""),
                            r.get("contact_title", ""),
                            r.get("email", ""),
                            r.get("phone", ""),
                        ])

                    filename = f"EventBot_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    wb.save(filename)

                    with open(filename, "rb") as f:
                        st.download_button("📥 Download Excel", f, filename)

                    os.remove(filename)

                except Exception as e:
                    st.warning(f"Excel: {e}")

            # CSV export
            with col_exp2:
                import csv
                from io import StringIO

                csv_buffer = StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(headers)
                for r in filtered:
                    writer.writerow([r.get(h.lower(), "") for h in headers])

                st.download_button("📥 Download CSV", csv_buffer.getvalue(), f"EventBot_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")

        else:
            st.info("No results match filters")

    else:
        if st.session_state.get("results_shown", False):
            st.info("🔄 Search in progress... Results will appear here shortly")
        else:
            st.info("👉 Go to Search tab, select venues, and click START SEARCH")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: MANAGE VENUES
# ─────────────────────────────────────────────────────────────────────────────

with tab_manage:
    st.markdown("## ⚙️ Manage Venues")

    st.markdown("### ➕ Add Custom Venue")

    col_v1, col_v2 = st.columns([2, 1])

    with col_v1:
        venue_name = st.text_input("Venue Name", placeholder="e.g., Marriott Downtown")

    with col_v2:
        venue_city = st.selectbox("City", ["Washington", "Baltimore", "Philadelphia", "Oxon Hill", "Bethesda"], key="manage_city_key")

    if st.button("✅ Add Venue", use_container_width=True):
        if venue_name:
            if add_venue(venue_name, venue_city):
                st.success(f"✅ Added: {venue_name}")
            else:
                st.warning("Already exists")
        else:
            st.error("Enter venue name")

    st.markdown("---")

    st.markdown("### 📋 Current Venues")

    custom = load_custom_venues()
    default = ["DC Convention Center (Washington)", "Marriott Marquis (Washington)", "Gaylord National Harbor (Oxon Hill)"]

    st.markdown("**Default Venues:**")
    for v in default:
        st.write(f"• {v}")

    if custom:
        st.markdown("**Custom Venues:**")
        for v in custom:
            st.write(f"• {v['name']} ({v['city']})")
    else:
        st.write("*No custom venues yet*")

st.divider()
st.caption(f"EventBot Pro v6 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
