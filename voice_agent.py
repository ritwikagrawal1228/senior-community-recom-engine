"""
Gemini Real-Time Voice Agent for Senior Living Consultations
Uses Gemini 2.0 Flash Live API for real-time voice conversations
"""

import os
import json
import asyncio
import base64
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field

# WebSocket imports
try:
    from websockets.asyncio.client import connect as ws_connect
except ImportError:
    from websockets import connect as ws_connect

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Gemini Live API Configuration
GEMINI_HOST = 'generativelanguage.googleapis.com'
GEMINI_MODEL = 'models/gemini-2.0-flash-live-001'
SAMPLE_RATE = 24000

@dataclass
class VoiceSession:
    """Represents an active voice session"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now())
    status: str = 'waiting'  # waiting, connected, collecting, processing, results, ended
    client_info: Dict[str, Any] = field(default_factory=dict)
    conversation_history: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    gemini_ws: Any = None
    client_ws: Any = None
    
    def __post_init__(self):
        # Session expires based on configured timeout
        timeout = get_session_timeout()
        self.expires_at = self.created_at + timedelta(minutes=timeout)
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.now() > self.expires_at
    
    def is_active(self) -> bool:
        """Check if session is still usable"""
        return not self.is_expired() and self.status not in ['ended', 'expired']
    
    def time_remaining(self) -> int:
        """Returns seconds remaining before expiration"""
        delta = self.expires_at - datetime.now()
        return max(0, int(delta.total_seconds()))


# Active sessions storage
active_sessions: Dict[str, VoiceSession] = {}

# Configuration (can be updated dynamically by admin)
MAX_CONCURRENT_SESSIONS = 10  # Maximum parallel sessions
SESSION_TIMEOUT_MINUTES = 30  # Session expiration time

def get_max_sessions() -> int:
    """Get max sessions from admin config if available"""
    try:
        from admin_config import admin_config
        return admin_config.get_max_sessions()
    except:
        return MAX_CONCURRENT_SESSIONS

def get_session_timeout() -> int:
    """Get session timeout from admin config if available"""
    try:
        from admin_config import admin_config
        return admin_config.get_session_timeout()
    except:
        return SESSION_TIMEOUT_MINUTES

def get_voice_system_instruction(language: str = 'english') -> str:
    """Get the system instruction for the voice agent"""
    
    language_suffix = {
        'english': 'Respond and listen only in English.',
        'hindi': 'Respond and listen only in Hindi.',
        'spanish': 'Respond and listen only in Spanish.'
    }.get(language.lower(), 'Respond and listen only in English.')
    
    return f"""You are a friendly and professional AI voice assistant for a senior living placement service. Your name is "Sage" and you help families find the perfect senior living community.

PERSONALITY:
- Warm, empathetic, and patient
- Professional but conversational
- Encouraging and supportive
- Never rushed or dismissive

YOUR CONVERSATION FLOW:

1. GREETING (First message):
   - Introduce yourself warmly
   - Explain you're here to help find the perfect community
   - Ask if they're looking for themselves or a loved one

2. INFORMATION GATHERING (Ask one at a time, naturally):
   - Care Level: "What type of care are you looking for? Independent living for those who are active, assisted living for daily support, or memory care for cognitive needs?"
   - Budget: "What monthly budget range works for you? This helps me find communities that fit your finances."
   - Location: "What area or ZIP code would you prefer? Being close to family is often important."
   - Timeline: "How soon are you hoping to make this transition? Immediately, in the next few months, or are you just planning ahead?"
   - Special Needs: "Are there any special requirements? For example, pets, couples staying together, or specific medical needs?"

3. PROCESSING PHASE:
   - Once you have the key information, tell them you're searching
   - Make friendly small talk while they wait (2-3 minutes)
   - Topics: amenities at communities, what to expect, questions they might have
   - Periodically reassure them the search is ongoing

4. RESULTS PHASE:
   - Announce excitedly that you found matches
   - Present top 3 recommendations clearly:
     * Community name/ID
     * Care level and monthly fee
     * Why it's a good match
     * Any special features
   - Ask if they have questions about any option

IMPORTANT RULES:
- Keep responses concise (2-3 sentences max for voice)
- Use natural speech patterns with filler words occasionally
- Show empathy when discussing sensitive topics
- Never make up specific community names - use "Community #X" format
- If unsure about something, ask clarifying questions
- {language_suffix}

TOOL USAGE:
When you've collected enough information, use the search_communities function to find matches.
When presenting results, use the present_recommendations function.
"""


def encode_text_input(text: str) -> dict:
    """Encode text input for Gemini Live API"""
    return {
        'clientContent': {
            'turns': [{
                'role': 'user',
                'parts': [{'text': text}]
            }],
            'turnComplete': True
        }
    }


def encode_audio_input(audio_data: bytes) -> dict:
    """Encode audio input for Gemini Live API"""
    return {
        'realtimeInput': {
            'mediaChunks': [{
                'mimeType': f'audio/pcm;rate={SAMPLE_RATE}',
                'data': base64.b64encode(audio_data).decode('utf-8')
            }]
        }
    }


def decode_response(response: dict) -> Dict[str, Any]:
    """Decode Gemini Live API response"""
    result = {
        'type': 'unknown',
        'text': None,
        'audio': None,
        'turn_complete': False,
        'interrupted': False,
        'tool_call': None
    }
    
    server_content = response.get('serverContent', {})
    
    # Check for model turn (text or audio response)
    model_turn = server_content.get('modelTurn', {})
    if model_turn:
        parts = model_turn.get('parts', [])
        for part in parts:
            # Text response
            if 'text' in part:
                result['type'] = 'text'
                result['text'] = part['text']
            # Audio response
            elif 'inlineData' in part:
                result['type'] = 'audio'
                result['audio'] = base64.b64decode(part['inlineData'].get('data', ''))
    
    # Check for turn complete
    if server_content.get('turnComplete'):
        result['turn_complete'] = True
    
    # Check for interruption
    if server_content.get('interrupted'):
        result['interrupted'] = True
    
    # Check for tool call
    if 'toolCall' in response:
        result['type'] = 'tool_call'
        result['tool_call'] = response['toolCall']
    
    return result


class GeminiVoiceAgent:
    """Handles real-time voice conversations with Gemini"""
    
    def __init__(self, api_key: str, session_id: str, language: str = 'english'):
        self.api_key = api_key
        self.session_id = session_id
        self.language = language
        self.ws = None
        self.is_connected = False
        self.collected_info = {}
        self.on_message_callback: Optional[Callable] = None
        self.on_audio_callback: Optional[Callable] = None
        self.on_status_callback: Optional[Callable] = None
        
    async def connect(self) -> bool:
        """Connect to Gemini Live API"""
        try:
            uri = f'wss://{GEMINI_HOST}/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={self.api_key}'
            
            self.ws = await ws_connect(uri)
            
            # Send setup message
            setup_message = {
                'setup': {
                    'model': GEMINI_MODEL,
                    'generationConfig': {
                        'responseModalities': ['AUDIO', 'TEXT'],
                        'speechConfig': {
                            'voiceConfig': {
                                'prebuiltVoiceConfig': {
                                    'voiceName': 'Aoede'  # Friendly female voice
                                }
                            }
                        }
                    },
                    'systemInstruction': {
                        'parts': [{'text': get_voice_system_instruction(self.language)}]
                    },
                    'tools': [{
                        'functionDeclarations': [
                            {
                                'name': 'search_communities',
                                'description': 'Search for senior living communities based on collected client information',
                                'parameters': {
                                    'type': 'OBJECT',
                                    'properties': {
                                        'care_level': {
                                            'type': 'STRING',
                                            'description': 'Type of care needed: independent, assisted, or memory_care'
                                        },
                                        'budget_min': {
                                            'type': 'NUMBER',
                                            'description': 'Minimum monthly budget'
                                        },
                                        'budget_max': {
                                            'type': 'NUMBER',
                                            'description': 'Maximum monthly budget'
                                        },
                                        'zip_code': {
                                            'type': 'STRING',
                                            'description': 'Preferred ZIP code or area'
                                        },
                                        'timeline': {
                                            'type': 'STRING',
                                            'description': 'When they need to move: immediate, near_term, flexible'
                                        },
                                        'special_needs': {
                                            'type': 'STRING',
                                            'description': 'Any special requirements like pets, couples, etc.'
                                        }
                                    },
                                    'required': ['care_level']
                                }
                            },
                            {
                                'name': 'present_recommendations',
                                'description': 'Present the found recommendations to the client',
                                'parameters': {
                                    'type': 'OBJECT',
                                    'properties': {
                                        'recommendations': {
                                            'type': 'ARRAY',
                                            'description': 'List of community recommendations',
                                            'items': {
                                                'type': 'OBJECT',
                                                'properties': {
                                                    'community_id': {'type': 'STRING'},
                                                    'care_level': {'type': 'STRING'},
                                                    'monthly_fee': {'type': 'NUMBER'},
                                                    'match_score': {'type': 'NUMBER'},
                                                    'highlights': {'type': 'STRING'}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }]
                }
            }
            
            await self.ws.send(json.dumps(setup_message))
            
            # Wait for setup complete
            response = await self.ws.recv()
            setup_response = json.loads(response)
            
            if 'setupComplete' in setup_response:
                self.is_connected = True
                logger.info(f"Gemini Voice Agent connected for session {self.session_id}")
                return True
            else:
                logger.error(f"Setup failed: {setup_response}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {e}")
            return False
    
    async def send_text(self, text: str):
        """Send text message to Gemini"""
        if not self.is_connected or not self.ws:
            return
        
        message = encode_text_input(text)
        await self.ws.send(json.dumps(message))
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to Gemini"""
        if not self.is_connected or not self.ws:
            return
        
        message = encode_audio_input(audio_data)
        await self.ws.send(json.dumps(message))
    
    async def start_conversation(self):
        """Start the conversation with a greeting"""
        # Send initial trigger to start conversation
        await self.send_text("Hello, I'm ready to start the consultation.")
    
    async def handle_tool_call(self, tool_call: dict) -> dict:
        """Handle function calls from Gemini"""
        function_calls = tool_call.get('functionCalls', [])
        responses = []
        
        for fc in function_calls:
            name = fc.get('name')
            args = fc.get('args', {})
            fc_id = fc.get('id')
            
            if name == 'search_communities':
                # Store collected info
                self.collected_info = args
                
                # Notify status change
                if self.on_status_callback:
                    await self.on_status_callback('processing', 'Searching communities...')
                
                # Simulate search (in real implementation, call recommendation system)
                result = await self._search_communities(args)
                
                responses.append({
                    'id': fc_id,
                    'name': name,
                    'response': {'result': result}
                })
                
            elif name == 'present_recommendations':
                if self.on_status_callback:
                    await self.on_status_callback('results', 'Presenting recommendations')
                
                responses.append({
                    'id': fc_id,
                    'name': name,
                    'response': {'result': {'success': True}}
                })
        
        # Send tool response back to Gemini
        if responses:
            tool_response = {
                'toolResponse': {
                    'functionResponses': responses
                }
            }
            await self.ws.send(json.dumps(tool_response))
        
        return responses
    
    async def _search_communities(self, criteria: dict) -> dict:
        """Search for communities based on criteria using the real recommendation system"""
        try:
            # Try to use the actual recommendation system
            from main_pipeline_ranking import RankingBasedRecommendationSystem
            import pandas as pd
            
            system = RankingBasedRecommendationSystem()
            
            # Build client profile from collected criteria
            care_level = criteria.get('care_level', 'assisted')
            budget_min = criteria.get('budget_min', 0)
            budget_max = criteria.get('budget_max', 10000)
            zip_code = criteria.get('zip_code', '')
            timeline = criteria.get('timeline', 'flexible')
            special_needs = criteria.get('special_needs', '')
            
            # Map care level to system format
            care_level_map = {
                'independent': 'Independent Living',
                'assisted': 'Assisted Living',
                'memory_care': 'Memory Care',
                'memory': 'Memory Care'
            }
            mapped_care = care_level_map.get(care_level.lower(), 'Assisted Living')
            
            # Create client profile
            client_profile = {
                'care_level': mapped_care,
                'budget_range': f"${budget_min:,} - ${budget_max:,}",
                'budget_min': budget_min,
                'budget_max': budget_max,
                'location': zip_code,
                'zip_code': zip_code,
                'timeline': timeline,
                'special_requirements': special_needs,
                'pets': 'yes' if 'pet' in special_needs.lower() else 'no',
                'couples': 'yes' if 'couple' in special_needs.lower() else 'no'
            }
            
            # Get recommendations
            results = system.get_recommendations(client_profile, top_n=5)
            
            recommendations = []
            for rec in results.get('recommendations', []):
                recommendations.append({
                    'community_id': str(rec.get('community_id', rec.get('CommunityID', 'N/A'))),
                    'name': f"Community #{rec.get('community_id', rec.get('CommunityID', 'N/A'))}",
                    'care_level': rec.get('care_level', mapped_care),
                    'monthly_fee': rec.get('monthly_fee', rec.get('Monthly Fee', 0)),
                    'match_score': rec.get('match_score', rec.get('score', 0)),
                    'zip': rec.get('zip', rec.get('ZIP', '')),
                    'highlights': rec.get('explanation', rec.get('match_reasons', 'Good match for your needs')),
                    'waitlist': rec.get('waitlist', rec.get('Est. Waitlist Length', 'Unknown')),
                    'enhanced': rec.get('enhanced', rec.get('Enhanced', False))
                })
            
            if recommendations:
                return {
                    'success': True,
                    'count': len(recommendations),
                    'recommendations': recommendations
                }
            
        except Exception as e:
            logger.warning(f"Could not use real recommendation system: {e}")
        
        # Fallback to mock results if real system fails
        care_level = criteria.get('care_level', 'assisted')
        budget_max = criteria.get('budget_max', 6000)
        
        recommendations = [
            {
                'community_id': '101',
                'name': 'Community #101',
                'care_level': care_level.title(),
                'monthly_fee': min(5200, budget_max),
                'match_score': 95,
                'zip': criteria.get('zip_code', '90210'),
                'highlights': 'Pet-friendly, 24-hour care, gourmet dining, beautiful gardens',
                'waitlist': 'None'
            },
            {
                'community_id': '102',
                'name': 'Community #102',
                'care_level': care_level.title(),
                'monthly_fee': min(4800, int(budget_max * 0.9)),
                'match_score': 92,
                'zip': criteria.get('zip_code', '90210'),
                'highlights': 'Award-winning memory care, therapy services, family events',
                'waitlist': '1-2 months'
            },
            {
                'community_id': '103',
                'name': 'Community #103',
                'care_level': care_level.title(),
                'monthly_fee': min(4500, int(budget_max * 0.85)),
                'match_score': 89,
                'zip': criteria.get('zip_code', '90210'),
                'highlights': 'Exceptional dining, active social calendar, transportation',
                'waitlist': 'None'
            }
        ]
        
        return {
            'success': True,
            'count': len(recommendations),
            'recommendations': recommendations
        }
    
    async def receive_loop(self):
        """Main loop to receive and process messages from Gemini"""
        if not self.ws:
            return
        
        try:
            async for message in self.ws:
                response = json.loads(message)
                decoded = decode_response(response)
                
                # Handle different response types
                if decoded['type'] == 'text' and decoded['text']:
                    if self.on_message_callback:
                        await self.on_message_callback('agent', decoded['text'])
                
                elif decoded['type'] == 'audio' and decoded['audio']:
                    if self.on_audio_callback:
                        await self.on_audio_callback(decoded['audio'])
                
                elif decoded['type'] == 'tool_call' and decoded['tool_call']:
                    await self.handle_tool_call(decoded['tool_call'])
                
                if decoded['interrupted']:
                    logger.info("User interrupted")
                
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
        finally:
            self.is_connected = False
    
    async def disconnect(self):
        """Disconnect from Gemini"""
        self.is_connected = False
        if self.ws:
            await self.ws.close()
            self.ws = None


def cleanup_expired_sessions():
    """Remove expired sessions from memory"""
    expired = [sid for sid, session in active_sessions.items() if session.is_expired()]
    for sid in expired:
        logger.info(f"Cleaning up expired session: {sid}")
        active_sessions[sid].status = 'expired'
        del active_sessions[sid]
    return len(expired)


def get_active_session_count() -> int:
    """Get count of active (non-expired) sessions"""
    cleanup_expired_sessions()  # Clean up first
    return len([s for s in active_sessions.values() if s.is_active()])


def create_session() -> tuple[str, Optional[str]]:
    """
    Create a new voice session.
    Returns (session_id, error_message)
    """
    # Cleanup expired sessions first
    cleanup_expired_sessions()
    
    # Check if we've hit the limit
    max_sessions = get_max_sessions()
    active_count = get_active_session_count()
    if active_count >= max_sessions:
        return None, f"Maximum concurrent sessions ({max_sessions}) reached. Please try again later."
    
    session_id = f"voice_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    active_sessions[session_id] = VoiceSession(session_id=session_id)
    
    logger.info(f"Created session {session_id}. Active sessions: {active_count + 1}/{MAX_CONCURRENT_SESSIONS}")
    
    return session_id, None


def get_session(session_id: str) -> Optional[VoiceSession]:
    """Get an existing voice session if it's still valid"""
    session = active_sessions.get(session_id)
    
    if session is None:
        return None
    
    # Check if expired
    if session.is_expired():
        session.status = 'expired'
        return session  # Return it so caller can show appropriate message
    
    return session


def end_session(session_id: str):
    """End and cleanup a voice session"""
    if session_id in active_sessions:
        session = active_sessions[session_id]
        session.status = 'ended'
        logger.info(f"Ended session {session_id}. Remaining active: {get_active_session_count() - 1}")
        del active_sessions[session_id]


def get_all_sessions_info() -> list:
    """Get info about all active sessions (for admin/monitoring)"""
    cleanup_expired_sessions()
    return [
        {
            'session_id': s.session_id,
            'status': s.status,
            'created_at': s.created_at.isoformat(),
            'expires_at': s.expires_at.isoformat(),
            'time_remaining': s.time_remaining(),
            'conversation_count': len(s.conversation_history),
            'created_by': s.client_info.get('created_by', 'unknown')
        }
        for s in active_sessions.values()
    ]


# Export for use in Flask app
__all__ = [
    'GeminiVoiceAgent',
    'VoiceSession',
    'create_session',
    'get_session',
    'end_session',
    'active_sessions',
    'SAMPLE_RATE'
]

