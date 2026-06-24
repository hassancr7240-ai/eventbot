# EventBot Pro - Production Edition

**Smart conference & tradeshow event discovery bot**

---

## 🚀 Quick Start

### Login
- Password: `workrbee2026`

### How to Use

1. **🚀 Run Search Tab**
   - Select a venue
   - Set year range (2026-2030)
   - Click "START SEARCH"
   - Takes 5-15 minutes depending on venue size

2. **📊 View Results Tab**
   - See all discovered events
   - Filter by venue, city, or search term
   - View contact details, emails, phone numbers
   - Events displayed in chronological order

3. **📥 Export Tab**
   - Download results as Excel or CSV
   - Perfect format for your team
   - Includes all contact information

---

## 📋 Data Collected

For each event, we extract:
- ✅ Event Name
- ✅ Event Date
- ✅ Venue & Location
- ✅ Contact Person Name
- ✅ Contact Title (Event Manager, Registration Manager, CMP, etc.)
- ✅ Email Address
- ✅ Phone Number

---

## 🏗️ Project Files

```
eventbot/
├── app.py              ← Streamlit dashboard (main UI)
├── scraper.py          ← Event discovery engine
├── scheduler.py        ← Background task runner
├── deduplicator.py     ← Duplicate removal & data merge
├── venues.py           ← Venue database (62 venues)
├── excel_writer.py     ← Excel export utility
├── events_db.json      ← Local database
├── requirements.txt    ← Python dependencies
└── data/               ← Config & logs folder
    ├── events_db.json
    └── scheduler_config.json
```

---

## 💻 Local Development

### Run Locally
```bash
cd c:\Users\M A D I N A\Desktop\fiverr_project\eventbot
python -m streamlit run app.py
```

Opens at `http://localhost:8501`

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ☁️ Cloud Deployment (Streamlit Cloud)

### Deploy
1. Go to https://share.streamlit.io
2. Connect your GitHub repository
3. Select branch: `main`
4. Select file: `app.py`
5. Click Deploy

### Redeploy Latest Changes
1. Go to https://share.streamlit.io
2. Find your app
3. Click **3-dot menu** → **Reboot**

---

## 🔧 Configuration

### Venue Database
Edit `venues.py` to add/remove venues

### Scheduler Config
Edit `data/scheduler_config.json` to change:
- Frequency (daily/weekly)
- Run time
- Year range

---

## 📊 Features

✅ **Smart Search** - Uses industry sources for accurate results
✅ **Contact Extraction** - Finds emails, phones, contact names
✅ **Deduplication** - Removes duplicate events automatically
✅ **Chronological Order** - Events sorted by date
✅ **Easy Export** - Download as Excel or CSV
✅ **Clean UI** - Simple, professional interface
✅ **Fast** - 5-15 minutes per venue
✅ **Reliable** - Runs automatically or on-demand

---

## 🎯 Next Steps

1. **Test locally** - Run the app and search a venue
2. **Deploy to cloud** - Push to Streamlit Cloud
3. **Run searches** - Pick venues and export results
4. **Integrate with team** - Share link with colleagues

---

**EventBot Pro v4 - Production Ready** ✅
