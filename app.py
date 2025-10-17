"""
Senior Living Community Recommendation System - Web Interface
Simple Flask backend for UI interaction
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from main_pipeline_ranking import RankingBasedRecommendationSystem
from google_sheets_integration import push_to_crm

# Load environment
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs('uploads', exist_ok=True)
os.makedirs('output', exist_ok=True)

# Initialize recommendation system
recommendation_system = None

def get_system():
    """Lazy-load the recommendation system"""
    global recommendation_system
    if recommendation_system is None:
        recommendation_system = RankingBasedRecommendationSystem()
    return recommendation_system

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'gemini_configured': bool(os.getenv('GEMINI_API_KEY')),
        'sheets_configured': bool(os.getenv('GOOGLE_SPREADSHEET_ID'))
    })

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """Process uploaded audio file"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)

        # Process the audio file
        system = get_system()
        result = system.process_audio_file(filepath)

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

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-text', methods=['POST'])
def process_text():
    """Process text consultation"""
    try:
        data = request.get_json()
        text = data.get('text', '')

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

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

        stats = {
            'total_communities': len(df),
            'care_levels': df['Care Level'].value_counts().to_dict(),
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
    print("\nStarting server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
