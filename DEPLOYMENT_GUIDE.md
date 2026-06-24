# EventBot Pro - Complete Deployment & Testing Guide

## 🚀 STEP 1: Redeploy on Streamlit Cloud

### What to do:
1. Go to https://share.streamlit.io
2. Login with your GitHub account
3. Find your "eventbot" app in the list
4. Click the **3-dot menu** (top right corner)
5. Click **"Reboot app"**
6. Wait 2-3 minutes for it to redeploy with new code

### What to check:
- App loads without errors
- You see login screen with password input
- Password is `workrbee2026`
- All 4 tabs appear: 🚀 Run Bot, 📋 Live Tracker, ➕ Add Venues, 📥 Export & Upload

---

## 🤖 STEP 2: Run the Bot (First Time)

### How your client does it:

**1. Login**
- Go to https://eventbot-qyn45u3nykr7wnsrpp7hlt.streamlit.app/
- Enter password: `workrbee2026`
- Click Login

**2. Go to "🚀 Run Bot" tab**

**3. Set Search Filters** (she can customize or use defaults)
   - **Year Range:** Default is 2026 (START: 2026, END: 2026)
   - **Venues:** Default is "All Venues" (searches all 62)
   - **Cities:** All checked by default
   - **Quick Presets:** Can click 🟢 Fast, 🟡 Standard, or 🔴 Full

**4. Click "▶️ START BOT SEARCH"**
   - Bot starts in background
   - Yellow warning appears: "⏳ Bot is searching..."
   - Page auto-refreshes every 3 seconds

**5. While bot runs:**
   - Go to "📋 Live Tracker" tab
   - Watch results fill up in real-time
   - Can search, filter by venue/status
   - Can use "🚫 Hide Duplicates" to see unique events only
   - Can download CSV anytime

**6. When bot finishes (15-20 min):**
   - Warning box disappears
   - All results visible in Live Tracker
   - Shows: Total events, New events, Unique venues

---

## 📊 STEP 3: What to Check / Quality Control

### After bot completes, check Live Tracker:

**✅ Good signs:**
- Events from MULTIPLE venues (Baltimore, Philadelphia, DC, Wilmington, etc.)
- Real conference event names (not generic junk)
- Mix of venues showing events
- Minimal duplicates (if any)
- No Chinese text, podcasts, or fake events

**❌ Bad signs (report if seen):**
- Same event repeated 5-6 times
- Events like "Club Meeting", "Sports Representative meeting" appearing everywhere
- Junk data: "Conference Next", "Upcoming Conferences", Chinese text
- Only 3-4 venues showing results
- Lots of empty Email/Phone columns (expected)

### Specific checks:

**Check 1: Event Quality**
- Click on a few event names
- Should be real conference names like:
  - "Summer Leadership Summit 2026"
  - "Tech Conference & Expo"
  - "Business Networking Summit"
- NOT: "Club Meeting", "Glow-Up Soirée", "Workshop"

**Check 2: Venue Coverage**
- Use "Filter by venue" dropdown
- Should see venues from different cities:
  - ✅ DC Convention Center
  - ✅ Marriott Marquis (DC)
  - ✅ Hyatt Regency (Baltimore)
  - ✅ Philadelphia Convention Center
  - ✅ Wilmington venues
  - NOT ❌ Same 3 venues like before

**Check 3: Duplicates**
- Look for same event in multiple venues
- Click "🚫 Hide Duplicates" checkbox
- Count should drop significantly if duplicates exist
- If Hide Duplicates works → deduplication is working

**Check 4: Dates are reasonable**
- Should see dates in 2026 (or your selected range)
- Not future years like 2030, 2050
- Not past dates like 2023, 2024

---

## 📥 STEP 4: Export & Upload to Google Sheets

### If bot results look good:

**1. Go to "📥 Export & Upload" tab**

**2. Click "📥 Download CSV"**
   - Downloads file like: `EventBot_20260624_1410.csv`
   - Save to her computer

**3. Upload to Google Sheets:**
   - Open Google Sheet: https://docs.google.com/spreadsheets/d/1sQEvI5uHEYYppPVIpe0qqzTiqj-oS5ryhN21xNj1scA
   - Click **File** → **Import** → **Upload file**
   - Select the CSV you just downloaded
   - Click **Import**
   - New tab created with all events
   - Done! ✅

---

## ➕ STEP 5: Add New Venues

### If she wants to add a venue:

**1. Go to "➕ Add Venues" tab**

**2. Fill the form:**
   - Venue Name: e.g., "Marriott Ballroom"
   - Address: e.g., "123 Main St, Baltimore, MD 21201"
   - City: e.g., "Baltimore"
   - State: "MD", "DC", "PA", "DE", "VA", etc.

**3. Click "✅ Add Venue"**
   - Green success message appears
   - Venue added automatically
   - Will be searched on next bot run

---

## ⏰ STEP 6: Automatic Daily Runs

### The bot runs automatically:
- **Time:** 6:00 AM every morning
- **Duration:** 15-20 minutes
- **What it does:** Searches all 62 venues for new events
- **Results:** Automatically saved in Live Tracker

### To check if it ran:
1. Go to Live Tracker tab
2. Look at event timestamps in "Updated" column
3. If recent (today), bot ran successfully
4. Or check "Last Run" timestamp at bottom of screen

---

## 🧪 QUICK TEST CHECKLIST

**After redeployment, run this test:**

- [ ] App loads and asks for password
- [ ] Login works with `workrbee2026`
- [ ] See all 4 tabs
- [ ] Click "Run Bot" tab
- [ ] See filter options (years, venues, cities, presets)
- [ ] Click "▶️ START BOT SEARCH"
- [ ] Warning "Bot is searching" appears
- [ ] Go to "Live Tracker" tab
- [ ] See events appearing (within 2-3 min)
- [ ] Events from multiple venues visible
- [ ] "Hide Duplicates" toggle works
- [ ] Can download CSV from "Export & Upload"
- [ ] Can add venue from "Add Venues" tab
- [ ] Summary metrics show correct counts

**If all ✅ PASSED → Ready for production!**

---

## 🐛 Troubleshooting

### Bot says "searching" but no results after 30 min:
- Click "Live Tracker" and refresh page
- If still nothing: Reboot Streamlit app and try again

### Only seeing 3-4 venues:
- Wait full 20 minutes (bot processes 62 venues)
- Check "Hide Duplicates" is OFF
- Try running again

### CSV won't download:
- Try a different browser (Chrome/Firefox/Safari)
- Make sure bot completed (yellow warning gone)

### Venue add didn't work:
- Refresh page after adding
- Try again with simpler venue name

### Want to run bot manually (not wait for 6 AM):
- Go to "Run Bot" tab
- Click "START BOT SEARCH" anytime
- Results will appear in real-time

---

## 📞 Important Info for Client

**Share with her:**

```
EventBot Pro is ready!

✅ Search starts automatically every day at 6:00 AM
✅ Results appear in Live Tracker in real-time (15-20 min)
✅ Can run manually anytime by clicking START BOT
✅ Add new venues yourself in Add Venues tab
✅ Download as CSV and upload to Google Sheets in 2 clicks

Password: workrbee2026
Link: https://eventbot-qyn45u3nykr7wnsrpp7hlt.streamlit.app/

Questions? Let me know!
```

---

## 📋 Local Testing (Developer Only)

If you want to test locally before sending to Streamlit:

```bash
# In terminal, go to project folder
cd c:\Users\M A D I N A\Desktop\fiverr_project\eventbot

# Run Streamlit locally
streamlit run app.py

# Opens http://localhost:8501 in browser
# Test everything before pushing to cloud
```

---

**That's it! 🚀 You're ready to deploy!**
