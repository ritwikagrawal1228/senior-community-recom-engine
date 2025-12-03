"""
Admin Configuration Management
Handles system settings, ranking weights, and event management
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = 'admin_config.json'

# Default configuration
DEFAULT_CONFIG = {
    'voice_agent': {
        'max_concurrent_sessions': 10,
        'session_timeout_minutes': 30,
        'default_language': 'english',
        'enable_voice_agent': True,
        'push_to_crm': True  # Automatically push voice consultation results to CRM
    },
    'ranking_weights': {
        'business': 1.0,
        'cost': 1.0,
        'distance': 1.0,
        'availability': 1.0,
        'budget_efficiency': 1.0,
        'couple': 1.0,
        'amenity': 1.0,
        'holistic': 1.0
    },
    'ranking_weights_presets': {
        'balanced': {
            'name': 'Balanced',
            'description': 'Equal weight to all factors',
            'weights': {
                'business': 1.0, 'cost': 1.0, 'distance': 1.0, 'availability': 1.0,
                'budget_efficiency': 1.0, 'couple': 1.0, 'amenity': 1.0, 'holistic': 1.0
            }
        },
        'cost_focused': {
            'name': 'Cost Focused',
            'description': 'Prioritizes budget and cost efficiency',
            'weights': {
                'business': 0.5, 'cost': 2.0, 'distance': 1.0, 'availability': 1.0,
                'budget_efficiency': 2.0, 'couple': 1.0, 'amenity': 0.5, 'holistic': 1.0
            }
        },
        'location_focused': {
            'name': 'Location Focused',
            'description': 'Prioritizes proximity to client',
            'weights': {
                'business': 1.0, 'cost': 1.0, 'distance': 3.0, 'availability': 1.0,
                'budget_efficiency': 1.0, 'couple': 1.0, 'amenity': 1.0, 'holistic': 1.0
            }
        },
        'availability_focused': {
            'name': 'Immediate Availability',
            'description': 'Prioritizes communities with immediate openings',
            'weights': {
                'business': 1.0, 'cost': 1.0, 'distance': 1.0, 'availability': 3.0,
                'budget_efficiency': 1.0, 'couple': 1.0, 'amenity': 0.5, 'holistic': 1.0
            }
        },
        'premium_experience': {
            'name': 'Premium Experience',
            'description': 'Prioritizes amenities and holistic fit',
            'weights': {
                'business': 1.5, 'cost': 0.5, 'distance': 1.0, 'availability': 1.0,
                'budget_efficiency': 0.5, 'couple': 1.0, 'amenity': 2.0, 'holistic': 2.0
            }
        }
    },
    'system': {
        'maintenance_mode': False,
        'debug_mode': False,
        'log_level': 'INFO',
        'max_recommendations': 10,
        'enable_crm_integration': True,
        'enable_email_notifications': True
    },
    'events': {},  # Active events stored here
    'audit_log': []  # Track configuration changes
}


@dataclass
class Event:
    """Represents a single QR code event with concurrent session limit"""
    event_id: str
    name: str
    description: str
    created_at: datetime
    expires_at: datetime
    created_by: str
    max_concurrent_sessions: int  # How many people can use this QR at once
    current_sessions: int = 0  # Currently active sessions
    total_sessions_served: int = 0  # Total sessions that have used this event
    is_active: bool = True
    session_ids: List[str] = field(default_factory=list)  # Track active session IDs
    
    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'created_by': self.created_by,
            'max_concurrent_sessions': self.max_concurrent_sessions,
            'current_sessions': self.current_sessions,
            'total_sessions_served': self.total_sessions_served,
            'is_active': self.is_active,
            'session_ids': self.session_ids,
            'time_remaining': self.time_remaining(),
            'is_expired': self.is_expired()
        }
    
    def time_remaining(self) -> int:
        """Returns seconds until expiration"""
        delta = self.expires_at - datetime.now()
        return max(0, int(delta.total_seconds()))
    
    def is_expired(self) -> bool:
        """Check if event has expired"""
        return datetime.now() > self.expires_at
    
    def can_accept_session(self) -> bool:
        """Check if event can accept new sessions"""
        return self.is_active and not self.is_expired() and self.current_sessions < self.max_concurrent_sessions
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        return cls(
            event_id=data['event_id'],
            name=data['name'],
            description=data['description'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            created_by=data['created_by'],
            max_concurrent_sessions=data.get('max_concurrent_sessions', data.get('max_sessions', 10)),
            current_sessions=data.get('current_sessions', 0),
            total_sessions_served=data.get('total_sessions_served', data.get('sessions_used', 0)),
            is_active=data.get('is_active', True),
            session_ids=data.get('session_ids', [])
        )


class AdminConfig:
    """Manages admin configuration with persistence"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file or create default"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(DEFAULT_CONFIG, loaded)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: dict, loaded: dict) -> dict:
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _add_audit_log(self, action: str, user: str, details: dict):
        """Add entry to audit log"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user': user,
            'details': details
        }
        if 'audit_log' not in self.config:
            self.config['audit_log'] = []
        self.config['audit_log'].append(entry)
        # Keep only last 100 entries
        self.config['audit_log'] = self.config['audit_log'][-100:]
        self._save_config()
    
    # ==================== Voice Agent Settings ====================
    
    def get_voice_settings(self) -> dict:
        return self.config.get('voice_agent', DEFAULT_CONFIG['voice_agent'])
    
    def update_voice_settings(self, settings: dict, user: str) -> dict:
        """Update voice agent settings"""
        old_settings = self.config.get('voice_agent', {}).copy()
        self.config['voice_agent'].update(settings)
        self._save_config()
        self._add_audit_log('update_voice_settings', user, {
            'old': old_settings,
            'new': self.config['voice_agent']
        })
        return self.config['voice_agent']
    
    def get_max_sessions(self) -> int:
        return self.config.get('voice_agent', {}).get('max_concurrent_sessions', 10)
    
    def get_session_timeout(self) -> int:
        return self.config.get('voice_agent', {}).get('session_timeout_minutes', 30)
    
    # ==================== Ranking Weights ====================
    
    def get_ranking_weights(self) -> dict:
        return self.config.get('ranking_weights', DEFAULT_CONFIG['ranking_weights'])
    
    def update_ranking_weights(self, weights: dict, user: str) -> dict:
        """Update ranking weights"""
        old_weights = self.config.get('ranking_weights', {}).copy()
        
        # Validate weights (must be between 0 and 5)
        for key, value in weights.items():
            if not isinstance(value, (int, float)) or value < 0 or value > 5:
                raise ValueError(f"Weight '{key}' must be a number between 0 and 5")
        
        self.config['ranking_weights'].update(weights)
        self._save_config()
        self._add_audit_log('update_ranking_weights', user, {
            'old': old_weights,
            'new': self.config['ranking_weights']
        })
        return self.config['ranking_weights']
    
    def reset_ranking_weights(self, user: str) -> dict:
        """Reset weights to default"""
        old_weights = self.config.get('ranking_weights', {}).copy()
        self.config['ranking_weights'] = DEFAULT_CONFIG['ranking_weights'].copy()
        self._save_config()
        self._add_audit_log('reset_ranking_weights', user, {
            'old': old_weights,
            'new': self.config['ranking_weights']
        })
        return self.config['ranking_weights']
    
    def apply_weight_preset(self, preset_name: str, user: str) -> dict:
        """Apply a preset weight configuration"""
        presets = self.config.get('ranking_weights_presets', {})
        if preset_name not in presets:
            raise ValueError(f"Preset '{preset_name}' not found")
        
        preset = presets[preset_name]
        return self.update_ranking_weights(preset['weights'], user)
    
    def get_weight_presets(self) -> dict:
        return self.config.get('ranking_weights_presets', DEFAULT_CONFIG['ranking_weights_presets'])
    
    # ==================== System Settings ====================
    
    def get_system_settings(self) -> dict:
        return self.config.get('system', DEFAULT_CONFIG['system'])
    
    def update_system_settings(self, settings: dict, user: str) -> dict:
        """Update system settings"""
        old_settings = self.config.get('system', {}).copy()
        self.config['system'].update(settings)
        self._save_config()
        self._add_audit_log('update_system_settings', user, {
            'old': old_settings,
            'new': self.config['system']
        })
        return self.config['system']
    
    def is_maintenance_mode(self) -> bool:
        return self.config.get('system', {}).get('maintenance_mode', False)
    
    # ==================== Event Management ====================
    
    def create_event(self, name: str, description: str, max_concurrent_sessions: int, 
                     duration_hours: int, duration_minutes: int, user: str) -> Event:
        """Create a new event with a single QR code and concurrent session limit"""
        event_id = f"event_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        # Calculate total duration
        total_minutes = (duration_hours * 60) + duration_minutes
        
        event = Event(
            event_id=event_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=total_minutes),
            created_by=user,
            max_concurrent_sessions=max_concurrent_sessions
        )
        
        if 'events' not in self.config:
            self.config['events'] = {}
        
        self.config['events'][event_id] = event.to_dict()
        self._save_config()
        self._add_audit_log('create_event', user, {
            'event_id': event_id,
            'name': name,
            'max_concurrent_sessions': max_concurrent_sessions,
            'duration_minutes': total_minutes
        })
        
        return event
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID"""
        event_data = self.config.get('events', {}).get(event_id)
        if event_data:
            return Event.from_dict(event_data)
        return None
    
    def get_all_events(self) -> List[Event]:
        """Get all events"""
        events = []
        for event_data in self.config.get('events', {}).values():
            events.append(Event.from_dict(event_data))
        return sorted(events, key=lambda e: e.created_at, reverse=True)
    
    def deactivate_event(self, event_id: str, user: str) -> bool:
        """Deactivate an event"""
        if event_id in self.config.get('events', {}):
            self.config['events'][event_id]['is_active'] = False
            self._save_config()
            self._add_audit_log('deactivate_event', user, {'event_id': event_id})
            return True
        return False
    
    def delete_event(self, event_id: str, user: str) -> bool:
        """Delete an event"""
        if event_id in self.config.get('events', {}):
            del self.config['events'][event_id]
            self._save_config()
            self._add_audit_log('delete_event', user, {'event_id': event_id})
            return True
        return False
    
    def start_event_session(self, event_id: str, session_id: str) -> tuple[bool, str]:
        """Start a new session for an event. Returns (success, error_message)"""
        if event_id not in self.config.get('events', {}):
            return False, "Event not found"
        
        event_data = self.config['events'][event_id]
        event = Event.from_dict(event_data)
        
        if not event.is_active:
            return False, "Event is not active"
        
        if event.is_expired():
            return False, "Event has expired"
        
        if event.current_sessions >= event.max_concurrent_sessions:
            return False, f"Maximum concurrent sessions ({event.max_concurrent_sessions}) reached"
        
        # Add session
        event_data['current_sessions'] = event_data.get('current_sessions', 0) + 1
        event_data['total_sessions_served'] = event_data.get('total_sessions_served', 0) + 1
        if 'session_ids' not in event_data:
            event_data['session_ids'] = []
        event_data['session_ids'].append(session_id)
        
        self._save_config()
        return True, ""
    
    def end_event_session(self, event_id: str, session_id: str) -> bool:
        """End a session for an event"""
        if event_id not in self.config.get('events', {}):
            return False
        
        event_data = self.config['events'][event_id]
        
        if session_id in event_data.get('session_ids', []):
            event_data['session_ids'].remove(session_id)
            event_data['current_sessions'] = max(0, event_data.get('current_sessions', 1) - 1)
            self._save_config()
            return True
        return False
    
    def update_event(self, event_id: str, updates: dict, user: str) -> Optional[Event]:
        """Update an existing event"""
        if event_id not in self.config.get('events', {}):
            return None
        
        event_data = self.config['events'][event_id]
        old_data = event_data.copy()
        
        # Update allowed fields
        if 'name' in updates:
            event_data['name'] = updates['name']
        if 'description' in updates:
            event_data['description'] = updates['description']
        if 'max_concurrent_sessions' in updates:
            event_data['max_concurrent_sessions'] = updates['max_concurrent_sessions']
        if 'duration_hours' in updates or 'duration_minutes' in updates:
            hours = updates.get('duration_hours', 0)
            minutes = updates.get('duration_minutes', 0)
            if hours > 0 or minutes > 0:
                total_minutes = (hours * 60) + minutes
                # Extend from now
                event_data['expires_at'] = (datetime.now() + timedelta(minutes=total_minutes)).isoformat()
        if 'is_active' in updates:
            event_data['is_active'] = updates['is_active']
        
        self._save_config()
        self._add_audit_log('update_event', user, {
            'event_id': event_id,
            'old': old_data,
            'new': event_data
        })
        
        return Event.from_dict(event_data)
    
    # ==================== Audit Log ====================
    
    def get_audit_log(self, limit: int = 50) -> list:
        """Get recent audit log entries"""
        log = self.config.get('audit_log', [])
        return log[-limit:][::-1]  # Return most recent first
    
    # ==================== Full Config ====================
    
    def get_full_config(self) -> dict:
        """Get entire configuration (for admin display)"""
        return {
            'voice_agent': self.get_voice_settings(),
            'ranking_weights': self.get_ranking_weights(),
            'ranking_weights_presets': self.get_weight_presets(),
            'system': self.get_system_settings(),
            'events_count': len(self.config.get('events', {})),
            'active_events': len([e for e in self.get_all_events() if e.is_active])
        }
    
    def export_config(self) -> dict:
        """Export configuration (without audit log)"""
        config_copy = self.config.copy()
        config_copy.pop('audit_log', None)
        return config_copy
    
    def import_config(self, config_data: dict, user: str) -> bool:
        """Import configuration"""
        try:
            # Validate structure
            if 'ranking_weights' in config_data:
                for key in DEFAULT_CONFIG['ranking_weights']:
                    if key not in config_data['ranking_weights']:
                        raise ValueError(f"Missing weight: {key}")
            
            old_config = self.config.copy()
            self.config = self._merge_configs(DEFAULT_CONFIG, config_data)
            self._save_config()
            self._add_audit_log('import_config', user, {
                'imported_keys': list(config_data.keys())
            })
            return True
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return False


# Singleton instance
admin_config = AdminConfig()


# Export for use in app.py
__all__ = ['admin_config', 'AdminConfig', 'Event', 'DEFAULT_CONFIG']

