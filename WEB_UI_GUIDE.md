# Web UI User Guide

**Senior Living Community Recommendation System - Web Interface**

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Make sure your `.env` file has:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional (for CRM integration)
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/service-account.json
```

### 3. Start the Server

```bash
python app.py
```

The server will start at `http://localhost:5000`

Open your web browser and navigate to: **http://localhost:5000**

---

## 📱 Features Overview

### 1. **New Consultation** (Main Tab)

Process client consultations using either:

#### Audio Recording
- **Drag & drop** or **click to browse** audio files
- Supported formats: M4A, MP3, WAV, OGG
- Maximum file size: 50MB
- Automatic extraction of client requirements
- AI-powered recommendations

#### Text Consultation
- Paste or type consultation transcripts
- Same AI processing as audio
- Faster processing time

**Options:**
- ✅ **Push to Google Sheets CRM** - Automatically save results to spreadsheet

**Results Display:**
- Client information summary
- Top 5 community recommendations with:
  - Rank and combined score
  - Monthly fee, distance, availability
  - AI reasoning for each recommendation
- Performance metrics (time, tokens, cost)

---

### 2. **Community Database** (Database Tab)

Manage your community listings:

#### View Communities
- **Search** - Filter by ID, care level, ZIP code, or waitlist
- **Statistics** - View total communities, average fees, enhanced services count
- **Table View** - Sortable, searchable table with all communities

#### Add Community
1. Click **"Add Community"** button
2. Fill in required fields (marked with *)
   - Care Level (Independent/Assisted/Memory Care)
   - Monthly Fee
   - ZIP Code
3. Optional fields:
   - Contract Rate
   - Waitlist Status
   - Work with Placement
   - Enhanced/Enriched services
4. Click **"Save Community"**

#### Edit Community
1. Click the **edit (pencil)** icon next to any community
2. Update fields in the modal
3. Click **"Update Community"**

#### Delete Community
1. Click the **delete (trash)** icon
2. Confirm deletion
3. Community removed from database

**⚠️ Important:** All database changes affect future recommendations immediately.

---

### 3. **Help** (Help Tab)

Comprehensive user guide with:
- Getting Started instructions
- Database management guide
- Understanding results
- Tips & best practices
- System requirements
- Troubleshooting

---

## 🎨 UI Design Philosophy

### For Non-Technical Users

The UI is designed with simplicity and clarity:

1. **Three Main Sections**
   - New Consultation (primary workflow)
   - Community Database (manage data)
   - Help (documentation)

2. **Visual Feedback**
   - Loading indicators for all operations
   - Success/error messages
   - Real-time validation

3. **Drag & Drop**
   - Upload audio files by dragging them onto the page
   - No technical knowledge required

4. **Inline Help**
   - Placeholder text shows examples
   - Field labels clearly marked (* for required)
   - Tooltips on hover

5. **Responsive Design**
   - Works on desktop, tablet, and mobile
   - Adapts to screen size

---

## 💡 Usage Tips

### Best Practices for Consultations

**Audio Files:**
- Ensure clear audio quality
- Speak clearly and include all details
- Explicitly mention: budget, timeline, location
- File formats: M4A (best), MP3, WAV, OGG

**Text Input:**
- Use conversation format (Agent: / Client:)
- Be specific about requirements
- Include ZIP code or city name
- State timeline clearly:
  - "immediate" = within 1 month
  - "near-term" = 1-3 months
  - "flexible" = 3+ months

### Database Management Tips

1. **Keep Data Current**
   - Update monthly fees regularly
   - Refresh waitlist status often
   - Verify ZIP codes are accurate

2. **Data Quality**
   - Fill in all important fields
   - Use consistent formatting
   - Double-check before saving

3. **Search Efficiently**
   - Search by ID for specific communities
   - Filter by ZIP code for location-based queries
   - Use care level to narrow results

---

## 🔧 Technical Details

### System Architecture

```
┌─────────────────┐
│   Web Browser   │
│   (HTML/CSS/JS) │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  Flask Server   │
│   (app.py)      │
└────────┬────────┘
         │
         ├─► Recommendation System (AI Processing)
         ├─► Database (Excel File)
         └─► Google Sheets (CRM)
```

### No Middleware Complexity

- **Single Flask Server** - No separate backend/frontend servers
- **Static HTML/CSS/JS** - No build process required
- **Direct File Access** - Excel database read/write
- **Simple Deployment** - Just run `python app.py`

### API Endpoints

**Consultation:**
- `POST /api/process-audio` - Process audio file
- `POST /api/process-text` - Process text consultation

**Database:**
- `GET /api/communities` - Get all communities
- `GET /api/communities/<id>` - Get specific community
- `POST /api/communities` - Add new community
- `PUT /api/communities/<id>` - Update community
- `DELETE /api/communities/<id>` - Delete community
- `GET /api/stats` - Get database statistics

**System:**
- `GET /api/health` - Health check

---

## ⚠️ Troubleshooting

### Server Won't Start

**Error:** `Address already in use`
**Solution:** Port 5000 is occupied. Kill the process or change port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
```

### Audio Upload Fails

**Error:** `Invalid file type`
**Solution:** Only M4A, MP3, WAV, OGG files are supported. Convert your file first.

**Error:** `File too large`
**Solution:** Maximum file size is 50MB. Compress or trim your audio file.

### Processing Takes Too Long

**Cause:** Gemini API timeouts or slow responses
**Solution:**
- System has built-in retry logic (3 attempts)
- Wait patiently - processing can take 30-120 seconds
- Check internet connection

### Database Changes Don't Appear

**Solution:** Refresh the page or switch to another tab and back.

### CRM Push Fails

**Cause:** Google Sheets not configured
**Solution:**
1. Verify `.env` has correct credentials
2. Check spreadsheet is shared with service account
3. Ensure Google Sheets API is enabled

---

## 🔐 Security Notes

### Local Use Only

This UI is designed for **local use only**:
- No authentication system
- No encryption for API requests
- Direct file system access

### For Production Deployment

If you need to deploy this publicly:
1. Add authentication (Flask-Login)
2. Use HTTPS (SSL certificates)
3. Add CSRF protection
4. Implement rate limiting
5. Use production WSGI server (Gunicorn)
6. Store database in proper database system (PostgreSQL)

---

## 📚 Additional Resources

- **Main README:** [README.md](README.md)
- **Ranking System Docs:** [RANKING_SYSTEM_README.md](RANKING_SYSTEM_README.md)
- **Google Sheets Setup:** [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
- **Codebase Structure:** [CODEBASE_STRUCTURE.md](CODEBASE_STRUCTURE.md)

---

## 🎯 Keyboard Shortcuts

- **Ctrl + Click** file upload area = Open file browser
- **Drag & Drop** = Upload audio file
- **Escape** = Close modal
- **Enter** in search box = Search immediately

---

## 📞 Getting Help

If you encounter issues:

1. Check the **Help** tab in the UI
2. Review console logs in browser (F12 → Console)
3. Check Flask server logs in terminal
4. Verify `.env` configuration
5. Ensure all dependencies are installed

---

**Enjoy using the Senior Living Recommendation System! 🏘️**
