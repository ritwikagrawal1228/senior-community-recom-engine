# Senior Living Recommendation System

An AI-powered recommendation system for senior living placement agents. Uses Gemini AI to analyze client consultations (audio/text) and match them with the best senior living communities from a database.

## Features

### Core Features
- **Audio Consultation Processing** - Upload M4A, MP3, WAV recordings of client consultations
- **Text Input Processing** - Paste consultation transcripts directly  
- **AI-Powered Analysis** - Extracts client requirements (care level, budget, location, timeline)
- **Smart Ranking Engine** - Multi-factor ranking with customizable weights
- **Real-time Voice Agent** - Gemini-powered voice assistant for live client consultations
- **QR Code Sessions** - Generate QR codes for events/kiosks for walk-up consultations

### Admin Features
- **Ranking Weight Configuration** - Adjust importance of different factors
- **Voice Agent Settings** - Configure session limits, timeouts, languages
- **Event Management** - Create time-limited QR codes for events
- **CRM Integration** - Auto-push results to Google Sheets
- **Run Logging** - Track all consultations with performance metrics

### UI/UX
- **iOS 26 "Liquid Glass" Design** - Modern glassmorphic aesthetic
- **Dark/Light Mode** - Automatic theme switching
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Real-time Updates** - WebSocket-based live status updates

## Quick Start

### Prerequisites
- Python 3.10+
- Gemini API Key (get from [Google AI Studio](https://aistudio.google.com/app/apikey))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/senior-living-recommendation.git
cd senior-living-recommendation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment example and configure
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` with your settings:

```env
# Required: OpenRouter API (for audio/text workflow)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-flash

# OpenRouter Attribution (for app visibility and analytics)
# APP_URL: Identifies your app in OpenRouter's public rankings (default: http://localhost:5050)
# APP_NAME: Sets your app's display name (required if using localhost)
APP_URL=http://localhost:5050  # Use your production URL when deployed
APP_NAME=Senior Living Recommendations

# Required: Gemini API (for voice agent - still uses direct API)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_LIVE_MODEL=gemini-2.5-flash-native-audio-preview-09-2025

# Required: Flask
SECRET_KEY=your_secret_key_here

# Optional - for CRM integration
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/service-account.json
```

### Running

```bash
python app.py
```

Open http://localhost:5050 in your browser.

**Default Login:**
- Username: `admin`
- Password: `admin123`

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT INTERFACES                            │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│   Web UI        │   Voice Agent   │   API                           │
│   (index.html)  │   (QR Sessions) │   (/api/*)                      │
└────────┬────────┴────────┬────────┴────────┬────────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FLASK APP (app.py)                          │
│   • Authentication    • File Upload    • WebSocket (Socket.IO)      │
└────────┬────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PROCESSING PIPELINE                             │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│ Audio Analyzer  │  Gemini AI      │  Voice Agent                    │
│ (transcription) │  (extraction)   │  (real-time)                    │
└────────┬────────┴────────┬────────┴────────┬────────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       RANKING ENGINE                                 │
│   • Rule-based scoring    • AI holistic ranking    • Aggregation    │
└────────┬────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│ Community DB    │  Run Logs DB    │  Google Sheets CRM              │
│ (Excel/CSV)     │  (SQLite)       │  (via API)                      │
└─────────────────┴─────────────────┴─────────────────────────────────┘
```

## Voice Agent

The real-time voice agent allows clients to speak naturally about their needs:

1. **Generate QR Code** - Admin creates a session QR code
2. **Client Scans** - Opens voice consultation page
3. **Join Call** - Client clicks to start conversation
4. **AI Conversation** - Gemini collects requirements through natural dialogue
5. **Automatic Search** - When ready, triggers the recommendation pipeline
6. **Spoken Results** - AI speaks the top community recommendations

### Voice Agent Features
- Uses Gemini 2.5 Flash Native Audio for low-latency voice
- Supports English, Hindi, and Spanish
- Handles interruptions naturally
- Automatically extracts structured data from conversation

## API Endpoints

### Processing
- `POST /api/process-audio` - Process audio file
- `POST /api/process-text` - Process text input

### Data
- `GET /api/communities` - List all communities
- `GET /api/run-logs` - Get processing history
- `GET /api/performance-stats` - Get performance metrics

### Admin
- `GET /api/admin/config` - Get admin configuration
- `POST /api/admin/voice-settings` - Update voice settings
- `POST /api/admin/ranking-weights` - Update ranking weights
- `POST /api/admin/events` - Create event QR codes

### Voice Agent
- `GET /voice-session/<session_id>` - Voice consultation page
- `POST /api/voice-session` - Create voice session
- `GET /api/voice-session/<id>/qr` - Get QR code for session

## File Structure

```
├── app.py                    # Main Flask application
├── voice_agent.py            # Gemini real-time voice agent
├── ranking_engine.py         # Multi-factor ranking system
├── gemini_audio_processor.py # Audio transcription & analysis
├── audio_analyzer.py         # Audio file handling
├── google_sheets_integration.py  # CRM integration
├── admin_config.py           # Admin configuration management
├── run_logs_db.py            # Run logging database
├── templates/
│   ├── index.html            # Main UI
│   ├── login.html            # Login page
│   └── voice_session.html    # Voice agent interface
├── static/
│   ├── css/style.css         # Styles (iOS 26 Liquid Glass)
│   └── js/app.js             # Frontend JavaScript
├── .env.example              # Environment template
└── requirements.txt          # Python dependencies
```

## Technology Stack

- **Backend**: Python, Flask, Flask-SocketIO
- **AI**: Google Gemini 2.5 Flash, Gemini Live API
- **Database**: SQLite (run logs), Excel/CSV (communities)
- **Frontend**: Vanilla JS, CSS3 (Glassmorphism)
- **Real-time**: WebSockets via Socket.IO

## Performance

- **Processing Time**: ~2-3 minutes per consultation
- **Accuracy**: 93%+ time reduction vs manual matching
- **Voice Latency**: <500ms response time
- **Concurrent Sessions**: Configurable (default: 10)

## License

MIT License - See LICENSE file for details.

## Support

For issues and feature requests, please open a GitHub issue.

