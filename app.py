"""
Senior Living Community Recommendation System - Web Interface
Simple Flask backend for UI interaction

This system is part of Volley's broader vision for AI-powered solutions.
Volley is led by CEO Kelly Smith.
"""

# Standard library imports
import os
import json
import sys
import base64
import asyncio
import threading
import logging
from io import StringIO
from datetime import datetime

# Third-party imports
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, flash
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# Local imports
from main_pipeline_ranking import RankingBasedRecommendationSystem
from google_sheets_integration import push_to_crm
from voice_agent import (
    GeminiVoiceAgent, 
    create_session, 
    get_session, 
    end_session, 
    active_sessions,
    get_active_session_count,
    get_all_sessions_info,
    cleanup_expired_sessions,
    SAMPLE_RATE
)
import voice_agent  # For dynamic config updates
from admin_config import admin_config, Event
import run_logs_db  # For persistent run logging
import re

# Helper functions for voice agent budget extraction
def extract_budget_min(budget_str: str) -> int:
    """Extract minimum budget from a string like '$3,000 to $5,000' or '3000-5000'"""
    if not budget_str:
        return 0
    
    # Remove $ and commas
    cleaned = re.sub(r'[$,]', '', str(budget_str))
    
    # Find all numbers
    numbers = re.findall(r'\d+', cleaned)
    
    if numbers:
        return int(numbers[0])
    return 0


def extract_budget_max(budget_str: str) -> int:
    """Extract maximum budget from a string like '$3,000 to $5,000' or '3000-5000'"""
    if not budget_str:
        return 10000  # Default max
    
    # Remove $ and commas
    cleaned = re.sub(r'[$,]', '', str(budget_str))
    
    # Find all numbers
    numbers = re.findall(r'\d+', cleaned)
    
    if len(numbers) >= 2:
        return int(numbers[1])
    elif numbers:
        # If only one number, assume it's a max with some flexibility
        return int(numbers[0]) + 1000
    return 10000


# Initialize run logs database
run_logs_db.init_database()

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize Socket.IO for real-time voice communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Simple user database (in production, use a real database)
USERS = {
    'admin': 'admin123',
    'consultant': 'consultant123',
    'manager': 'manager123'
}

# Admin users (can access admin panel)
ADMIN_USERS = {'admin', 'manager'}

def is_admin():
    """Check if current user is an admin"""
    return session.get('username') in ADMIN_USERS

def admin_required(f):
    """Decorator for admin-only routes"""
    def decorated_function(*args, **kwargs):
        # Check if this is an API request (AJAX/fetch)
        is_api_request = request.path.startswith('/api/') or request.headers.get('Content-Type') == 'application/json'
        
        if 'username' not in session:
            if is_api_request:
                return jsonify({'error': 'Not logged in. Please log in as admin or manager.'}), 401
            return redirect(url_for('login'))
        if session['username'] not in ADMIN_USERS:
            return jsonify({'error': f'Admin access required. You are logged in as "{session["username"]}", but you need to be logged in as "admin" or "manager".'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Voice agent instances per session
voice_agents: dict = {}

# Authentication decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

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

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
@login_required
def index():
    """Serve the main UI"""
    response = app.make_response(render_template('index.html'))
    # Prevent caching of HTML
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in USERS and USERS[username] == password:
            session['username'] = username
            session['role'] = 'admin' if username == 'admin' else 'user'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    session.pop('username', None)
    session.pop('role', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

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
@login_required
def process_audio():
    """Process uploaded audio file"""
    global current_logs
    current_logs = []  # Reset logs
    logger.info("Processing audio file request")

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

        # Validate file format
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac'}
        allowed_mime_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
            'audio/m4a', 'audio/x-m4a', 'audio/ogg', 'audio/webm', 'audio/flac'
        }
        
        filename_lower = file.filename.lower()
        file_ext = None
        for ext in allowed_extensions:
            if filename_lower.endswith(ext):
                file_ext = ext
                break
        
        if not file_ext and file.content_type not in allowed_mime_types:
            return jsonify({
                'error': f'Unsupported audio format. Supported formats: MP3, WAV, M4A, OGG, WebM, FLAC. Your file: {file.filename} (type: {file.content_type or "unknown"})'
            }), 400

        # Validate file size (50MB max)
        if file.content_length and file.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({
                'error': f'File too large. Maximum file size is 50MB. Your file: {file.content_length / 1024 / 1024:.2f}MB'
            }), 400

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
        
        # For audio, the transcription is not directly available (Gemini processes audio directly)
        # But we can note that it was processed from audio
        result['transcription'] = result.get('transcription', f"[Audio processed from: {filename}]")
        result['input_type'] = 'audio'
        
        # Generate run_id and save to database
        run_id = run_logs_db.generate_run_id()
        result['run_id'] = run_id
        
        # Extract performance metrics
        perf = result.get('performance_metrics', {})
        timings = perf.get('timings', {})
        tokens = perf.get('token_counts', {})
        costs = perf.get('costs', {})
        
        # Save run log
        run_logs_db.save_run_log(
            run_id=run_id,
            input_type='audio',
            language=language,
            input_filename=filename,
            input_size_bytes=os.path.getsize(filepath) if os.path.exists(filepath) else None,
            transcription=result.get('transcription'),
            client_info=result.get('client_info'),
            recommendations=result.get('recommendations'),
            processing_time_seconds=timings.get('e2e_total'),
            tokens_used=tokens.get('total_tokens'),
            api_cost=costs.get('total_cost'),
            api_calls=perf.get('api_calls'),
            timing_breakdown=timings,
            status='completed',
            crm_pushed=result.get('crm_pushed', False),
            consultation_id=result.get('consultation_id'),
            username=session.get('username')
        )

        logger.info("Processing completed successfully")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in processing: {e}", exc_info=True)
        # Save failed run
        run_logs_db.save_run_log(
            run_id=run_logs_db.generate_run_id(),
            input_type='audio',
            language=request.form.get('language', 'english'),
            status='failed',
            error_message=str(e),
            username=session.get('username')
        )
        return jsonify({'error': str(e), 'logs': log_capture.logs}), 500
    finally:
        sys.stdout = old_stdout

@app.route('/api/process-text', methods=['POST'])
@login_required
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
        
        # For text input, the input IS the transcription
        result['transcription'] = text
        result['input_type'] = 'text'
        
        # Generate run_id and save to database
        run_id = run_logs_db.generate_run_id()
        result['run_id'] = run_id
        
        # Extract performance metrics
        perf = result.get('performance_metrics', {})
        timings = perf.get('timings', {})
        tokens = perf.get('token_counts', {})
        costs = perf.get('costs', {})
        
        # Save run log
        run_logs_db.save_run_log(
            run_id=run_id,
            input_type='text',
            language=language,
            transcription=text,  # For text input, the input IS the transcription
            client_info=result.get('client_info'),
            recommendations=result.get('recommendations'),
            processing_time_seconds=timings.get('e2e_total'),
            tokens_used=tokens.get('total_tokens'),
            api_cost=costs.get('total_cost'),
            api_calls=perf.get('api_calls'),
            timing_breakdown=timings,
            status='completed',
            crm_pushed=result.get('crm_pushed', False),
            consultation_id=result.get('consultation_id'),
            username=session.get('username')
        )

        logger.info("Processing completed successfully")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in processing: {e}", exc_info=True)
        # Save failed run
        run_logs_db.save_run_log(
            run_id=run_logs_db.generate_run_id(),
            input_type='text',
            language=data.get('language', 'english') if 'data' in locals() else 'english',
            status='failed',
            error_message=str(e),
            username=session.get('username')
        )
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

        # Convert Yes/No columns to numeric for counting
        enhanced_count = 0
        if 'Enhanced' in df.columns:
            enhanced_count = int((df['Enhanced'].str.lower() == 'yes').sum())

        placement_count = 0
        if 'Work with Placement?' in df.columns:
            placement_count = int((df['Work with Placement?'].str.lower() == 'yes').sum())

        # Calculate average monthly fee, filtering out non-numeric values
        avg_monthly_fee = 0
        if 'Monthly Fee' in df.columns:
            # Convert to numeric, coercing errors to NaN
            numeric_fees = pd.to_numeric(df['Monthly Fee'], errors='coerce')
            avg_monthly_fee = float(numeric_fees.mean()) if not numeric_fees.empty else 0

        stats = {
            'total_communities': len(df),
            'care_levels': df[care_level_col].value_counts().to_dict() if care_level_col in df.columns else {},
            'avg_monthly_fee': avg_monthly_fee,
            'enhanced_available': enhanced_count,
            'working_with_placement': placement_count
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-crm', methods=['POST'])
def update_crm():
    """Update CRM with current consultation data - Coming Soon"""
    try:
        data = request.get_json()
        client_profile = data.get('clientProfile', {})
        recommendations = data.get('recommendations', [])
        
        # Return "coming soon" message
        return jsonify({
            'success': False,
            'message': 'CRM integration coming soon',
            'note': 'Google Sheets CRM integration will be available in a future update'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-email-client', methods=['POST'])
def send_email_client():
    """Send email to client with recommendations"""
    try:
        data = request.get_json()
        client_profile = data.get('clientProfile', {})
        recommendations = data.get('recommendations', [])
        summary = data.get('summary', '')

        client_email = client_profile.get('email', '')
        if not client_email:
            return jsonify({'error': 'Client email address not found in profile'}), 400

        # Check if email is configured
        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = os.getenv('SMTP_PORT', '587')
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_user)

        if not smtp_host or not smtp_user or not smtp_password:
            # Return success but log that email wasn't actually sent
            return jsonify({
                'success': True,
                'message': f'Email prepared for {client_email}',
                'note': 'Email not sent: SMTP not configured. Please set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env',
                'preview': {
                    'to': client_email,
                    'subject': f'Senior Living Recommendations for {client_profile.get("name", "you")}',
                    'recommendations_count': len(recommendations)
                }
            })

        # Build email content
        email_subject = f'Senior Living Recommendations for {client_profile.get("name", "you")}'
        email_body = f"""
Dear {client_profile.get('name', 'Client')},

Thank you for your interest in finding the perfect senior living community. Based on our consultation, here are your personalized recommendations:

"""
        for rec in recommendations:
            email_body += f"""
{rec.get('name', 'Community')}
Price: {rec.get('price', 'Contact for pricing')}
Reason: {rec.get('reason', '')}
"""

        email_body += f"""

Summary: {summary}

Please contact us if you have any questions or would like to schedule a tour.

Best regards,
Senior Living Placement Team
"""

        # Try to send email using smtplib
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = client_email
            msg['Subject'] = email_subject
            msg.attach(MIMEText(email_body, 'plain'))

            server = smtplib.SMTP(smtp_host, int(smtp_port))
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()

            return jsonify({
                'success': True,
                'message': f'Email sent successfully to {client_email}'
            })
        except Exception as email_error:
            return jsonify({
                'error': f'Failed to send email: {str(email_error)}',
                'message': 'Please check your SMTP configuration'
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-email-manager', methods=['POST'])
def send_email_manager():
    """Send email to manager for review"""
    try:
        data = request.get_json()
        client_profile = data.get('clientProfile', {})
        recommendations = data.get('recommendations', [])
        summary = data.get('summary', '')

        # Get manager email from environment or config
        manager_email = os.getenv('MANAGER_EMAIL', '')
        if not manager_email:
            return jsonify({
                'error': 'Manager email not configured',
                'message': 'Please set MANAGER_EMAIL in .env file'
            }), 400

        # Check if email is configured
        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = os.getenv('SMTP_PORT', '587')
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_user)

        if not smtp_host or not smtp_user or not smtp_password:
            return jsonify({
                'success': True,
                'message': f'Email prepared for {manager_email}',
                'note': 'Email not sent: SMTP not configured. Please set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env',
                'preview': {
                    'to': manager_email,
                    'subject': f'Review Required: Consultation for {client_profile.get("name", "Client")}',
                    'recommendations_count': len(recommendations)
                }
            })

        # Build email content for manager
        email_subject = f'Review Required: Consultation for {client_profile.get("name", "Client")}'
        email_body = f"""
Manager Review Request

Client Information:
- Name: {client_profile.get('name', 'Unknown')}
- Care Level: {client_profile.get('careLevel', 'Not specified')}
- Budget: {client_profile.get('budget', 'Not specified')}
- Location: {client_profile.get('location', 'Not specified')}
- Timeline: {client_profile.get('timeline', 'Not specified')}

Recommendations Generated: {len(recommendations)}

Top Recommendations:
"""
        for rec in recommendations[:3]:  # Top 3
            email_body += f"""
{rec.get('name', 'Community')} - {rec.get('reason', '')}
"""

        email_body += f"""

Summary: {summary}

Please review and provide feedback.

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # Try to send email using smtplib
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = manager_email
            msg['Subject'] = email_subject
            msg.attach(MIMEText(email_body, 'plain'))

            server = smtplib.SMTP(smtp_host, int(smtp_port))
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()

            return jsonify({
                'success': True,
                'message': f'Email sent successfully to {manager_email}'
            })
        except Exception as email_error:
            return jsonify({
                'error': f'Failed to send email: {str(email_error)}',
                'message': 'Please check your SMTP configuration'
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-excel', methods=['POST'])
def update_excel():
    """Update Excel sheet with consultation data"""
    try:
        data = request.get_json()
        client_profile = data.get('clientProfile', {})
        recommendations = data.get('recommendations', [])
        summary = data.get('summary', '')

        # Read existing Excel file
        excel_file = 'DataFile_students_OPTIMIZED.xlsx'
        if not os.path.exists(excel_file):
            return jsonify({'error': f'Excel file not found: {excel_file}'}), 404

        # Read Excel file
        df = pd.read_excel(excel_file)

        # Create a separate consultations log file instead of modifying the main database
        consultations_file = 'consultations_log.xlsx'
        
        # Create consultation log entry
        consultation_data = {
            'Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'Client Name': [client_profile.get('name', 'Unknown')],
            'Budget': [client_profile.get('budget', '')],
            'Location': [client_profile.get('location', '')],
            'Care Level': [client_profile.get('careLevel', '')],
            'Timeline': [client_profile.get('timeline', '')],
            'Top Recommendation': [recommendations[0].get('name', '') if recommendations else ''],
            'Summary': [summary[:500]]  # Limit summary length
        }

        # Append to consultations log
        if os.path.exists(consultations_file):
            existing_df = pd.read_excel(consultations_file)
            new_df = pd.DataFrame(consultation_data)
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            updated_df = pd.DataFrame(consultation_data)

        # Save consultations log
        updated_df.to_excel(consultations_file, index=False)

        return jsonify({
            'success': True,
            'message': 'Consultation logged to Excel successfully',
            'file': consultations_file,
            'row_added': len(updated_df)
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return jsonify({
            'error': str(e),
            'details': error_details
        }), 500


# ========================================
# Voice Agent Routes
# ========================================

@app.route('/api/voice/create-session', methods=['POST'])
@login_required
def create_voice_session():
    """Create a new voice session and return session ID with QR code URL"""
    try:
        data = request.get_json() or {}
        language = data.get('language', 'english')
        
        # Create session (now returns tuple)
        session_id, error = create_session()
        
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'active_sessions': get_active_session_count(),
                'max_sessions': admin_config.get_max_sessions()
            }), 429  # Too Many Requests
        
        voice_session = get_session(session_id)
        
        if voice_session:
            voice_session.client_info['language'] = language
            voice_session.client_info['created_by'] = session.get('username', 'unknown')
            
            # Persist session to database for QR code persistence
            try:
                import json
                from datetime import datetime
                conn = run_logs_db.get_connection()
                cursor = conn.cursor()
                
                # Check if voice_sessions table exists, create if not
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS voice_sessions (
                        session_id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        status TEXT DEFAULT 'waiting',
                        language TEXT DEFAULT 'english',
                        created_by TEXT,
                        session_data JSON
                    )
                ''')
                
                # Save session
                expires_at = voice_session.expires_at.isoformat() if voice_session.expires_at else None
                cursor.execute('''
                    INSERT OR REPLACE INTO voice_sessions 
                    (session_id, expires_at, status, language, created_by, session_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    expires_at,
                    voice_session.status,
                    language,
                    session.get('username', 'unknown'),
                    json.dumps({
                        'session_url': f"{request.host_url.rstrip('/')}/voice-session/{session_id}",
                        'client_info': voice_session.client_info
                    })
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to persist voice session: {e}")
        
        # Generate URLs
        base_url = request.host_url.rstrip('/')
        session_url = f"{base_url}/voice-session/{session_id}"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={session_url}"
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'session_url': session_url,
            'qr_url': qr_url,
            'status': 'waiting',
            'expires_in_seconds': voice_session.time_remaining() if voice_session else 1800,
            'active_sessions': get_active_session_count(),
            'max_sessions': admin_config.get_max_sessions()
        })
        
    except Exception as e:
        logger.error(f"Error creating voice session: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/session/<session_id>', methods=['GET'])
def get_voice_session_status(session_id):
    """Get the status of a voice session"""
    try:
        voice_session = get_session(session_id)
        
        if not voice_session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session_id,
            'status': voice_session.status,
            'created_at': voice_session.created_at.isoformat(),
            'client_info': voice_session.client_info,
            'conversation_count': len(voice_session.conversation_history),
            'has_recommendations': len(voice_session.recommendations) > 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/session/<session_id>/end', methods=['POST'])
def end_voice_session(session_id):
    """End a voice session"""
    try:
        # Cleanup voice agent if exists
        if session_id in voice_agents:
            agent = voice_agents[session_id]
            asyncio.run(agent.disconnect())
            del voice_agents[session_id]
        
        # End session
        end_session(session_id)
        
        return jsonify({'success': True, 'message': 'Session ended'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/sessions', methods=['GET'])
@login_required
def list_voice_sessions():
    """List all active voice sessions (admin endpoint)"""
    try:
        sessions = get_all_sessions_info()
        return jsonify({
            'success': True,
            'active_count': get_active_session_count(),
            'max_sessions': admin_config.get_max_sessions(),
            'sessions': sessions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/cleanup', methods=['POST'])
@login_required  
def cleanup_sessions():
    """Manually trigger cleanup of expired sessions"""
    try:
        cleaned = cleanup_expired_sessions()
        return jsonify({
            'success': True,
            'cleaned_count': cleaned,
            'remaining_active': get_active_session_count()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# Run Logs API Routes
# ========================================

@app.route('/api/run-logs', methods=['GET'])
@login_required
def get_run_logs():
    """Get recent run logs with optional filtering"""
    try:
        limit = request.args.get('limit', 50, type=int)
        type_filter = request.args.get('type', 'all')
        status_filter = request.args.get('status', 'all')
        username = session.get('username')
        
        runs = run_logs_db.get_recent_runs(limit=limit, username=username)
        
        # Apply filters
        if type_filter != 'all':
            runs = [r for r in runs if r.get('input_type') == type_filter]
        if status_filter != 'all':
            runs = [r for r in runs if r.get('status') == status_filter]
        
        return jsonify({
            'runs': runs,
            'total': len(runs)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-logs/<run_id>', methods=['GET'])
@login_required
def get_run_log(run_id):
    """Get specific run log with full details including transcription"""
    try:
        run = run_logs_db.get_run_log(run_id)
        if not run:
            return jsonify({'error': 'Run not found'}), 404
        return jsonify(run)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-logs/stats', methods=['GET'])
@login_required
def get_run_stats():
    """Get performance statistics for charts"""
    try:
        days = request.args.get('days', 30, type=int)
        stats = run_logs_db.get_performance_stats(days=days)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-logs/history/processing-time', methods=['GET'])
@login_required
def get_processing_time_history():
    """Get processing time history for mini-chart"""
    try:
        limit = request.args.get('limit', 20, type=int)
        times = run_logs_db.get_processing_time_history(limit=limit)
        return jsonify({'data': times})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-logs/history/tokens', methods=['GET'])
@login_required
def get_token_history():
    """Get token usage history for mini-chart"""
    try:
        limit = request.args.get('limit', 20, type=int)
        tokens = run_logs_db.get_token_history(limit=limit)
        return jsonify({'data': tokens})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-logs/history/cost', methods=['GET'])
@login_required
def get_cost_history():
    """Get API cost history for mini-chart"""
    try:
        limit = request.args.get('limit', 20, type=int)
        costs = run_logs_db.get_cost_history(limit=limit)
        return jsonify({'data': costs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========================================
# Admin Panel Routes
# ========================================

@app.route('/api/admin/config', methods=['GET'])
@admin_required
def get_admin_config():
    """Get full admin configuration"""
    try:
        config = admin_config.get_full_config()
        config['is_admin'] = True
        config['current_user'] = session.get('username')
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/voice-settings', methods=['GET', 'POST'])
@admin_required
def admin_voice_settings():
    """Get or update voice agent settings"""
    try:
        if request.method == 'GET':
            return jsonify(admin_config.get_voice_settings())
        
        data = request.get_json()
        user = session.get('username', 'unknown')
        
        # Update voice_agent module's config dynamically
        if 'max_concurrent_sessions' in data:
            voice_agent.MAX_CONCURRENT_SESSIONS = data['max_concurrent_sessions']
        if 'session_timeout_minutes' in data:
            voice_agent.SESSION_TIMEOUT_MINUTES = data['session_timeout_minutes']
        
        updated = admin_config.update_voice_settings(data, user)
        return jsonify({'success': True, 'settings': updated})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/ranking-weights', methods=['GET', 'POST'])
@admin_required
def admin_ranking_weights():
    """Get or update ranking weights"""
    try:
        if request.method == 'GET':
            return jsonify({
                'weights': admin_config.get_ranking_weights(),
                'presets': admin_config.get_weight_presets()
            })
        
        data = request.get_json()
        user = session.get('username', 'unknown')
        
        if 'preset' in data:
            # Apply a preset
            updated = admin_config.apply_weight_preset(data['preset'], user)
        elif 'reset' in data and data['reset']:
            # Reset to defaults
            updated = admin_config.reset_ranking_weights(user)
        else:
            # Update individual weights
            updated = admin_config.update_ranking_weights(data.get('weights', {}), user)
        
        return jsonify({'success': True, 'weights': updated})
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/system-settings', methods=['GET', 'POST'])
@admin_required
def admin_system_settings():
    """Get or update system settings"""
    try:
        if request.method == 'GET':
            return jsonify(admin_config.get_system_settings())
        
        data = request.get_json()
        user = session.get('username', 'unknown')
        updated = admin_config.update_system_settings(data, user)
        return jsonify({'success': True, 'settings': updated})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/events', methods=['GET', 'POST'])
@admin_required
def admin_events():
    """List events or create new event"""
    try:
        if request.method == 'GET':
            events = admin_config.get_all_events()
            base_url = request.host_url.rstrip('/')
            
            events_with_qr = []
            for e in events:
                event_dict = e.to_dict()
                # Generate single QR code URL for this event
                session_url = f"{base_url}/event/{e.event_id}"
                event_dict['session_url'] = session_url
                event_dict['qr_url'] = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={session_url}"
                events_with_qr.append(event_dict)
            
            return jsonify({
                'events': events_with_qr,
                'total': len(events),
                'active': len([e for e in events if e.is_active and not e.is_expired()])
            })
        
        # Create new event
        data = request.get_json()
        user = session.get('username', 'unknown')
        
        event = admin_config.create_event(
            name=data['name'],
            description=data.get('description', ''),
            max_concurrent_sessions=data.get('max_concurrent_sessions', 10),
            duration_hours=data.get('duration_hours', 0),
            duration_minutes=data.get('duration_minutes', 60),
            user=user
        )
        
        # Generate single QR code URL
        base_url = request.host_url.rstrip('/')
        session_url = f"{base_url}/event/{event.event_id}"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={session_url}"
        
        return jsonify({
            'success': True,
            'event': event.to_dict(),
            'session_url': session_url,
            'qr_url': qr_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/events/<event_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def admin_event_detail(event_id):
    """Get, update, or delete a specific event"""
    try:
        if request.method == 'GET':
            event = admin_config.get_event(event_id)
            if not event:
                return jsonify({'error': 'Event not found'}), 404
            
            # Add QR URL
            base_url = request.host_url.rstrip('/')
            session_url = f"{base_url}/event/{event_id}"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={session_url}"
            
            return jsonify({
                'event': event.to_dict(),
                'session_url': session_url,
                'qr_url': qr_url
            })
        
        elif request.method == 'PUT':
            # Update event
            data = request.get_json()
            user = session.get('username', 'unknown')
            
            updated_event = admin_config.update_event(event_id, data, user)
            if not updated_event:
                return jsonify({'error': 'Event not found'}), 404
            
            base_url = request.host_url.rstrip('/')
            session_url = f"{base_url}/event/{event_id}"
            
            return jsonify({
                'success': True,
                'event': updated_event.to_dict(),
                'session_url': session_url,
                'qr_url': f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={session_url}"
            })
        
        # DELETE
        user = session.get('username', 'unknown')
        if admin_config.delete_event(event_id, user):
            return jsonify({'success': True})
        return jsonify({'error': 'Event not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/events/<event_id>/deactivate', methods=['POST'])
@admin_required
def admin_deactivate_event(event_id):
    """Deactivate an event (stop accepting new sessions)"""
    try:
        user = session.get('username', 'unknown')
        if admin_config.deactivate_event(event_id, user):
            return jsonify({'success': True})
        return jsonify({'error': 'Event not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/audit-log', methods=['GET'])
@admin_required
def admin_audit_log():
    """Get audit log"""
    try:
        limit = request.args.get('limit', 50, type=int)
        log = admin_config.get_audit_log(limit)
        return jsonify({'log': log, 'count': len(log)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/export-config', methods=['GET'])
@admin_required
def admin_export_config():
    """Export configuration as JSON"""
    try:
        config = admin_config.export_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/import-config', methods=['POST'])
@admin_required
def admin_import_config():
    """Import configuration from JSON"""
    try:
        data = request.get_json()
        user = session.get('username', 'unknown')
        
        if admin_config.import_config(data, user):
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to import configuration'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/voice-session/<session_id>')
def voice_session_page(session_id):
    """Client-facing page for voice consultation"""
    voice_session = get_session(session_id)
    
    if not voice_session:
        return render_template('voice_session_error.html', 
                             error='Session not found. It may have expired or been deleted.'), 404
    
    if voice_session.status == 'expired':
        return render_template('voice_session_error.html',
                             error='This session has expired. Please ask for a new QR code.'), 410
    
    if voice_session.status == 'ended':
        return render_template('voice_session_error.html',
                             error='This session has ended. Thank you for using our service!'), 410
    
    if voice_session.status == 'connected':
        return render_template('voice_session_error.html',
                             error='This session is already in use by another client.'), 409
    
    return render_template('voice_session.html', 
                         session_id=session_id,
                         sample_rate=SAMPLE_RATE,
                         time_remaining=voice_session.time_remaining())


@app.route('/event/<event_id>')
def event_session_page(event_id):
    """Client-facing page for event-based voice consultation"""
    event = admin_config.get_event(event_id)
    
    if not event:
        return render_template('voice_session_error.html',
                             error='Event not found.'), 404
    
    if not event.is_active:
        return render_template('voice_session_error.html',
                             error='This event is no longer active.'), 410
    
    if event.is_expired():
        return render_template('voice_session_error.html',
                             error='This event has expired.'), 410
    
    if not event.can_accept_session():
        return render_template('voice_session_error.html',
                             error=f'This event has reached its maximum capacity ({event.max_concurrent_sessions} concurrent sessions). Please try again in a few minutes.'), 503
    
    # Create a new voice session for this event
    session_id, error = create_session()
    if error:
        return render_template('voice_session_error.html',
                             error=error), 503
    
    # Link session to event
    success, err_msg = admin_config.start_event_session(event_id, session_id)
    if not success:
        end_session(session_id)
        return render_template('voice_session_error.html',
                             error=err_msg), 503
    
    # Store event_id in session for cleanup
    voice_session = get_session(session_id)
    if voice_session:
        voice_session.client_info['event_id'] = event_id
        voice_session.client_info['event_name'] = event.name
    
    return render_template('voice_session.html',
                         session_id=session_id,
                         sample_rate=SAMPLE_RATE,
                         time_remaining=event.time_remaining(),
                         event_name=event.name)


# ========================================
# Socket.IO Events for Voice Agent
# ========================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on('join_session')
def handle_join_session(data):
    """Client joins a voice session room"""
    session_id = data.get('session_id')
    client_type = data.get('client_type', 'client')  # 'client' or 'consultant'
    
    if not session_id:
        emit('error', {'message': 'Session ID required'})
        return
    
    voice_session = get_session(session_id)
    if not voice_session:
        emit('error', {'message': 'Session not found'})
        return
    
    # Join the room
    join_room(session_id)
    
    # Update session status
    if client_type == 'client':
        voice_session.status = 'connected'
        # Notify consultant that client connected
        emit('client_connected', {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }, room=session_id)
    
    emit('joined', {
        'session_id': session_id,
        'status': voice_session.status
    })
    
    logger.info(f"{client_type} joined session {session_id}")


@socketio.on('leave_session')
def handle_leave_session(data):
    """Client leaves a voice session room"""
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        emit('left', {'session_id': session_id})


# Store event loops per session for async operations
voice_loops = {}

@socketio.on('start_voice')
def handle_start_voice(data):
    """Initialize Gemini voice agent for a session"""
    session_id = data.get('session_id')
    language = data.get('language', 'english')
    
    voice_session = get_session(session_id)
    if not voice_session:
        emit('error', {'message': 'Session not found'})
        return
    
    # Get CRM setting from admin config (not from client!)
    voice_settings = admin_config.get_voice_settings()
    push_to_crm = voice_settings.get('push_to_crm', True)
    voice_session.client_info['push_to_crm'] = push_to_crm
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        emit('error', {'message': 'Gemini API key not configured'})
        return
    
    try:
        # Create voice agent
        agent = GeminiVoiceAgent(api_key, session_id, language)
        voice_agents[session_id] = agent
        
        # Set up callbacks - these will be called from the async context
        async def on_message(role, text):
            socketio.emit('voice_message', {
                'role': role,
                'text': text,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            # Store in history
            voice_session.conversation_history.append({
                'role': role,
                'text': text,
                'timestamp': datetime.now().isoformat()
            })
        
        async def on_audio(audio_data):
            # Send audio as base64
            socketio.emit('voice_audio', {
                'audio': base64.b64encode(audio_data).decode('utf-8'),
                'sample_rate': SAMPLE_RATE
            }, room=session_id)
        
        async def on_status(status, message):
            voice_session.status = status
            if status == 'interrupted':
                socketio.emit('voice_interrupted', {}, room=session_id)
            socketio.emit('voice_status', {
                'status': status,
                'message': message
            }, room=session_id)
        
        async def on_search_ready(params):
            """Called when agent has collected enough info to search"""
            logger.info(f"🔍 Search triggered with params: {params}")
            
            # Notify frontend that search is in progress
            socketio.emit('voice_status', {
                'status': 'searching',
                'message': 'Running AI recommendations...',
                'params': params
            }, room=session_id)
            
            voice_session.status = 'processing'
            voice_session.client_info = params
            
            # Run the actual recommendation pipeline in a thread
            def run_recommendations():
                start_time = datetime.now()
                run_log_id = None
                
                try:
                    import re
                    
                    # If params are empty (natural language trigger), extract from conversation history
                    if not any(params.values()):
                        logger.info("Extracting info from conversation history...")
                        conversation_text = "\n".join([
                            f"{msg.get('role', 'unknown').upper()}: {msg.get('text', '')}"
                            for msg in voice_session.conversation_history
                        ])
                        
                        # Extract care level
                        care_patterns = [
                            r'(?:care level|care type|level of care|assistance level)[:\s]+(independent|assisted|memory care|skilled nursing)',
                            r'(independent|assisted|memory care|skilled nursing)[\s]+(?:care|living)',
                        ]
                        care_level = ''
                        for pattern in care_patterns:
                            match = re.search(pattern, conversation_text, re.IGNORECASE)
                            if match:
                                care_level = match.group(1).lower()
                                break
                        
                        # Extract budget
                        budget_patterns = [
                            r'(?:budget|price|cost|afford)[:\s]+(?:around|about|up to|approximately)?\s*\$?(\d+(?:,\d{3})*(?:k|K)?)',
                            r'\$(\d+(?:,\d{3})*(?:k|K)?)',
                        ]
                        budget = ''
                        for pattern in budget_patterns:
                            match = re.search(pattern, conversation_text, re.IGNORECASE)
                            if match:
                                budget = match.group(1)
                                break
                        
                        # Extract location
                        location_patterns = [
                            r'(?:location|city|area|prefer|looking)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                        ]
                        location = ''
                        for pattern in location_patterns:
                            match = re.search(pattern, conversation_text, re.IGNORECASE)
                            if match:
                                location = match.group(1)
                                break
                        
                        # Extract timeline
                        timeline_patterns = [
                            r'(?:timeline|when|need|move)[:\s]+(immediate|asap|soon|near.?term|flexible|within.*month)',
                        ]
                        timeline = ''
                        for pattern in timeline_patterns:
                            match = re.search(pattern, conversation_text, re.IGNORECASE)
                            if match:
                                timeline = match.group(1).lower()
                                break
                        
                        params.update({
                            'care_level': care_level,
                            'budget': budget,
                            'location': location,
                            'timeline': timeline
                        })
                        logger.info(f"Extracted from conversation: {params}")
                    
                    # Create client requirements from voice params
                    client_requirements = {
                        'care_level': params.get('care_level', ''),
                        'budget_min': extract_budget_min(params.get('budget', '')),
                        'budget_max': extract_budget_max(params.get('budget', '')),
                        'location': params.get('location', ''),
                        'timeline': params.get('timeline', ''),
                        'special_requirements': params.get('special_requirements', ''),
                        'source': 'voice_agent'
                    }
                    
                    logger.info(f"Running ranking with requirements: {client_requirements}")
                    
                    # Build transcription from conversation history
                    transcription = "\n".join([
                        f"{msg.get('role', 'unknown').upper()}: {msg.get('text', '')}"
                        for msg in voice_session.conversation_history
                    ])
                    
                    # Use the SAME workflow as audio/text - process transcription as text input
                    # This ensures identical backend processing, CRM format, and logging
                    system = get_system()
                    result = system.process_text_input(transcription)
                    
                    # Extract recommendations from result (same format as audio/text)
                    recommendations = result.get('recommendations', [])[:5]
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Got {len(recommendations)} recommendations in {processing_time:.1f}s")
                    
                    # Store in session
                    voice_session.recommendations = recommendations
                    voice_session.status = 'results'
                    
                    # ============ LOG TO DATABASE ============
                    try:
                        run_log_id = run_logs_db.generate_run_id()
                        run_logs_db.save_run_log(
                            run_id=run_log_id,
                            input_type='voice_agent',
                            input_filename=f'voice_session:{session_id}',
                            transcription=transcription,
                            client_info=client_requirements,
                            recommendations=recommendations,
                            processing_time_seconds=processing_time,
                            crm_pushed=False,  # Will update if CRM push succeeds
                            status='completed',
                            username=session.get('username', 'voice_client')
                        )
                        logger.info(f"Saved voice agent run log with ID: {run_log_id}")
                    except Exception as log_err:
                        logger.error(f"Failed to save run log: {log_err}")
                        run_log_id = None
                    
                    # ============ PUSH TO CRM (if enabled) ============
                    # Check if CRM push is enabled for this session
                    push_to_crm_enabled = voice_session.client_info.get('push_to_crm', True)
                    crm_result = None
                    
                    if push_to_crm_enabled and recommendations:
                        try:
                            from google_sheets_integration import push_to_crm
                            crm_data = {
                                'client_requirements': client_requirements,
                                'recommendations': recommendations,
                                'transcription': transcription[:500],  # First 500 chars
                                'source': 'voice_agent',
                                'session_id': session_id,
                                'timestamp': datetime.now().isoformat()
                            }
                            crm_result = push_to_crm(crm_data)
                            logger.info(f"Pushed voice results to CRM: {crm_result}")
                            
                            # Update run log with CRM status
                            if run_log_id:
                                run_logs_db.update_crm_status(run_log_id, True)
                        except Exception as crm_err:
                            logger.error(f"CRM push failed: {crm_err}")
                    
                    # Send recommendations to the voice agent to speak
                    loop = voice_loops.get(session_id)
                    if loop and loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(
                            agent.send_recommendations(recommendations), 
                            loop
                        )
                        future.result(timeout=30)
                    
                    # Also notify frontend (same format as audio/text results)
                    # Also notify frontend (same format as audio/text results)
                    socketio.emit('voice_recommendations', {
                        'session_id': session_id,
                        'recommendations': recommendations,
                        'client_info': result.get('client_info', client_requirements),
                        'processing_time': processing_time,
                        'run_log_id': run_log_id,
                        'crm_pushed': crm_result is not None,
                        'consultation_id': crm_result.get('consultation_id') if crm_result else None,
                        'performance_metrics': perf  # Include full metrics like audio/text
                    }, room=session_id)
                    
                except Exception as e:
                    logger.error(f"Error running recommendations: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Log the error
                    if run_log_id is None:
                        try:
                            error_run_id = run_logs_db.generate_run_id()
                            run_logs_db.save_run_log(
                                run_id=error_run_id,
                                input_type='voice_agent',
                                input_filename=f'voice_session:{session_id}',
                                transcription=str(voice_session.conversation_history),
                                client_info=params,
                                recommendations=[],
                                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                                status='failed',
                                error_message=str(e)
                            )
                        except:
                            pass
                    
                    # Tell agent to apologize
                    loop = voice_loops.get(session_id)
                    if loop and loop.is_running():
                        error_msg = "RESULTS: I apologize, but I encountered an issue searching our database. Let me try again or connect you with a human consultant."
                        asyncio.run_coroutine_threadsafe(
                            agent.session.send(input=error_msg, end_of_turn=True),
                            loop
                        )
            
            # Run in background thread to not block the voice loop
            thread = threading.Thread(target=run_recommendations, name=f"rec-{session_id}")
            thread.daemon = True
            thread.start()
        
        agent.on_message_callback = on_message
        agent.on_audio_callback = on_audio
        agent.on_status_callback = on_status
        agent.on_search_ready_callback = on_search_ready
        
        # Wrap on_status to emit voice_ready when connected
        original_on_status = on_status
        async def on_status_with_ready(status, message):
            await original_on_status(status, message)
            if status == 'connected':
                socketio.emit('voice_ready', {
                    'session_id': session_id,
                    'message': 'Voice agent ready'
                }, room=session_id)
                voice_session.status = 'collecting'
            elif status == 'interrupted':
                socketio.emit('voice_interrupted', {}, room=session_id)
        
        agent.on_status_callback = on_status_with_ready
        
        # Connect to Gemini in a background thread with its own event loop
        def connect_and_start():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            voice_loops[session_id] = loop
            
            try:
                # Run the agent's main loop (handles connect, receive, everything)
                loop.run_until_complete(agent.run())
            except Exception as e:
                logger.error(f"Voice agent error: {type(e).__name__}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                socketio.emit('error', {
                    'message': f'Voice agent error: {str(e)}'
                }, room=session_id)
            finally:
                logger.info(f"Voice agent loop ended for session {session_id}")
                loop.close()
                if session_id in voice_loops:
                    del voice_loops[session_id]
        
        # Start in background thread
        thread = threading.Thread(target=connect_and_start, name=f"voice-{session_id}")
        thread.daemon = True
        thread.start()
        
        emit('voice_initializing', {
            'session_id': session_id,
            'message': 'Connecting to AI voice agent...'
        })
        
    except Exception as e:
        logger.error(f"Error starting voice agent: {e}")
        import traceback
        logger.error(traceback.format_exc())
        emit('error', {'message': str(e)})


@socketio.on('voice_input')
def handle_voice_input(data):
    """Handle voice/audio input from client"""
    session_id = data.get('session_id')
    audio_data = data.get('audio')  # Base64 encoded
    text_input = data.get('text')
    
    if session_id not in voice_agents:
        logger.error(f"Voice agent not found for session {session_id}")
        emit('error', {'message': 'Voice agent not initialized. Please refresh the page.'})
        return
    
    agent = voice_agents[session_id]
    
    if not agent.is_connected:
        logger.error(f"Voice agent not connected for session {session_id}")
        emit('error', {'message': 'Voice agent disconnected. Please refresh the page.'})
        return
    
    try:
        # Get the event loop for this session
        loop = voice_loops.get(session_id)
        
        if audio_data:
            # Decode and send audio through the session's event loop
            audio_bytes = base64.b64decode(audio_data)
            
            if loop and loop.is_running():
                # Schedule the coroutine in the session's event loop
                asyncio.run_coroutine_threadsafe(agent.send_audio(audio_bytes), loop)
            else:
                logger.warning(f"Event loop not available for session {session_id}")
                
        elif text_input:
            # Send text input
            logger.info(f"Sending text to Gemini: {text_input[:100]}...")
            
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(agent.send_text(text_input), loop)
            
            # Also emit to room for display
            voice_session = get_session(session_id)
            if voice_session:
                voice_session.conversation_history.append({
                    'role': 'user',
                    'text': text_input,
                    'timestamp': datetime.now().isoformat()
                })
            
            emit('voice_message', {
                'role': 'user',
                'text': text_input,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
    except Exception as e:
        logger.error(f"Error processing voice input: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        emit('error', {'message': f'Error: {str(e)}'})


@socketio.on('stop_voice')
def handle_stop_voice(data):
    """Stop the voice agent"""
    session_id = data.get('session_id')
    
    if session_id in voice_agents:
        agent = voice_agents[session_id]
        
        # Disconnect is synchronous - just call it directly
        agent.disconnect()
        
        del voice_agents[session_id]
    
    # Clean up event loop reference
    if session_id in voice_loops:
        del voice_loops[session_id]
    
    voice_session = get_session(session_id)
    if voice_session:
        voice_session.status = 'ended'
    
    emit('voice_stopped', {'session_id': session_id}, room=session_id)
    logger.info(f"Voice session {session_id} stopped")


def load_persisted_voice_sessions():
    """Load persisted voice sessions from database on startup"""
    try:
        from voice_agent import VoiceSession, active_sessions
        from datetime import datetime
        import json
        
        conn = run_logs_db.get_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='voice_sessions'")
        if not cursor.fetchone():
            conn.close()
            return
        
        # Load active sessions (not expired)
        cursor.execute('''
            SELECT session_id, expires_at, status, language, created_by, session_data
            FROM voice_sessions
            WHERE expires_at > datetime('now') AND status != 'ended'
        ''')
        
        rows = cursor.fetchall()
        for row in rows:
            session_id, expires_at_str, status, language, created_by, session_data_json = row
            try:
                expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None
                session_data = json.loads(session_data_json) if session_data_json else {}
                
                # Recreate VoiceSession
                voice_session = VoiceSession(session_id=session_id)
                voice_session.status = status
                voice_session.client_info = session_data.get('client_info', {})
                voice_session.client_info['language'] = language
                voice_session.client_info['created_by'] = created_by
                if expires_at:
                    voice_session.expires_at = expires_at
                
                active_sessions[session_id] = voice_session
                logger.info(f"Loaded persisted voice session: {session_id}")
            except Exception as e:
                logger.warning(f"Failed to load session {session_id}: {e}")
        
        conn.close()
        logger.info(f"Loaded {len(rows)} persisted voice sessions")
    except Exception as e:
        logger.warning(f"Failed to load persisted sessions: {e}")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("SENIOR LIVING RECOMMENDATION SYSTEM - WEB INTERFACE")
    print("="*80)
    print("\nStarting AI Sales Assistant server with Voice Agent support...")
    
    # Load persisted voice sessions
    load_persisted_voice_sessions()
    
    print("Open your browser to: http://localhost:5050")
    print("\nVoice Agent requires GEMINI_API_KEY environment variable")
    print("\nPress Ctrl+C to stop the server")
    print("="*80 + "\n")

    # Use socketio.run for WebSocket support
    socketio.run(app, debug=False, host='0.0.0.0', port=5050, allow_unsafe_werkzeug=True)
