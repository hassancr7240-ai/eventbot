"""
EventBot Pro v3 - Complete Smooth Experience
Auto-save venues | Live tracker | Quick export | Daily schedule
"""

import streamlit as st
import os
import json
import subprocess
import threading
import time
from datetime import datetime
from deduplicator import get_stats, load_db, update_record
from venues import VENUES
import csv
from io import StringIO

st.set_page_config(page_title="EventBot Pro", layout="wide", initial_sidebar_state="collapsed")

# ── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
* { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.main { background: #f8f9fa; }
.metric-card {
    background: white; padding: 20px; border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center;
    border-top: 4px solid #667eea;
}
.metric-num { font-size: 36px; font-weight: bold; color: #667eea; }
.metric-lbl { font-size: 13px; color: #999; margin-top: 8px; text-transform: uppercase; letter-spacing: 1px; }
.success-box { background: #d4edda; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }
.warning-box { background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; }
.info-box { background: #d1ecf1; padding: 15px; border-radius: 8px; border-left: 4px solid #17a2b8; }
.event-row { padding: 12px; border-bottom: 1px solid #eee; hover: background #f5f5f5; }
.event-row:hover { background: #f5f5f5; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

# ── PASSWORD ───────────────────────────────────────────────────────────────────
PASSWORD = "workrbee2026"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("# 🔒 EventBot Pro")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pwd = st.text_input("Enter Password", type="password", placeholder="Password...")
            if st.button("Login", use_container_width=True):
                if pwd == PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        return False
    return True

if not check_password():
    st.stop()

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "bot_running" not in st.session_state:
    st.session_state.bot_running = False
if "bot_progress" not in st.session_state:
    st.session_state.bot_progress = ""
if "selected_venue" not in st.session_state:
    st.session_state.selected_venue = "All"

# ── HELPER: Load venues from venues.py ─────────────────────────────────────────
def get_venue_list():
    """Get list of all venue names"""
    return sorted(list(set([v.get("name", "") for v in VENUES])))

# ── HELPER: Add venue to venues.py ─────────────────────────────────────────────
def add_venue_to_file(name: str, address: str, city: str, state: str) -> bool:
    """Add venue directly to venues.py file"""
    try:
        venues_file = os.path.join(os.path.dirname(__file__), "venues.py")

        # Read current venues.py
        with open(venues_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the VENUES list and add before the closing bracket
        new_entry = f'''    {{
        "city_group": "{city} {state}",
        "name": "{name}",
        "address": "{address}",
        "city": "{city}",
        "state": "{state}",
        "search_name": "{name} {city} events",
        "source_urls": [],
    }},
'''

        # Insert before the last ] of VENUES
        insert_pos = content.rfind("]")
        if insert_pos > 0:
            new_content = content[:insert_pos] + new_entry + content[insert_pos:]
            with open(venues_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"Error adding venue: {e}")
    return False

# ── HELPER: Export to CSV and upload to Google Sheets ─────────────────────────
def export_to_csv():
    """Generate CSV from database"""
    db = load_db()
    all_events = []

    for venue, events in db.items():
        for event in events:
            all_events.append({
                "Venue": event.get("venue_name", ""),
                "City": event.get("city", ""),
                "State": event.get("state", ""),
                "Event Name": event.get("event_name", ""),
                "Dates": event.get("event_dates", ""),
                "Contact": event.get("contact_person", ""),
                "Title": event.get("contact_title", ""),
                "Email": event.get("email", ""),
                "Phone": event.get("phone", ""),
                "Status": event.get("status", "New"),
                "Updated": event.get("last_updated", ""),
            })

    if not all_events:
        return None

    # Create CSV string
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=all_events[0].keys())
    writer.writeheader()
    writer.writerows(all_events)
    return output.getvalue()

def upload_to_google_sheets_simple():
    """Upload via simple method - for now just return CSV"""
    csv_data = export_to_csv()
    if csv_data:
        return csv_data
    return None

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("# 🤖 EventBot Pro")
st.markdown("Automated event discovery across DC, Baltimore, Philadelphia & more")

# Show schedule
schedule_info = """
**📅 Daily Schedule:** Runs at 6:00 AM every morning
**⏱️ Search Time:** 15-20 minutes (all 62 venues)
**📊 Last Run:** Check Live Tracker below
"""
st.markdown(schedule_info)
st.markdown("---")

# ── TOP METRICS ────────────────────────────────────────────────────────────────
s = get_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-num">{s["total_events"]}</div><div class="metric-lbl">Events Found</div></div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-num">{s["total_contacts"]}</div><div class="metric-lbl">Contacts</div></div>', unsafe_allow_html=True)

with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-num">{s["total_emailed"]}</div><div class="metric-lbl">Emailed</div></div>', unsafe_allow_html=True)

with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-num">{len(VENUES)}</div><div class="metric-lbl">Venues</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ── TABS ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Run Bot", "📋 Live Tracker", "➕ Add Venues", "📥 Export & Upload"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: RUN BOT
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 🚀 Start Bot Search")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **What happens when you click START:**
        - Searches all 62 venues for 2026 events
        - Validates events with AI
        - Removes duplicates
        - Saves results to Live Tracker
        - Takes 15-20 minutes

        **You can:**
        - Watch Live Tracker for real-time results
        - Download results anytime
        - Export to Google Sheets
        """)

    with col2:
        if st.button("▶️ START BOT", use_container_width=True, key="run_bot_btn", help="Searches all venues"):
            st.session_state.bot_running = True
            st.rerun()

    if st.session_state.bot_running:
        st.markdown("<div class='warning-box'><strong>⏳ Bot is searching...</strong><br>Check Live Tracker for real-time results. This takes 15-20 minutes.</div>", unsafe_allow_html=True)

        progress_placeholder = st.empty()

        def run_bot_background():
            try:
                result = subprocess.run(
                    ["python", "scheduler.py", "--run-now", "--years", "2026", "2026"],
                    cwd=os.path.dirname(__file__),
                    capture_output=True,
                    text=True,
                    timeout=3600
                )
                st.session_state.bot_progress = "✅ Bot completed!"
                st.session_state.bot_running = False
            except Exception as e:
                st.session_state.bot_progress = f"❌ Error: {str(e)}"
                st.session_state.bot_running = False

        thread = threading.Thread(target=run_bot_background, daemon=True)
        thread.start()

        # Auto-refresh every 3 seconds
        time.sleep(3)
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: LIVE TRACKER (with real-time updates)
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 📋 Live Event Tracker")

    db = load_db()
    all_events = []

    for venue, events in db.items():
        for event in events:
            all_events.append({
                "Venue": event.get("venue_name", ""),
                "City": event.get("city", ""),
                "Event": event.get("event_name", ""),
                "Dates": event.get("event_dates", ""),
                "Email": event.get("email", ""),
                "Phone": event.get("phone", ""),
                "Status": event.get("status", "New"),
            })

    if all_events:
        st.markdown(f"**Total: {len(all_events)} events**")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input("🔍 Search event or venue:")
        with col2:
            venues_list = ["All"] + get_venue_list()
            venue_filter = st.selectbox("Filter by venue:", venues_list)
        with col3:
            status_filter = st.selectbox("Filter by status:", ["All", "New", "Emailed", "Booked"])

        # Apply filters
        filtered = all_events

        if search_term:
            filtered = [e for e in filtered if search_term.lower() in e["Event"].lower() or search_term.lower() in e["Venue"].lower()]

        if venue_filter != "All":
            filtered = [e for e in filtered if e["Venue"] == venue_filter]

        if status_filter != "All":
            filtered = [e for e in filtered if e["Status"] == status_filter]

        st.markdown(f"**Showing {len(filtered)} of {len(all_events)} events**")

        # Display as table with click-able rows
        st.dataframe(filtered, use_container_width=True, height=400)

        # Quick stats
        st.markdown("---")
        st.markdown("### Quick Stats")
        stat_col1, stat_col2, stat_col3 = st.columns(3)

        with stat_col1:
            new_count = len([e for e in filtered if e["Status"] == "New"])
            st.metric("New Events", new_count)

        with stat_col2:
            emailed_count = len([e for e in filtered if e["Status"] == "Emailed"])
            st.metric("Emailed", emailed_count)

        with stat_col3:
            venues_count = len(set([e["Venue"] for e in filtered]))
            st.metric("Unique Venues", venues_count)

    else:
        st.info("📭 No events yet. Click 'Run Bot' to start searching!")

    # Auto-refresh
    if st.session_state.bot_running:
        time.sleep(5)
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ADD VENUES (auto-save)
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## ➕ Add New Venue")
    st.markdown("Add venues to search. They'll be included in the next bot run.")

    with st.form("add_venue_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Venue Name *", placeholder="e.g., Marriott Ballroom")
            address = st.text_input("Address *", placeholder="e.g., 123 Main St")

        with col2:
            city = st.text_input("City *", placeholder="e.g., Baltimore")
            state = st.selectbox("State *", ["MD", "DC", "PA", "DE", "VA", "NJ", "NY", "Other"])

        if st.form_submit_button("✅ Add Venue", use_container_width=True):
            if name and address and city and state:
                # Auto-save to venues.py
                if add_venue_to_file(name, address, city, state):
                    st.markdown(f"<div class='success-box'><strong>✅ Venue Added!</strong><br>{name}, {city}, {state}<br>Will be searched on next bot run.</div>", unsafe_allow_html=True)
                else:
                    st.error("Could not add venue. Please try again.")
            else:
                st.error("Please fill all fields marked with *")

    st.markdown("---")
    st.markdown("### Current Venues")

    # Show venues by city
    venues_by_city = {}
    for v in VENUES:
        city_group = v.get("city_group", "Other")
        if city_group not in venues_by_city:
            venues_by_city[city_group] = []
        venues_by_city[city_group].append(v["name"])

    cols = st.columns(3)
    col_idx = 0

    for city, venues_list in sorted(venues_by_city.items()):
        with cols[col_idx % 3]:
            st.markdown(f"**📍 {city}** ({len(venues_list)})")
            for v in sorted(venues_list):
                st.caption(f"• {v}")
            col_idx += 1

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: EXPORT & UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 📥 Export & Upload Results")

    db = load_db()
    total = sum(len(events) for events in db.values())

    if total > 0:
        st.markdown(f"**Ready to export: {total} events**")

        st.markdown("### Step 1: Download CSV")
        csv_data = export_to_csv()
        if csv_data:
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"EventBot_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("### Step 2: Upload to Google Sheets")
        st.markdown("""
        **How to upload:**
        1. Download the CSV above
        2. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA
        3. Click **File > Import > Upload file**
        4. Choose the CSV
        5. Click **Import**

        Done! All events are now in Google Sheets.
        """)

        st.markdown("### Quick Upload Instructions")
        if st.button("📋 Copy Google Sheet Link", use_container_width=True):
            st.code("https://docs.google.com/spreadsheets/d/1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA", language="text")

        st.markdown("---")
        st.markdown("### Export Preview")
        preview = export_to_csv()
        if preview:
            preview_lines = preview.split("\n")[:6]
            st.code("\n".join(preview_lines), language="csv")

    else:
        st.info("No events to export yet. Run the bot first!")

st.markdown("---")
st.markdown("**EventBot Pro v3** | Password: workrbee2026 | Updated 2026-06-24")
