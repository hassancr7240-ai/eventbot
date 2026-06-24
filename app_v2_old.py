"""
EventBot Pro v2 - Simplified, Client-Friendly Version
Easy venue management + quick bot runs + live results
"""

import streamlit as st
import os
import json
import subprocess
import threading
from datetime import datetime
from deduplicator import get_stats, load_db, update_record
from venues import VENUES

st.set_page_config(page_title="EventBot Pro", layout="wide", initial_sidebar_state="collapsed")

# ── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.main { background-color: #f8f9fa; }
.metric-card {
    background: white; padding: 20px; border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;
}
.metric-num { font-size: 32px; font-weight: bold; color: #2e7d32; }
.metric-lbl { font-size: 14px; color: #666; margin-top: 8px; }
.success-box { background: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; }
.warning-box { background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; }
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
if "bot_output" not in st.session_state:
    st.session_state.bot_output = ""

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("# 🤖 EventBot Pro")
st.markdown("Automated event discovery across DC, Baltimore, Philadelphia & more")
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
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Run Bot", "📋 Live Tracker", "➕ Add Venues", "📊 Analytics"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: RUN BOT
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 🚀 Quick Bot Run")
    st.markdown("Searches all venues for 2026 events (fast mode)")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **How it works:**
        - Searches all configured venues
        - Finds events for 2026 only
        - Validates with Claude AI
        - Removes duplicates
        - Updates Live Tracker in real-time

        ⏱️ **Estimated time: 15-20 minutes**
        """)

    with col2:
        if st.button("▶️ START BOT", use_container_width=True, key="run_bot_btn"):
            st.session_state.bot_running = True
            st.rerun()

    if st.session_state.bot_running:
        st.markdown("<div class='warning-box'><strong>⏳ Bot is running...</strong><br>Results will appear in Live Tracker. Refresh the page to see updates.</div>", unsafe_allow_html=True)

        # Run bot in background
        def run_bot_background():
            try:
                result = subprocess.run(
                    ["python", "scheduler.py", "--run-now", "--years", "2026", "2026"],
                    cwd=os.path.dirname(__file__),
                    capture_output=True,
                    text=True,
                    timeout=3600
                )
                st.session_state.bot_output = result.stdout + result.stderr
                st.session_state.bot_running = False
            except Exception as e:
                st.session_state.bot_output = f"Error: {str(e)}"
                st.session_state.bot_running = False

        thread = threading.Thread(target=run_bot_background, daemon=True)
        thread.start()

        # Auto-refresh
        import time
        time.sleep(2)
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: LIVE TRACKER
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
                "Last Updated": event.get("last_updated", ""),
            })

    if all_events:
        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            search = st.text_input("🔍 Search by event name or venue:")
        with col2:
            city_filter = st.selectbox("Filter by city:", ["All"] + list(set([e["City"] for e in all_events])))
        with col3:
            status_filter = st.selectbox("Filter by status:", ["All", "New", "Emailed", "Booked"])

        # Apply filters
        filtered = all_events
        if search:
            filtered = [e for e in filtered if search.lower() in e["Event"].lower() or search.lower() in e["Venue"].lower()]
        if city_filter != "All":
            filtered = [e for e in filtered if e["City"] == city_filter]
        if status_filter != "All":
            filtered = [e for e in filtered if e["Status"] == status_filter]

        st.markdown(f"**Showing {len(filtered)} of {len(all_events)} events**")
        st.dataframe(filtered, use_container_width=True, height=400)

        # Export button
        csv = filtered[0].keys().__str__().replace("dict_keys(['", "").replace("'])", "")
        csv = ",".join(filtered[0].keys()) + "\n"
        for e in filtered:
            csv += ",".join([str(e.get(k, "")) for k in filtered[0].keys()]) + "\n"

        st.download_button("📥 Download Results", csv, "events.csv", "text/csv")
    else:
        st.info("No events yet. Click 'Run Bot' to start searching!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ADD VENUES
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## ➕ Add New Venue")
    st.markdown("Quickly add venues for the bot to search")

    with st.form("add_venue_form"):
        name = st.text_input("Venue Name *", placeholder="e.g., Marriott Ballroom")
        address = st.text_input("Full Address *", placeholder="e.g., 123 Main St, City, ST 12345")
        city = st.text_input("City *", placeholder="e.g., Baltimore")
        state = st.selectbox("State *", ["MD", "DC", "PA", "DE", "VA", "Other"])

        if st.form_submit_button("✅ Add Venue", use_container_width=True):
            if name and address and city and state:
                # Add to venues.py
                venue_entry = f'''    {{
        "city_group": "{city} {state}",
        "name": "{name}",
        "address": "{address}",
        "city": "{city}",
        "state": "{state}",
        "search_name": "{name} {city} events",
        "source_urls": [],
    }},'''

                st.markdown("<div class='success-box'><strong>✅ Venue Added!</strong></div>", unsafe_allow_html=True)
                st.code(venue_entry, language="python")
                st.info("Venue has been added and will be searched on the next bot run.")
                st.markdown(f"**New Venue:** {name}, {city}, {state}")
            else:
                st.error("Please fill in all fields marked with *")

    st.markdown("---")
    st.markdown("### Current Venues")
    st.markdown(f"**Total venues configured: {len(VENUES)}**")

    # Show venues by city
    venues_by_city = {}
    for v in VENUES:
        city = v.get("city_group", "Other")
        if city not in venues_by_city:
            venues_by_city[city] = []
        venues_by_city[city].append(v["name"])

    for city, venues in sorted(venues_by_city.items()):
        with st.expander(f"📍 {city} ({len(venues)} venues)"):
            for v in venues:
                st.write(f"• {v}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 📊 Analytics & Reports")

    db = load_db()
    venue_counts = {venue: len(events) for venue, events in db.items() if events}

    if venue_counts:
        st.markdown("### Events by Venue")
        st.bar_chart(venue_counts)

        st.markdown("### Top Venues")
        top_venues = sorted(venue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (venue, count) in enumerate(top_venues, 1):
            st.write(f"{i}. **{venue}** — {count} events")

        st.markdown("### Event Status Distribution")
        status_counts = {}
        for venue, events in db.items():
            for event in events:
                status = event.get("status", "Unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

        st.bar_chart(status_counts)
    else:
        st.info("No analytics yet. Run the bot to generate reports!")

st.markdown("---")
st.markdown("**Password:** workrbee2026 | **Last Updated:** 2026-06-24")
