"""
EventBot Pro - Production Edition
Clean, Simple, Fast | No clutter | Real results
"""

import streamlit as st
import os
import json
import subprocess
import threading
import time
from datetime import datetime
from deduplicator import get_stats, load_db
from venues import VENUES
import pandas as pd
import csv
from io import StringIO

st.set_page_config(
    page_title="EventBot Pro",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": "EventBot Pro v4 - Production"}
)

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM THEME
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
* { font-family: 'Segoe UI', system-ui, sans-serif; }
body { background: #ffffff; }
.main { background: #ffffff; }

/* Clean header */
h1 { color: #1a1a1a; font-size: 2rem; margin-bottom: 0.5rem; }
h2 { color: #2d2d2d; font-size: 1.4rem; margin-top: 1.5rem; }

/* Cards */
.metric-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}
.metric-num { font-size: 2.5rem; font-weight: bold; }
.metric-label { font-size: 0.9rem; opacity: 0.9; margin-top: 5px; }

/* Status boxes */
.success-box { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 5px; }
.warning-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 5px; }
.error-box { background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; border-radius: 5px; }
.info-box { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; border-radius: 5px; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    font-weight: 600;
    width: 100%;
}
.stButton > button:hover {
    opacity: 0.9;
}

/* Tables */
.dataframe { font-size: 0.9rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #e0e0e0; }
.stTabs [aria-selected="true"] { color: #667eea; border-bottom: 3px solid #667eea; }

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════

PASSWORD = "workrbee2026"

def check_auth():
    if "auth" not in st.session_state:
        st.session_state.auth = False

    if not st.session_state.auth:
        st.markdown("<h1 style='text-align: center; margin-top: 10rem;'>🔒 EventBot Pro</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pwd = st.text_input("Enter Password", type="password")
            if st.button("Login", use_container_width=True):
                if pwd == PASSWORD:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("❌ Wrong password")
        st.stop()

check_auth()

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

if "bot_running" not in st.session_state:
    st.session_state.bot_running = False
if "selected_venue" not in st.session_state:
    st.session_state.selected_venue = None

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("# 🤖 EventBot Pro")
st.markdown("**Conference & Tradeshow Event Discovery**")
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD METRICS
# ─────────────────────────────────────────────────────────────────────────────

stats = get_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-num">{stats['total_events']}</div>
        <div class="metric-label">Events Found</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-num">{stats['total_contacts']}</div>
        <div class="metric-label">Contacts</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-num">{stats['total_emailed']}</div>
        <div class="metric-label">Emailed</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-num">{len(VENUES)}</div>
        <div class="metric-label">Venues</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab_run, tab_results, tab_export = st.tabs(["🚀 Run Search", "📊 View Results", "📥 Export"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: RUN SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

with tab_run:
    st.markdown("## 🚀 Start Search")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Settings")

        # Venue selection
        venue_names = sorted(list(set([v["name"] for v in VENUES])))
        selected_venue = st.selectbox(
            "Select Venue",
            venue_names,
            help="Choose a venue to search for events"
        )

        # Year selection
        st.markdown("**Year Range**")
        start_year = st.slider("Start", 2026, 2030, 2026)
        end_year = st.slider("End", 2026, 2030, 2026)

        if start_year > end_year:
            st.error("Start year must be before end year")

    with col2:
        st.markdown("### How It Works")
        st.info("""
        ✅ **Searches** the selected venue across multiple sources

        ✅ **Extracts** event details, dates, and contact information

        ✅ **Deduplicates** to remove duplicate events

        ✅ **Saves** results to database automatically

        ⏱️ **Takes** 5-15 minutes depending on venue
        """)

    st.markdown("---")

    # Run button
    col1, col2 = st.columns([2, 1])
    with col2:
        if st.button("▶️ START SEARCH", use_container_width=True, key="run_btn"):
            st.session_state.bot_running = True
            st.session_state.selected_venue = selected_venue
            st.rerun()

    # Running status
    if st.session_state.bot_running:
        st.markdown("""
        <div class='warning-box'>
        <strong>⏳ Search in progress...</strong><br>
        Go to "View Results" tab to see events as they're discovered.
        </div>
        """, unsafe_allow_html=True)

        def run_search_background():
            try:
                cmd = ["python", "scheduler.py", "--run-now", "--years", str(start_year), str(end_year)]
                result = subprocess.run(
                    cmd,
                    cwd=os.path.dirname(__file__),
                    capture_output=True,
                    text=True,
                    timeout=3600
                )
                st.session_state.bot_running = False
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.bot_running = False

        thread = threading.Thread(target=run_search_background, daemon=True)
        thread.start()
        time.sleep(2)
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: VIEW RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_results:
    st.markdown("## 📊 Event Results")

    db = load_db()

    if not db or sum(len(events) for events in db.values()) == 0:
        st.info("📭 No events yet. Click 'Run Search' to get started!")
    else:
        # Build events list
        all_events = []
        for venue_name, events in db.items():
            for event in events:
                all_events.append({
                    "Date": event.get("event_dates", ""),
                    "Event": event.get("event_name", ""),
                    "Venue": event.get("venue_name", ""),
                    "City": event.get("city", ""),
                    "Contact": event.get("contact_person", ""),
                    "Title": event.get("contact_title", ""),
                    "Email": event.get("email", ""),
                    "Phone": event.get("phone", ""),
                })

        if all_events:
            # Filters
            col1, col2, col3 = st.columns(3)

            with col1:
                search_term = st.text_input("🔍 Search events", placeholder="Event name, venue, contact...")
            with col2:
                venue_filter = st.selectbox("Venue", ["All"] + sorted(list(set([e["Venue"] for e in all_events]))))
            with col3:
                city_filter = st.selectbox("City", ["All"] + sorted(list(set([e["City"] for e in all_events]))))

            # Apply filters
            filtered = all_events

            if search_term:
                filtered = [e for e in filtered if search_term.lower() in str(e).lower()]

            if venue_filter != "All":
                filtered = [e for e in filtered if e["Venue"] == venue_filter]

            if city_filter != "All":
                filtered = [e for e in filtered if e["City"] == city_filter]

            # Display
            st.markdown(f"**Showing {len(filtered)} of {len(all_events)} events**")

            # Create DataFrame
            df = pd.DataFrame(filtered)
            df = df.sort_values(by=["Date", "Event"]) if "Date" in df.columns else df

            st.dataframe(df, use_container_width=True, height=500)

            # Quick stats
            st.markdown("---")
            st.markdown("### Quick Stats")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Events", len(filtered))

            with col2:
                has_contact = len([e for e in filtered if e["Contact"]])
                st.metric("With Contact", has_contact)

            with col3:
                has_email = len([e for e in filtered if e["Email"]])
                st.metric("With Email", has_email)

        else:
            st.warning("⚠️ No events in database")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

with tab_export:
    st.markdown("## 📥 Export Results")

    db = load_db()
    total_events = sum(len(events) for events in db.values())

    if total_events == 0:
        st.info("No events to export yet. Run a search first!")
    else:
        st.markdown(f"**Ready to export: {total_events} events**")

        # Build export data
        export_data = []
        for venue_name, events in db.items():
            for event in events:
                export_data.append({
                    "Date": event.get("event_dates", ""),
                    "Event Name": event.get("event_name", ""),
                    "Venue": event.get("venue_name", ""),
                    "City": event.get("city", ""),
                    "State": event.get("state", ""),
                    "Contact Person": event.get("contact_person", ""),
                    "Title": event.get("contact_title", ""),
                    "Email": event.get("email", ""),
                    "Phone": event.get("phone", ""),
                    "URL": event.get("event_url", ""),
                    "Status": event.get("status", ""),
                })

        # Sort by date
        try:
            export_data.sort(key=lambda x: x.get("Date", ""))
        except:
            pass

        # Excel export
        st.markdown("### Download as Excel")
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = Workbook()
            ws = wb.active
            ws.title = "Events"

            # Headers
            headers = list(export_data[0].keys())
            ws.append(headers)

            # Style headers
            header_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Data
            for row_data in export_data:
                ws.append([row_data.get(h, "") for h in headers])

            # Auto-width
            for column in ws.columns:
                max_length = max(len(str(cell.value or "")) for cell in column)
                ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 40)

            # Save
            filename = f"EventBot_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            wb.save(filename)

            with open(filename, "rb") as f:
                st.download_button("📥 Download Excel", f, filename)

            os.remove(filename)

        except Exception as e:
            st.error(f"Excel export error: {e}")

        # CSV export
        st.markdown("### Download as CSV")
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)

        st.download_button(
            "📥 Download CSV",
            csv_buffer.getvalue(),
            f"EventBot_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv"
        )

st.divider()
st.caption(f"EventBot Pro | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
