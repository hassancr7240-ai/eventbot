"""
EventBot Pro — Production Streamlit Dashboard
Password-protected. Full event tracker, run bot, export Excel.
"""

import os
import sys
import threading
import logging
import time
from datetime import datetime
from queue import Queue, Empty

import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from venues import VENUES, EVENT_TYPES, INDUSTRY_SOURCES
from scraper import generate_phrases, scrape_venue, crawl_all_industry_sources
from deduplicator import (
    upsert_records, get_all_records, get_stats,
    record_run_timestamp, update_record, load_db,
)
from excel_writer import build_excel, get_latest_excel

logging.basicConfig(level=logging.INFO)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EventBot Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PASSWORD PROTECTION ───────────────────────────────────────────────────────
try:
    PASSWORD = st.secrets["EVENTBOT_PASSWORD"]
except Exception:
    PASSWORD = os.environ.get("EVENTBOT_PASSWORD", "workrbee2026")

def _check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <style>
    .login-box { max-width: 380px; margin: 120px auto; padding: 40px;
                 background: white; border-radius: 16px;
                 box-shadow: 0 4px 24px rgba(0,0,0,0.10); }
    .login-title { font-size: 26px; font-weight: 700; color: #0F1F3D;
                   text-align: center; margin-bottom: 8px; }
    .login-sub { font-size: 14px; color: #6B7280; text-align: center;
                 margin-bottom: 28px; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-title">🎯 EventBot Pro</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-sub">Enter your password to continue</div>', unsafe_allow_html=True)
            pwd = st.text_input("Password", type="password", key="pwd_input",
                                label_visibility="collapsed",
                                placeholder="Enter password...")
            if st.button("Sign In", use_container_width=True, type="primary"):
                if pwd == PASSWORD:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    return False

if not _check_password():
    st.stop()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stSidebar"] { background: #0F1F3D !important; }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] div { color: #E2E8F0 !important; }
  .metric-card { background: white; border: 1px solid #E2E8F0; border-radius: 10px;
                 padding: 18px 20px; text-align: center; }
  .metric-num { font-size: 30px; font-weight: 700; color: #0F1F3D; }
  .metric-lbl { font-size: 12px; color: #6B7280; margin-top: 3px; }
  .log-box { background:#0F172A; color:#E2E8F0; font-family:monospace; font-size:12px;
             padding:14px; border-radius:8px; height:260px; overflow-y:auto; line-height:1.8; }
  .sec-head { font-size:17px; font-weight:700; color:#0F1F3D; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for key, default in [
    ("log_lines", []),
    ("running", False),
    ("stop_event", threading.Event()),
    ("log_queue", Queue()),
    ("new_count", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 EventBot Pro")
    st.markdown("---")
    page = st.radio("", [
        "🏠 Dashboard",
        "🤖 Run Bot",
        "📋 Live Tracker",
        "📥 Export Excel",
        "⚙️ Settings",
    ], label_visibility="collapsed")
    st.markdown("---")
    s = get_stats()
    st.markdown(f"**Events:** {s['total_events']}")
    st.markdown(f"**Contacts:** {s['total_contacts']}")
    st.markdown(f"**Emailed:** {s['total_emailed']}")
    st.markdown(f"**Booked:** {s['total_booked']}")
    st.markdown(f"**Last run:** {s['last_run']}")
    st.markdown("---")
    if st.button("🔒 Sign out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.markdown("## 🎯 EventBot Pro")
    st.markdown("Automated event & contact discovery — DC, Baltimore, Philadelphia, Delaware, Bethesda, National Harbor.")
    st.markdown("---")

    c1,c2,c3,c4,c5 = st.columns(5)
    for col, label, val in zip(
        [c1,c2,c3,c4,c5],
        ["Events Found","Contacts","Emailed","Called","Booked"],
        [s["total_events"],s["total_contacts"],s["total_emailed"],s["total_called"],s["total_booked"]],
    ):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-num">{val}</div>'
                        f'<div class="metric-lbl">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    records = get_all_records()
    if records:
        df = pd.DataFrame(records)
        df = df[df["event_name"].str.len() > 5]

        st.markdown('<div class="sec-head">📅 Recent Events</div>', unsafe_allow_html=True)
        cols = ["event_name","venue_name","city","state","event_dates","contact_person","contact_title","email","phone","status"]
        avail = [c for c in cols if c in df.columns]
        st.dataframe(
            df.sort_values("scraped_at", ascending=False)[avail].head(25),
            use_container_width=True, height=400
        )
    else:
        st.info("No data yet. Go to **Run Bot** to start scraping.")

    st.markdown("---")
    st.markdown('<div class="sec-head">📍 Venue Coverage</div>', unsafe_allow_html=True)
    db = load_db()
    city_groups: dict[str,list] = {}
    for v in VENUES:
        city_groups.setdefault(v["city_group"], []).append(v)

    cols = st.columns(3)
    for i, (cg, venue_list) in enumerate(city_groups.items()):
        with cols[i % 3]:
            st.markdown(f"**{cg}**")
            for v in venue_list:
                count = len(db.get(v["name"], []))
                dot = "🟢" if count > 0 else "⚪"
                st.markdown(f"{dot} {v['name']} ({count})")


# ═══════════════════════════════════════════════════════════════════════════════
# RUN BOT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 Run Bot":
    st.markdown("## 🤖 Run Event Research Bot")
    st.markdown("The bot generates all search phrases automatically, searches Google (rate-limited), "
                "crawls all industry directories, visits event websites, and extracts contacts.")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Select Venues")
        city_group_names = sorted({v["city_group"] for v in VENUES})
        sel_cg = st.selectbox("City / Region", ["All Regions"] + city_group_names)
        if sel_cg == "All Regions":
            venue_options = [v["name"] for v in VENUES]
        else:
            venue_options = [v["name"] for v in VENUES if v["city_group"] == sel_cg]
        sel_venues = st.multiselect(
            "Venues (leave blank = all)",
            venue_options,
            default=venue_options[:2],
        )
        if not sel_venues:
            sel_venues = venue_options

    with col2:
        st.markdown("### Year Range")
        cy = datetime.now().year
        start_yr = st.selectbox("From", list(range(cy, cy+2)), index=0)
        end_yr   = st.selectbox("To",   list(range(cy, cy+5)), index=3)
        st.markdown("### Sources")
        use_google   = st.checkbox("Google search", value=True)
        use_industry = st.checkbox("Industry directories", value=True,
                                   help="allconferencealert.net, 10times.com, tradeshowz.com, etc.")

    # Phrase preview
    if sel_venues:
        sample = next((v for v in VENUES if v["name"] == sel_venues[0]), None)
        if sample:
            ph = generate_phrases(sample["search_name"], start_yr, end_yr, city=sample.get("city",""))
            st.info(f"**{len(ph):,} search phrases** for **{sel_venues[0]}**  •  "
                    f"Sample: `{ph[0]}` … `{ph[12]}` … `{ph[-1]}`")

    st.markdown("---")
    col_run, col_stop, _ = st.columns([1, 1, 4])
    run_btn  = col_run.button("▶ Run Bot",  disabled=st.session_state.running,  use_container_width=True, type="primary")
    stop_btn = col_stop.button("⬛ Stop",   disabled=not st.session_state.running, use_container_width=True)

    if stop_btn:
        st.session_state.stop_event.set()
        st.session_state.running = False
        st.warning("Stop signal sent.")

    pbar   = st.progress(0)
    status = st.empty()
    logbox = st.empty()

    # Drain log queue
    while True:
        try:
            line = st.session_state.log_queue.get_nowait()
            st.session_state.log_lines.append(line)
        except Empty:
            break

    if st.session_state.log_lines:
        html = "<br>".join(st.session_state.log_lines[-50:])
        logbox.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)

    if run_btn and not st.session_state.running:
        st.session_state.running  = True
        st.session_state.stop_event = threading.Event()
        st.session_state.log_lines  = []
        st.session_state.new_count  = 0
        q = st.session_state.log_queue

        venues_to_run = [v for v in VENUES if v["name"] in sel_venues]

        def _log(msg, color="#E2E8F0"):
            ts = datetime.now().strftime("%H:%M:%S")
            q.put(f'<span style="color:#475569">[{ts}]</span> <span style="color:{color}">{msg}</span>')

        def _run():
            total_new = total_upd = 0
            for vi, venue in enumerate(venues_to_run):
                if st.session_state.stop_event.is_set():
                    break
                _log(f"── Venue {vi+1}/{len(venues_to_run)}: {venue['name']}", "#38BDF8")
                all_recs = []

                if use_google:
                    ph = generate_phrases(venue["search_name"], start_yr, end_yr, venue.get("city",""))
                    _log(f"Google: {len(ph)} phrases", "#94A3B8")
                    def _cb(cur, tot, msg):
                        _log(f"  {msg}", "#64748B")
                    recs = scrape_venue(venue, start_yr, end_yr,
                                        progress_callback=_cb,
                                        stop_event=st.session_state.stop_event)
                    _log(f"Google done — {len(recs)} records", "#4ADE80")
                    all_recs.extend(recs)

                if use_industry and not st.session_state.stop_event.is_set():
                    _log(f"Industry directories...", "#38BDF8")
                    irecs = crawl_all_industry_sources(venue, st.session_state.stop_event)
                    _log(f"Directories done — {len(irecs)} records", "#4ADE80")
                    all_recs.extend(irecs)

                if all_recs:
                    added, upd = upsert_records(all_recs)
                    total_new += added; total_upd += upd
                    _log(f"✓ {venue['name']}: +{added} new, ~{upd} updated", "#4ADE80")
                else:
                    _log(f"⚠ {venue['name']}: no records found", "#FBBF24")

            record_run_timestamp()
            st.session_state.new_count  = total_new
            st.session_state.running    = False
            _log(f"✅ Complete — +{total_new} new  ~{total_upd} updated", "#4ADE80")

        threading.Thread(target=_run, daemon=True).start()
        st.rerun()

    if st.session_state.running:
        status.info("Bot running… page auto-refreshes.")
        time.sleep(2)
        st.rerun()
    elif st.session_state.new_count > 0:
        st.success(f"Done! **{st.session_state.new_count}** new records added.")


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE TRACKER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Live Tracker":
    st.markdown("## 📋 Live Event Tracker")
    st.markdown("Filter, view, and update all records. Changes save instantly.")
    st.markdown("---")

    records = get_all_records()
    if not records:
        st.info("No records yet. Run the bot first.")
        st.stop()

    df = pd.DataFrame(records)
    df = df[df["event_name"].str.len() > 4]

    # Filters
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        cities = ["All"] + sorted(df["city"].dropna().unique().tolist())
        city_f = st.selectbox("City", cities)
    with c2:
        states = ["All"] + sorted(df["state"].dropna().unique().tolist())
        state_f = st.selectbox("State", states)
    with c3:
        venues_f = ["All"] + sorted(df["venue_name"].dropna().unique().tolist())
        venue_f = st.selectbox("Venue", venues_f)
    with c4:
        stat_opts = ["All","New","Emailed","Called","Voicemail","Booked","Contract Signed","Do Not Contact"]
        status_f = st.selectbox("Status", stat_opts)

    search = st.text_input("🔍 Search event name, contact, or email", "")

    fdf = df.copy()
    if city_f   != "All": fdf = fdf[fdf["city"] == city_f]
    if state_f  != "All": fdf = fdf[fdf["state"] == state_f]
    if venue_f  != "All": fdf = fdf[fdf["venue_name"] == venue_f]
    if status_f != "All": fdf = fdf[fdf["status"].str.lower() == status_f.lower()]
    if search:
        mask = (
            fdf["event_name"].str.contains(search, case=False, na=False) |
            fdf["contact_person"].str.contains(search, case=False, na=False) |
            fdf["email"].str.contains(search, case=False, na=False)
        )
        fdf = fdf[mask]

    st.markdown(f"**{len(fdf)} records**")

    m1,m2,m3,m4 = st.columns(4)
    def _ct(d, kw): return d[d["status"].str.lower().str.contains(kw, na=False)].shape[0]
    m1.metric("New",       _ct(fdf,"new"))
    m2.metric("Emailed",   _ct(fdf,"email"))
    m3.metric("Called",    _ct(fdf,"call") + _ct(fdf,"voicemail"))
    m4.metric("Booked",    _ct(fdf,"book") + _ct(fdf,"contract"))

    st.markdown("---")

    show_cols = ["event_name","venue_name","city","state","event_dates",
                 "contact_person","contact_title","email","phone",
                 "status","email_sent","call_notes_1","call_notes_2","call_notes_3","call_notes_4"]
    avail = [c for c in show_cols if c in fdf.columns]
    fdf_show = fdf[avail].reset_index(drop=True)

    edited = st.data_editor(
        fdf_show,
        use_container_width=True,
        num_rows="fixed",
        height=540,
        column_config={
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["New","Emailed","Called","Voicemail","Booked","Contract Signed","Do Not Contact"],
            ),
            "email_sent": st.column_config.SelectboxColumn(
                "Email Sent?",
                options=["","Yes","No"],
            ),
            "event_name":    st.column_config.TextColumn("Event Name",    width="large"),
            "contact_person":st.column_config.TextColumn("Contact",       width="medium"),
            "contact_title": st.column_config.TextColumn("Title",         width="medium"),
            "email":         st.column_config.TextColumn("Email",         width="medium"),
            "call_notes_1":  st.column_config.TextColumn("Call Notes 1",  width="medium"),
            "call_notes_2":  st.column_config.TextColumn("Call Notes 2",  width="medium"),
            "call_notes_3":  st.column_config.TextColumn("Call Notes 3",  width="medium"),
            "call_notes_4":  st.column_config.TextColumn("Call Notes 4",  width="medium"),
        },
        key="tracker_grid",
    )

    if st.button("💾 Save Changes", type="primary"):
        saved = 0
        for _, row in edited.iterrows():
            email = str(row.get("email","")).strip()
            if not email:
                continue
            updates = {
                "status":       str(row.get("status","New")),
                "email_sent":   str(row.get("email_sent","")),
                "call_notes_1": str(row.get("call_notes_1","")),
                "call_notes_2": str(row.get("call_notes_2","")),
                "call_notes_3": str(row.get("call_notes_3","")),
                "call_notes_4": str(row.get("call_notes_4","")),
                "contact_person": str(row.get("contact_person","")),
                "contact_title":  str(row.get("contact_title","")),
            }
            if update_record(email, updates):
                saved += 1
        st.success(f"✅ Saved {saved} records.")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT EXCEL
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📥 Export Excel":
    st.markdown("## 📥 Export to Excel")
    st.markdown("Downloads a workbook matching your exact format — one tab per venue, chronological order.")
    st.markdown("---")

    if st.button("🔄 Build Excel Now", type="primary", use_container_width=False):
        with st.spinner("Building workbook…"):
            try:
                path = build_excel()
                st.session_state["last_excel"] = path
                st.success(f"Built: **{os.path.basename(path)}**")
            except ValueError as e:
                st.error(str(e))

    path = st.session_state.get("last_excel") or get_latest_excel()
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        st.download_button(
            "⬇️ Download Excel",
            data=data,
            file_name=os.path.basename(path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.caption(f"File: `{path}`")

    st.markdown("---")
    st.markdown("""
**What's in the file:**
- **SUMMARY** tab — all venues with event + contact counts
- **One tab per venue** — matching your exact current format
- Columns: Event Name · Contact Person · Email · Telephone · Date of Event · e-mail sent · Call Notes 1–11
- Sorted **chronologically** by date
- Rows **colour-coded** by status (New=blue, Emailed=amber, Called=purple, Booked=green)
- Email addresses are clickable mailto links
    """)


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    # ── Brave Search API Key ──────────────────────────────────────────────────
    st.markdown("### 🔍 Brave Search API Key")
    st.markdown(
        "Brave Search gives **real web results** with no blocking. "
        "**Free tier: 2,000 searches/month — no credit card needed.**\n\n"
        "Get your free key at 👉 **https://api.search.brave.com/app/keys**\n\n"
        "With this key the bot searches Google **and** Brave for every phrase, "
        "giving significantly more event results."
    )
    import json as _j
    _cfg_path = os.path.join(os.path.dirname(__file__), "data", "config.json")
    _cfg = _j.load(open(_cfg_path, encoding="utf-8")) if os.path.exists(_cfg_path) else {}
    _current_brave_key = _cfg.get("brave_api_key", "")
    with st.form("brave_key_form"):
        brave_key_input = st.text_input(
            "Brave Search API Key",
            value=_current_brave_key,
            type="password",
            placeholder="Paste your free Brave API key here",
        )
        if st.form_submit_button("💾 Save API Key"):
            _cfg["brave_api_key"] = brave_key_input.strip()
            os.makedirs(os.path.dirname(_cfg_path), exist_ok=True)
            _j.dump(_cfg, open(_cfg_path, "w", encoding="utf-8"), indent=2)
            if brave_key_input.strip():
                st.success("Brave Search key saved! Bot will now use Brave + Google for all searches.")
                st.rerun()
            else:
                st.info("Key cleared. Bot will use industry websites only.")
                st.rerun()
    if _current_brave_key:
        st.success(f"Brave Search is ACTIVE — key ends: ...{_current_brave_key[-6:]}")
    else:
        st.warning("No Brave key set. Bot uses industry websites only (still works — Brave just gives more results).")

    st.markdown("---")
    st.markdown("### 🔑 Change Password")
    with st.form("pwd_form"):
        new_pwd = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        if st.form_submit_button("Update Password"):
            if new_pwd and new_pwd == confirm:
                st.info(f"Set the environment variable `EVENTBOT_PASSWORD={new_pwd}` "
                        f"before starting the app to use this password.")
            else:
                st.error("Passwords don't match.")

    st.markdown("---")
    st.markdown("### 📍 All Configured Venues")
    vdf = pd.DataFrame([{
        "City Group": v["city_group"],
        "Venue": v["name"],
        "City": v["city"],
        "State": v["state"],
        "Address": v["address"],
    } for v in VENUES])
    st.dataframe(vdf, use_container_width=True, height=380)
    st.markdown(f"**{len(VENUES)} venues configured**")

    st.markdown("---")
    st.markdown("### ➕ Add a New Venue")
    with st.form("add_venue"):
        c1, c2 = st.columns(2)
        with c1:
            nname   = st.text_input("Venue Name", placeholder="e.g. Westin Alexandria")
            naddr   = st.text_input("Address")
            ncity   = st.text_input("City")
        with c2:
            nstate  = st.text_input("State (2-letter)", placeholder="VA")
            ngroup  = st.text_input("City Group", placeholder="e.g. Northern Virginia")
            nsearch = st.text_input("Google search name", placeholder="e.g. Westin Alexandria VA events")
        if st.form_submit_button("Generate Code"):
            if nname and ncity and nstate:
                st.code(f"""{{
    "city_group": "{ngroup}",
    "name": "{nname}",
    "address": "{naddr}",
    "city": "{ncity}",
    "state": "{nstate}",
    "search_name": "{nsearch or nname}",
    "source_urls": [],
}},""", language="python")
                st.info("Copy the block above and paste it into venues.py in the VENUES list, then restart the app.")

    st.markdown("---")
    st.markdown("### ℹ️ System Info")
    st.markdown(f"- **Venues configured:** {len(VENUES)}")
    st.markdown(f"- **Event types searched:** {len(EVENT_TYPES)}")
    st.markdown(f"- **Industry sources:** {len(INDUSTRY_SOURCES)}")
    st.markdown(f"- **Last bot run:** {get_stats()['last_run']}")
    st.markdown(f"- **DB path:** `data/events_db.json`")
    st.markdown(f"- **Output folder:** `output/`")
