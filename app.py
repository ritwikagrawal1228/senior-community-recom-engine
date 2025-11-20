"""
Senior Living Community Recommendation System - Web Interface
Simple Flask backend for UI interaction

This system is part of Volley's broader vision for AI-powered solutions.
Volley is led by CEO Kelly Smith.
"""

import os
import json
import sys
from io import StringIO
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import base64
import asyncio
import threading

from main_pipeline_ranking import RankingBasedRecommendationSystem
from google_sheets_integration import push_to_crm
from gemini_live_stream import GeminiLiveStream

# Global variable to store logs
current_logs = []

class LogCapture:
    """Capture print statements to a list while still printing to console"""
    def __init__(self, original_stdout):
        self.logs = []
        self.original_stdout = original_stdout

    def write(self, message):
        # Write to original stdout (console)
        self.original_stdout.write(message)
        self.original_stdout.flush()

        # Also capture to logs
        if message.strip():
            self.logs.append(message.strip())
            global current_logs
            current_logs.append(message.strip())

    def flush(self):
        self.original_stdout.flush()

# Load environment
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Ensure upload folder exists
os.makedirs('uploads', exist_ok=True)
os.makedirs('output', exist_ok=True)

# Language configurations
SUPPORTED_LANGUAGES = {
    'english': {
        'name': 'English',
        'code': 'en',
        'gemini_language_code': 'en-US',
        'instruction_suffix': ' Respond and listen only in English. Ignore any other languages spoken.'
    },
    'hindi': {
        'name': 'Hindi',
        'code': 'hi',
        'gemini_language_code': 'hi-IN',
        'instruction_suffix': ' Respond and listen only in Hindi. Ignore any other languages spoken.'
    },
    'spanish': {
        'name': 'Spanish',
        'code': 'es',
        'gemini_language_code': 'es-ES',
        'instruction_suffix': ' Respond and listen only in Spanish. Ignore any other languages spoken.'
    }
}

# CORS configuration for Google Studio (and other frontends)
allowed_origins_env = os.getenv('ALLOWED_ORIGINS', '*')
if allowed_origins_env == '*':
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    allowed_origins = '*'
else:
    origins_list = [o.strip() for o in allowed_origins_env.split(',') if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins_list}})
    allowed_origins = origins_list

# Initialize recommendation system
recommendation_system = None
active_live_sessions = {}  # Store active live streaming sessions

def get_system():
    """Lazy-load the recommendation system"""
    global recommendation_system
    if recommendation_system is None:
        recommendation_system = RankingBasedRecommendationSystem()
    return recommendation_system

def get_live_system_instruction(language='english'):
    """Get system instruction for live conversation based on language"""
    base_instruction = """
You are an AI assistant helping senior living consultants have natural conversations with potential clients.

Your role:
1. Ask relevant questions to understand client needs for senior living
2. Gather information about: care level needed, budget, timeline, location preferences, special needs
3. Be conversational and empathetic
4. Keep responses concise but natural
5. Focus on one topic at a time
6. Use the updateDashboard function to show recommendations as you gather information

Available tools:
- updateDashboard: Update the consultant's dashboard with client info and recommendations

IMPORTANT: Be conversational, not interrogative. Build rapport first.
"""

    language_config = SUPPORTED_LANGUAGES.get(language.lower(), SUPPORTED_LANGUAGES['english'])
    
    # Make language enforcement ABSOLUTE and strict
    if language.lower() == 'english':
        language_enforcement = """
        
CRITICAL LANGUAGE RULES - ABSOLUTE ENFORCEMENT:
- You MUST ONLY process, transcribe, and respond in English (en-US)
- DO NOT transcribe ANY non-English speech (Hindi, Spanish, etc.) - completely ignore it
- DO NOT respond to non-English input - treat it as if nothing was said
- If you detect non-English speech, DO NOT transcribe it - wait for English input
- All transcriptions MUST be in English characters only
- All your responses MUST be in English only
- If the user speaks in another language, silently ignore it and wait for English speech
- NEVER output Hindi, Spanish, or any other language characters - ONLY English
- The input audio transcription language is set to en-US - respect this absolutely
"""
    else:
        language_enforcement = language_config['instruction_suffix']
    
    return base_instruction + language_enforcement

def get_live_tools():
    """Get tools available for live conversation"""
    return [
        {
            "function_declarations": [
                {
                    "name": "updateDashboard",
                    "description": "Update the consultant dashboard with client information and community recommendations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_info": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "care_level": {"type": "string", "enum": ["Independent Living", "Assisted Living", "Memory Care"]},
                                    "budget": {"type": "number"},
                                    "timeline": {"type": "string", "enum": ["immediate", "near-term", "flexible"]},
                                    "location": {"type": "string"},
                                    "special_needs": {"type": "string"}
                                }
                            },
                            "community_recommendations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "community_id": {"type": "number"},
                                        "community_name": {"type": "string"},
                                        "monthly_fee": {"type": "number"},
                                        "distance_miles": {"type": "number"},
                                        "match_score": {"type": "number"},
                                        "reasoning": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "required": ["client_info"]
                    }
                }
            ]
        }
    ]

# SocketIO event handlers for live streaming
@socketio.on('start_live_session')
def handle_start_live_session(data):
    """Start a new live conversation session"""
    try:
        language = data.get('language', 'english').lower()
        if language not in SUPPORTED_LANGUAGES:
            language = 'english'

        session_id = data.get('session_id', 'default')

        # Create system instruction with language constraint
        system_instruction = get_live_system_instruction(language)
        tools = get_live_tools()
        language_config = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES['english'])

        # Initialize live stream
        live_stream = GeminiLiveStream(system_instruction, lambda msg: handle_live_message(session_id, msg), language_config)

        # Store session
        active_live_sessions[session_id] = {
            'live_stream': live_stream,
            'language': language,
            'system_instruction': system_instruction
        }

        # Start the session in a background thread
        def start_session():
            asyncio.run(live_stream.start())

        thread = threading.Thread(target=start_session, daemon=True)
        thread.start()

        emit('session_started', {
            'session_id': session_id,
            'language': language,
            'status': 'started'
        })

    except Exception as e:
        emit('error', {'message': f'Failed to start session: {str(e)}'})

@socketio.on('send_audio')
def handle_send_audio(data):
    """Handle incoming audio data"""
    try:
        session_id = data.get('session_id', 'default')
        audio_base64 = data.get('audio')
        end_of_turn = data.get('end_of_turn', False)

        if session_id not in active_live_sessions:
            emit('error', {'message': 'Session not found'})
            return

        session = active_live_sessions[session_id]
        live_stream = session['live_stream']

        # Send audio to Gemini in background
        def send_audio_async():
            asyncio.run(live_stream.send_audio(audio_base64, end_of_turn=end_of_turn))

        thread = threading.Thread(target=send_audio_async, daemon=True)
        thread.start()

    except Exception as e:
        emit('error', {'message': f'Failed to send audio: {str(e)}'})

@socketio.on('send_tool_response')
def handle_tool_response(data):
    """Handle tool function responses"""
    try:
        session_id = data.get('session_id', 'default')
        function_id = data.get('function_id')
        response = data.get('response')

        if session_id not in active_live_sessions:
            emit('error', {'message': 'Session not found'})
            return

        session = active_live_sessions[session_id]
        live_stream = session['live_stream']

        # Send tool response in background
        def send_tool_response_async():
            asyncio.run(live_stream.send_tool_response(function_id, response))

        thread = threading.Thread(target=send_tool_response_async, daemon=True)
        thread.start()

    except Exception as e:
        emit('error', {'message': f'Failed to send tool response: {str(e)}'})

@socketio.on('stop_live_session')
def handle_stop_live_session(data):
    """Stop a live conversation session"""
    try:
        session_id = data.get('session_id', 'default')

        if session_id in active_live_sessions:
            session = active_live_sessions[session_id]
            live_stream = session['live_stream']

            # Stop the session
            def stop_session():
                asyncio.run(live_stream.stop())

            thread = threading.Thread(target=stop_session, daemon=True)
            thread.start()

            # Remove from active sessions
            del active_live_sessions[session_id]

        emit('session_stopped', {'session_id': session_id})

    except Exception as e:
        emit('error', {'message': f'Failed to stop session: {str(e)}'})

def handle_live_message(session_id, message):
    """Handle messages from Gemini live stream"""
    try:
        # Forward message to client
        socketio.emit('live_message', {
            'session_id': session_id,
            'message': message
        })
    except Exception as e:
        print(f"Error handling live message: {e}")

@app.route('/')
def index():
    """Serve the main UI"""
    response = app.make_response(render_template('index.html'))
    # Prevent caching of HTML
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'gemini_configured': bool(os.getenv('GEMINI_API_KEY')),
        'sheets_configured': bool(os.getenv('GOOGLE_SPREADSHEET_ID')),
        'allowed_origins': allowed_origins_env
    })

# Optional API key auth for /api/* endpoints (excluding /api/health)
API_KEY = os.getenv('API_KEY')

@app.before_request
def enforce_api_key():
    path = request.path or ''
    if path.startswith('/api/') and path != '/api/health':
        if API_KEY:
            provided = request.headers.get('X-API-Key')
            if provided != API_KEY:
                return jsonify({'error': 'Unauthorized'}), 401

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """Process uploaded audio file"""
    global current_logs
    current_logs = []  # Reset logs

    # Capture stdout while still printing to console
    old_stdout = sys.stdout
    log_capture = LogCapture(old_stdout)
    sys.stdout = log_capture

    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get language parameter (default to English)
        language = request.form.get('language', 'english').lower()
        if language not in SUPPORTED_LANGUAGES:
            language = 'english'

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)

        # Process the audio file
        system = get_system()
        result = system.process_audio_file(filepath, language)

        # Push to CRM if enabled
        push_to_sheets = request.form.get('push_to_crm', 'true').lower() == 'true'
        crm_result = None

        if push_to_sheets and os.getenv('GOOGLE_SPREADSHEET_ID'):
            try:
                crm_result = push_to_crm(result)
            except Exception as e:
                result['crm_error'] = str(e)

        # Add CRM info to result
        if crm_result:
            result['crm_pushed'] = True
            result['consultation_id'] = crm_result['consultation_id']

        # Add language and logs to result
        result['language'] = language
        result['logs'] = log_capture.logs

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'logs': log_capture.logs}), 500
    finally:
        sys.stdout = old_stdout

@app.route('/api/process-text', methods=['POST'])
def process_text():
    """Process text consultation"""
    global current_logs
    current_logs = []  # Reset logs

    # Capture stdout while still printing to console
    old_stdout = sys.stdout
    log_capture = LogCapture(old_stdout)
    sys.stdout = log_capture

    try:
        data = request.get_json()
        text = data.get('text', '')
        language = data.get('language', 'english').lower()

        if language not in SUPPORTED_LANGUAGES:
            language = 'english'

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Process the text
        system = get_system()
        result = system.process_text_input(text)

        # Push to CRM if enabled
        push_to_sheets = data.get('push_to_crm', True)
        crm_result = None

        if push_to_sheets and os.getenv('GOOGLE_SPREADSHEET_ID'):
            try:
                crm_result = push_to_crm(result)
            except Exception as e:
                result['crm_error'] = str(e)

        # Add CRM info to result
        if crm_result:
            result['crm_pushed'] = True
            result['consultation_id'] = crm_result['consultation_id']

        # Add language and logs to result
        result['language'] = language
        result['logs'] = log_capture.logs

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'logs': log_capture.logs}), 500
    finally:
        sys.stdout = old_stdout

@app.route('/api/communities', methods=['GET'])
def get_communities():
    """Get all communities from database"""
    try:
        df = pd.read_excel('DataFile_students_OPTIMIZED.xlsx')

        # Convert to records and handle NaN values
        records = df.to_dict('records')
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        return jsonify({
            'total': len(records),
            'communities': records
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/communities/<int:community_id>', methods=['GET'])
def get_community(community_id):
    """Get specific community by ID"""
    try:
        df = pd.read_excel('DataFile_students_OPTIMIZED.xlsx')
        community = df[df['CommunityID'] == community_id]

        if community.empty:
            return jsonify({'error': 'Community not found'}), 404

        record = community.to_dict('records')[0]
        # Handle NaN values
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None

        return jsonify(record)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/communities', methods=['POST'])
def add_community():
    """Add new community to database"""
    try:
        data = request.get_json()

        # Read existing data
        df = pd.read_excel('DataFile_students_OPTIMIZED.xlsx')

        # Generate new CommunityID
        new_id = int(df['CommunityID'].max() + 1)
        data['CommunityID'] = new_id

        # Append new row
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)

        # Save back to Excel
        df.to_excel('DataFile_students_OPTIMIZED.xlsx', index=False)

        # Reload system to pick up changes
        global recommendation_system
        recommendation_system = None

        return jsonify({
            'success': True,
            'community_id': new_id,
            'message': f'Community {new_id} added successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/communities/<int:community_id>', methods=['PUT'])
def update_community(community_id):
    """Update existing community"""
    try:
        data = request.get_json()

        # Read existing data
        df = pd.read_excel('DataFile_students_OPTIMIZED.xlsx')

        # Find community
        idx = df[df['CommunityID'] == community_id].index
        if len(idx) == 0:
            return jsonify({'error': 'Community not found'}), 404

        # Update row
        for key, value in data.items():
            if key in df.columns and key != 'CommunityID':
                df.at[idx[0], key] = value

        # Save back to Excel
        df.to_excel('DataFile_students_OPTIMIZED.xlsx', index=False)

        # Reload system
        global recommendation_system
        recommendation_system = None

        return jsonify({
            'success': True,
            'message': f'Community {community_id} updated successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/communities/<int:community_id>', methods=['DELETE'])
def delete_community(community_id):
    """Delete community from database"""
    try:
        # Read existing data
        df = pd.read_excel('DataFile_students_OPTIMIZED.xlsx')

        # Find community
        initial_count = len(df)
        df = df[df['CommunityID'] != community_id]

        if len(df) == initial_count:
            return jsonify({'error': 'Community not found'}), 404

        # Save back to Excel
        df.to_excel('DataFile_students_OPTIMIZED.xlsx', index=False)

        # Reload system
        global recommendation_system
        recommendation_system = None

        return jsonify({
            'success': True,
            'message': f'Community {community_id} deleted successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        df = pd.read_excel('DataFile_students_OPTIMIZED.xlsx')

        # Use Type of Service column (same as Care Level)
        care_level_col = 'Type of Service' if 'Type of Service' in df.columns else 'Care Level'

        stats = {
            'total_communities': len(df),
            'care_levels': df[care_level_col].value_counts().to_dict() if care_level_col in df.columns else {},
            'avg_monthly_fee': float(df['Monthly Fee'].mean()) if 'Monthly Fee' in df.columns else 0,
            'enhanced_available': int(df['Enhanced'].sum()) if 'Enhanced' in df.columns else 0,
            'working_with_placement': int(df['Work with Placement?'].sum()) if 'Work with Placement?' in df.columns else 0
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*80)
    print("SENIOR LIVING RECOMMENDATION SYSTEM - WEB INTERFACE")
    print("="*80)
    print("\nStarting server with SocketIO support...")
    print("Open your browser to: http://localhost:5050")
    print("\nPress Ctrl+C to stop the server")
    print("="*80 + "\n")

    socketio.run(app, debug=False, host='0.0.0.0', port=5050, allow_unsafe_werkzeug=True)
