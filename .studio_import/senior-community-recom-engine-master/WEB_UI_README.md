# Web UI - Quick Reference

## 🚀 Getting Started in 3 Steps

### Step 1: Start the Server

**Windows:**
```bash
Double-click: START_WEB_UI.bat
```

**Mac/Linux:**
```bash
python app.py
```

### Step 2: Open Browser

Navigate to: **http://localhost:5000**

### Step 3: Start Using

- **New Consultation** → Upload audio or paste text
- **Community Database** → Manage communities
- **Help** → Read full user guide

---

## 🎯 Key Features

### For Non-Technical Users

✅ **No Command Line Required** - Everything in your web browser
✅ **Drag & Drop Upload** - Just drop your audio files
✅ **Visual Interface** - Beautiful cards and tables
✅ **Real-time Feedback** - See progress as it happens
✅ **Built-in Help** - Comprehensive guide in Help tab

### For Power Users

✅ **Database Management** - Full CRUD operations on communities
✅ **Search & Filter** - Find communities quickly
✅ **CRM Integration** - One-click push to Google Sheets
✅ **Performance Metrics** - Token counts and costs
✅ **API Access** - All features available via REST API

---

## 📱 Main Screens

### 1. New Consultation
Process client consultations using:
- **Audio Tab**: Upload M4A, MP3, WAV, OGG files (drag & drop supported)
- **Text Tab**: Paste or type consultation transcripts

**Results show:**
- Client information extracted by AI
- Top 5 community recommendations with reasoning
- Performance metrics (time, tokens, cost)

### 2. Community Database
Manage your community listings:
- **View** all 239 communities in searchable table
- **Add** new communities via form
- **Edit** existing community details
- **Delete** communities (with confirmation)
- **Statistics** dashboard (total, avg fee, enhanced)

### 3. Help
Complete user documentation:
- Getting started guide
- Database management instructions
- Understanding results
- Tips & best practices
- Troubleshooting

---

## 🎨 UI Design Highlights

### Modern & Clean
- **Card-based layout** - Information organized in cards
- **Color-coded badges** - Visual status indicators
- **Gradient accents** - Beautiful rank badges (gold, silver, bronze)
- **Hover effects** - Interactive feedback
- **Loading animations** - Smooth transitions

### Responsive Design
- **Desktop** - Full layout with 3 columns
- **Tablet** - 2-column responsive grid
- **Mobile** - Single column stacked layout

### Accessibility
- **Keyboard navigation** - Tab through all elements
- **Clear labels** - Every field labeled
- **Error messages** - Helpful validation feedback
- **Loading states** - Always know what's happening

---

## 🔧 Technical Architecture

### Simple Stack
```
Frontend: HTML5 + CSS3 + Vanilla JavaScript
Backend: Python Flask (lightweight)
Database: Excel file (DataFile_students_OPTIMIZED.xlsx)
AI: Gemini 2.5 Flash API
CRM: Google Sheets API (optional)
```

### No Complexity
- ✅ **Single server** - Just run `python app.py`
- ✅ **No build process** - No Webpack, no compilation
- ✅ **No frameworks** - Pure JavaScript, no React/Vue
- ✅ **No database server** - Direct Excel read/write
- ✅ **No middleware** - Direct API calls

### API Endpoints
```
GET  /                         → Serve UI
GET  /api/health              → Health check
POST /api/process-audio       → Process audio file
POST /api/process-text        → Process text consultation
GET  /api/communities         → Get all communities
GET  /api/communities/:id     → Get specific community
POST /api/communities         → Add new community
PUT  /api/communities/:id     → Update community
DELETE /api/communities/:id   → Delete community
GET  /api/stats               → Get database statistics
```

---

## 💡 Usage Tips

### Audio Recording Tips
1. **Clear audio** - Speak clearly, minimize background noise
2. **Include details** - Budget, timeline, location, care level
3. **File size** - Keep under 50MB for fast uploads
4. **Format** - M4A or MP3 recommended

### Text Consultation Tips
1. **Use dialogue format** - "Agent: ... Client: ..."
2. **Be specific** - Include ZIP code, exact budget, timeline
3. **Keywords matter** - "immediate" = <1 month, "near-term" = 1-3 months

### Database Management Tips
1. **Required fields** - Care level, monthly fee, ZIP code marked with *
2. **Keep updated** - Regularly update waitlist status
3. **Search works** - Filter by ID, care level, ZIP, or status
4. **Batch changes** - Use Excel for bulk updates, UI for individual

---

## 🚨 Common Issues & Solutions

### Server Won't Start
**Error:** `Address already in use`
**Solution:** Port 5000 is occupied
```python
# Edit app.py, change port:
app.run(debug=True, port=5001)
```

### Page Doesn't Load
**Solution:** Check server is running in terminal, look for:
```
* Running on http://localhost:5000
```

### Audio Upload Fails
**Error:** Invalid file type
**Solution:** Only M4A, MP3, WAV, OGG supported

**Error:** File too large
**Solution:** 50MB max - compress or trim your audio

### Processing Takes Long
**Normal:** 30-120 seconds for audio processing
**Reason:** AI extraction + ranking + API calls
**Tip:** Be patient, system has 3-retry logic with exponential backoff

### Database Changes Don't Show
**Solution:** Refresh page (F5) or switch tabs

---

## 🎯 Keyboard Shortcuts

- **Click upload area** = Open file browser
- **Drag & drop** = Upload audio file
- **Escape** = Close modal windows
- **Enter in search** = Search immediately
- **Tab** = Navigate between fields

---

## 📊 What Gets Displayed

### Client Information Card
- Care level needed
- Budget range
- Timeline (immediate/near-term/flexible)
- Location preference
- CRM push status

### Recommendation Cards (1-5)
Each shows:
- **Rank badge** - Position (gold/silver/bronze for top 3)
- **Combined score** - Lower is better (Borda count)
- **Monthly fee** - Base cost
- **Distance** - Miles from preferred location
- **Availability** - Waitlist status
- **AI Reasoning** - Why this community was recommended

### Performance Metrics
- Processing time (seconds)
- Total tokens (input + output)
- Cost breakdown (audio/text/output)
- Number of recommendations

---

## 🔐 Security Considerations

### Current Setup (Local Use)
✅ Designed for **local use only**
✅ No authentication required
✅ Direct file system access
✅ No encryption needed

### For Production Deployment
If you need to deploy publicly, add:
1. **Authentication** - Flask-Login or OAuth
2. **HTTPS** - SSL certificates
3. **CSRF Protection** - Flask-WTF
4. **Rate Limiting** - Flask-Limiter
5. **Production Server** - Gunicorn + Nginx
6. **Real Database** - PostgreSQL instead of Excel

---

## 📚 File Structure

```
d:\CAPSTONE\
├── app.py                    ← Flask server
├── templates\
│   └── index.html            ← Main UI
├── static\
│   ├── css\
│   │   └── style.css         ← Styles
│   └── js\
│       └── app.js            ← Frontend logic
├── uploads\                  ← Audio files (auto-created)
└── output\                   ← Results JSON (auto-created)
```

---

## ✅ Quick Checklist

Before first use:
- [ ] Installed Python 3.9+
- [ ] Ran `pip install -r requirements.txt`
- [ ] Created `.env` with `GEMINI_API_KEY`
- [ ] (Optional) Set up Google Sheets CRM
- [ ] Started server with `python app.py`
- [ ] Opened browser to `http://localhost:5000`

---

## 🎉 You're Ready!

The web UI is designed to be intuitive. If you get stuck:

1. **Check Help tab** in the UI (most comprehensive)
2. **Read WEB_UI_GUIDE.md** (detailed instructions)
3. **Check Flask logs** in terminal (error messages)
4. **Verify .env** configuration (API keys)

**Enjoy your Senior Living Recommendation System!** 🏘️

---

**For detailed documentation:** [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md)
**For main system docs:** [README.md](README.md)
