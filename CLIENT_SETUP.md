# 🚀 Client Setup Instructions
## AI Senior Living Placement Assistant

### ⚠️ IMPORTANT: Access the Frontend Only
**Always open:** `http://localhost:3000` (Frontend - This is what you use!)  
**Never open:** `http://localhost:5050` (Backend - Internal only, don't use this!)

---

## 📦 Prerequisites

Before starting, ensure you have:
- **Python 3.9 or higher** installed ([Download](https://www.python.org/downloads/))
- **Node.js 18+ and npm** installed ([Download](https://nodejs.org/))
- **Gemini API Key** (Get one at: https://ai.google.dev/)

---

## 🔧 Installation Steps

### Step 1: Extract the Zip File
Extract all files to a folder on your computer (e.g., `senior-community-recom-engine`)

### Step 2: Set Up Backend (Python)

1. **Open Terminal/Command Prompt** in the extracted folder

2. **Create Virtual Environment:**
   ```bash
   python3 -m venv venv
   ```
   (On Windows: `python -m venv venv`)

3. **Activate Virtual Environment:**
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```

4. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set Up Environment Variables:**
   - Copy `.env.example` to `.env`
   - Open `.env` file and add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

### Step 3: Set Up Frontend (React/Vite)

1. **Navigate to Frontend Folder:**
   ```bash
   cd .studio_import
   ```

2. **Install Node Dependencies:**
   ```bash
   npm install
   ```

3. **Go Back to Root Folder:**
   ```bash
   cd ..
   ```

---

## ▶️ Running the Application

### Option A: Use Startup Scripts (Easiest)

**Mac/Linux:**
```bash
chmod +x START.sh
./START.sh
```

**Windows:**
Double-click `START.bat` or run:
```bash
START.bat
```

### Option B: Manual Start (Two Terminal Windows)

#### Terminal 1: Start Backend Server
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Start backend
python3 app.py
```

**You should see:** `Running on http://127.0.0.1:5050`  
**✅ Keep this terminal open!**

#### Terminal 2: Start Frontend Server
```bash
# Navigate to frontend folder
cd .studio_import

# Start frontend
npm run dev
```

**You should see:** `Local: http://localhost:3000`  
**✅ Keep this terminal open too!**

---

## 🌐 Accessing the Application

### ✅ CORRECT: Open This URL
**Open your web browser and go to:**
```
http://localhost:3000
```

This is the **Frontend** - the user interface you'll interact with.

### ❌ WRONG: Don't Open This
```
http://localhost:5050  ← Don't use this! (This is the backend API)
```

---

## 🎯 Quick Start Guide

1. **Open:** `http://localhost:3000` in your browser
2. **You'll see:** Landing page with two options:
   - **"Launch AI Placement Assistant"** - Start using the tool
   - **"Product Vision & Playbook"** - Learn about the system

3. **Click "Launch AI Placement Assistant"**
4. **Select Language** (English/Spanish/Hindi - Coming Soon)
5. **Click "Start Call"** to begin a live consultation
   - OR use **"Upload"** button to process an audio file
   - OR use **"Process Text"** to paste a consultation transcript

---

## 📋 Features

- **Live Audio Consultation:** Real-time AI-powered conversation with clients
- **Audio File Processing:** Upload MP3, WAV, M4A, OGG, WebM, or FLAC files
- **Text Input:** Paste consultation transcripts for processing
- **Community Recommendations:** AI-ranked matches with detailed explanations
- **Client Profile Management:** Automatic extraction and display of client information
- **CRM Integration:** Export results to Excel/CRM systems

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to backend"
**Solution:** 
- Make sure Terminal 1 (backend) is running on port 5050
- Check that you see `Running on http://127.0.0.1:5050` in the backend terminal

### Issue: "Page not found" or blank page
**Solution:** 
- Make sure Terminal 2 (frontend) is running on port 3000
- Check that you're accessing `http://localhost:3000` (not 5050!)
- Look for `Local: http://localhost:3000` in the frontend terminal

### Issue: "API Error" or "Failed to fetch"
**Solution:** 
- Verify both servers are running (check both terminals)
- Check that `.env` file has your `GEMINI_API_KEY` set correctly
- Make sure you're accessing the frontend (port 3000), not backend (port 5050)
- Check browser console for detailed errors (F12 → Console tab)

### Issue: Port 3000 or 5050 already in use
**Solution:**
- Close any other applications using these ports
- Or change ports in:
  - Backend: Edit `app.py` (line with `port=5050`)
  - Frontend: Edit `.studio_import/vite.config.ts` (line with `port: 3000`)

### Issue: "Module not found" or import errors
**Solution:**
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- For frontend: `cd .studio_import && npm install`

### Issue: Audio file upload fails
**Solution:**
- Check file format (supported: MP3, WAV, M4A, OGG, WebM, FLAC)
- Check file size (max 50MB)
- Ensure backend server is running

---

## 📝 Summary

- **Frontend URL:** `http://localhost:3000` ← **USE THIS ONE!**
- **Backend URL:** `http://localhost:5050` ← Internal only, don't access directly
- **Two servers must run:** Backend (Terminal 1) + Frontend (Terminal 2)
- **Always start backend first**, then frontend
- **Use startup scripts** (`START.sh` or `START.bat`) for easiest setup

---

## 📚 Additional Documentation

- `README.md` - Full system documentation
- `QUICK_START.md` - Quick reference guide (in `.studio_import/` folder)
- `GOOGLE_SHEETS_SETUP.md` - Optional CRM integration setup

---

## 💡 Need Help?

If you encounter issues:
1. Check that both terminals show the servers are running
2. Verify you're accessing `http://localhost:3000` (not 5050)
3. Check browser console for errors (F12 → Console tab)
4. Ensure `.env` file has valid `GEMINI_API_KEY`
5. Review the troubleshooting section above

---

## 🎓 Project Information

**Project:** AI Senior Living Placement Assistant  
**Subtitle:** AI‑Powered Client Intake and Community Matching System  
**Project Team:** Shivam Sharma, Ritwik Agrawal, Manu Jain, Yu Chen Lin (Ryan)  
**Faculty Advisor:** Professor Elizabeth Mohr  
**Client Partner:** Neil Russell, Culina Health  

---

**Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Production Ready ✅

