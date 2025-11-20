# 📦 Files to Include in Zip

## ✅ Include These Files/Folders:

### Core Application
- `app.py` - Backend Flask server
- `requirements.txt` - Python dependencies
- `README.md` - Main documentation
- `CLIENT_SETUP.md` - **START HERE** - Client setup instructions
- `.env.example` - Environment variable template
- `START.sh` - Mac/Linux startup script
- `START.bat` - Windows startup script

### Python Backend Files
- `gemini_audio_processor.py`
- `gemini_live_stream.py`
- `gemini_websocket_proxy.py`
- `main_pipeline_ranking.py`
- `ranking_engine.py`
- `community_filter_engine_enhanced.py`
- `location_resolver.py`
- `geocoding_utils.py`
- `google_sheets_integration.py`
- `run_consultation.py`
- `setup_existing_sheet.py`

### Frontend Files
- `.studio_import/` folder (entire folder)
  - `package.json`
  - `vite.config.ts`
  - `App.tsx`
  - `components/` folder
  - `types.ts`
  - `QUICK_START.md`
  - All other frontend files

### Data Files
- `DataFile_students_OPTIMIZED.xlsx` - Community database

### Documentation
- `GOOGLE_SHEETS_SETUP.md`
- `WEB_UI_GUIDE.md`
- `RANKING_SYSTEM_README.md`

### Static Files
- `static/` folder
- `templates/` folder

## ❌ Exclude These:

- `venv/` - Virtual environment (client will create their own)
- `.studio_import/node_modules/` - Node modules (client will install)
- `uploads/` - Uploaded files (client will generate)
- `output/` - Output files (client will generate)
- `.env` - Environment file with API keys (use .env.example instead)
- `__pycache__/` - Python cache files
- `.git/` - Git repository (if present)
- `*.log` - Log files

## 📋 Pre-Zip Checklist:

- [ ] Created `CLIENT_SETUP.md` with instructions
- [ ] Created `.env.example` (no real API keys)
- [ ] Created `START.sh` and `START.bat` scripts
- [ ] Removed `venv/` folder
- [ ] Removed `.studio_import/node_modules/` folder
- [ ] Removed `.env` file (if exists)
- [ ] Removed `uploads/` contents (keep folder structure)
- [ ] Removed `output/` contents (keep folder structure)
- [ ] Tested that zip extracts correctly
- [ ] Verified all required files are included

