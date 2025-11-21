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
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# Local imports
from main_pipeline_ranking import RankingBasedRecommendationSystem
from google_sheets_integration import push_to_crm

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

# Simple user database (in production, use a real database)
USERS = {
    'admin': 'admin123',
    'consultant': 'consultant123',
    'manager': 'manager123'
}

# No SocketIO needed - live features removed

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

        logger.info("Processing completed successfully")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in processing: {e}", exc_info=True)
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

        logger.info("Processing completed successfully")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in processing: {e}", exc_info=True)
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

if __name__ == '__main__':
    print("\n" + "="*80)
    print("SENIOR LIVING RECOMMENDATION SYSTEM - WEB INTERFACE")
    print("="*80)
    print("\nStarting AI Sales Assistant server...")
    print("Open your browser to: http://localhost:5050")
    print("\nPress Ctrl+C to stop the server")
    print("="*80 + "\n")

    app.run(debug=False, host='0.0.0.0', port=5050)
