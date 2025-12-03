"""
Run Logs Database Module
Handles persistent storage of consultation runs, transcriptions, and metrics
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

DB_PATH = 'run_logs.db'

def get_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Run logs table - stores each consultation run
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS run_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Input info
            input_type TEXT NOT NULL,  -- 'audio' or 'text'
            language TEXT DEFAULT 'english',
            input_filename TEXT,
            input_size_bytes INTEGER,
            
            -- Transcription
            transcription TEXT,
            
            -- Extracted client info
            client_info JSON,
            
            -- Recommendations (JSON array)
            recommendations JSON,
            
            -- Performance metrics
            processing_time_seconds REAL,
            tokens_used INTEGER,
            api_cost REAL,
            api_calls INTEGER,
            
            -- Detailed timings (JSON)
            timing_breakdown JSON,
            
            -- Status
            status TEXT DEFAULT 'completed',  -- 'completed', 'failed', 'processing'
            error_message TEXT,
            
            -- CRM info
            crm_pushed BOOLEAN DEFAULT FALSE,
            consultation_id TEXT,
            
            -- User info
            username TEXT
        )
    ''')
    
    # Create indexes for common queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_run_logs_created_at ON run_logs(created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_run_logs_status ON run_logs(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_run_logs_username ON run_logs(username)')
    
    conn.commit()
    conn.close()
    print(f"[DB] Run logs database initialized at {DB_PATH}")

def generate_run_id() -> str:
    """Generate unique run ID"""
    import uuid
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    short_uuid = str(uuid.uuid4())[:8]
    return f"run_{timestamp}_{short_uuid}"

def save_run_log(
    run_id: str,
    input_type: str,
    language: str = 'english',
    input_filename: str = None,
    input_size_bytes: int = None,
    transcription: str = None,
    client_info: Dict = None,
    recommendations: List[Dict] = None,
    processing_time_seconds: float = None,
    tokens_used: int = None,
    api_cost: float = None,
    api_calls: int = None,
    timing_breakdown: Dict = None,
    status: str = 'completed',
    error_message: str = None,
    crm_pushed: bool = False,
    consultation_id: str = None,
    username: str = None
) -> bool:
    """Save a consultation run to the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO run_logs (
                run_id, input_type, language, input_filename, input_size_bytes,
                transcription, client_info, recommendations,
                processing_time_seconds, tokens_used, api_cost, api_calls,
                timing_breakdown, status, error_message,
                crm_pushed, consultation_id, username
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_id, input_type, language, input_filename, input_size_bytes,
            transcription,
            json.dumps(client_info) if client_info else None,
            json.dumps(recommendations) if recommendations else None,
            processing_time_seconds, tokens_used, api_cost, api_calls,
            json.dumps(timing_breakdown) if timing_breakdown else None,
            status, error_message,
            crm_pushed, consultation_id, username
        ))
        
        conn.commit()
        conn.close()
        print(f"[DB] Saved run log: {run_id}")
        return True
        
    except Exception as e:
        print(f"[DB] Error saving run log: {e}")
        return False

def get_run_log(run_id: str) -> Optional[Dict]:
    """Get a specific run log by ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM run_logs WHERE run_id = ?', (run_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return _row_to_dict(row)
        return None
        
    except Exception as e:
        print(f"[DB] Error getting run log: {e}")
        return None

def get_recent_runs(limit: int = 50, username: str = None) -> List[Dict]:
    """Get recent run logs"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if username:
            cursor.execute('''
                SELECT * FROM run_logs 
                WHERE username = ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (username, limit))
        else:
            cursor.execute('''
                SELECT * FROM run_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [_row_to_dict(row) for row in rows]
        
    except Exception as e:
        print(f"[DB] Error getting recent runs: {e}")
        return []

def get_performance_stats(days: int = 30) -> Dict:
    """Get aggregated performance statistics for charts"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get daily stats
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as run_count,
                AVG(processing_time_seconds) as avg_processing_time,
                AVG(tokens_used) as avg_tokens,
                SUM(api_cost) as total_cost,
                AVG(api_cost) as avg_cost
            FROM run_logs
            WHERE created_at >= datetime('now', ?)
            AND status = 'completed'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''', (f'-{days} days',))
        
        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row['date'],
                'run_count': row['run_count'],
                'avg_processing_time': round(row['avg_processing_time'] or 0, 2),
                'avg_tokens': int(row['avg_tokens'] or 0),
                'total_cost': round(row['total_cost'] or 0, 4),
                'avg_cost': round(row['avg_cost'] or 0, 4)
            })
        
        # Get overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_runs,
                AVG(processing_time_seconds) as avg_processing_time,
                MIN(processing_time_seconds) as min_processing_time,
                MAX(processing_time_seconds) as max_processing_time,
                SUM(tokens_used) as total_tokens,
                SUM(api_cost) as total_cost
            FROM run_logs
            WHERE created_at >= datetime('now', ?)
            AND status = 'completed'
        ''', (f'-{days} days',))
        
        overall = cursor.fetchone()
        conn.close()
        
        return {
            'daily': daily_stats,
            'overall': {
                'total_runs': overall['total_runs'] or 0,
                'avg_processing_time': round(overall['avg_processing_time'] or 0, 2),
                'min_processing_time': round(overall['min_processing_time'] or 0, 2),
                'max_processing_time': round(overall['max_processing_time'] or 0, 2),
                'total_tokens': int(overall['total_tokens'] or 0),
                'total_cost': round(overall['total_cost'] or 0, 4)
            }
        }
        
    except Exception as e:
        print(f"[DB] Error getting performance stats: {e}")
        return {'daily': [], 'overall': {}}

def get_processing_time_history(limit: int = 20) -> List[float]:
    """Get recent processing times for mini-chart"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT processing_time_seconds
            FROM run_logs
            WHERE status = 'completed'
            AND processing_time_seconds IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        times = [row['processing_time_seconds'] for row in cursor.fetchall()]
        conn.close()
        
        # Reverse to show oldest to newest (left to right on chart)
        return list(reversed(times))
        
    except Exception as e:
        print(f"[DB] Error getting processing time history: {e}")
        return []

def get_token_history(limit: int = 20) -> List[int]:
    """Get recent token usage for mini-chart"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tokens_used
            FROM run_logs
            WHERE status = 'completed'
            AND tokens_used IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        tokens = [row['tokens_used'] for row in cursor.fetchall()]
        conn.close()
        
        return list(reversed(tokens))
        
    except Exception as e:
        print(f"[DB] Error getting token history: {e}")
        return []

def get_cost_history(limit: int = 20) -> List[float]:
    """Get recent API costs for mini-chart"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT api_cost
            FROM run_logs
            WHERE status = 'completed'
            AND api_cost IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        costs = [row['api_cost'] for row in cursor.fetchall()]
        conn.close()
        
        return list(reversed(costs))
        
    except Exception as e:
        print(f"[DB] Error getting cost history: {e}")
        return []

def _row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert database row to dictionary with JSON parsing"""
    d = dict(row)
    
    # Parse JSON fields
    for field in ['client_info', 'recommendations', 'timing_breakdown']:
        if d.get(field):
            try:
                d[field] = json.loads(d[field])
            except:
                pass
    
    return d


def update_crm_status(run_id: str, pushed: bool = True) -> bool:
    """Update the CRM push status for a run log"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE run_logs 
            SET crm_pushed = ?
            WHERE run_id = ?
        ''', (pushed, run_id))
        
        conn.commit()
        conn.close()
        print(f"[DB] Updated CRM status for {run_id}: pushed={pushed}")
        return True
        
    except Exception as e:
        print(f"[DB] Error updating CRM status: {e}")
        return False


def get_run_by_db_id(db_id: int) -> Optional[Dict]:
    """Get a run log by database ID (not run_id)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM run_logs WHERE id = ?', (db_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return _row_to_dict(row)
        return None
        
    except Exception as e:
        print(f"[DB] Error getting run by DB ID: {e}")
        return None


# Initialize database on module load
if not os.path.exists(DB_PATH):
    init_database()

