"""
Gemini Real-Time Voice Agent for Senior Living Consultations
Uses Gemini 2.5 Flash Native Audio via google-genai SDK
Based on the bug-free reference implementation in sage---senior-living-voice-agent
"""

import os
import json
import asyncio
import base64
import logging
import uuid
import warnings
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Suppress SDK warnings about non-text/non-data parts
# These warnings occur when the SDK accesses .text/.data on multi-part responses
# We access parts directly, so these warnings are not relevant
warnings.filterwarnings('ignore', message='.*non-text parts.*')
warnings.filterwarnings('ignore', message='.*non-data parts.*')
warnings.filterwarnings('ignore', category=UserWarning, module='google_genai')

logger = logging.getLogger(__name__)

# Suppress warnings from google_genai SDK logger
# These warnings are about accessing .text/.data on multi-part responses
# We access parts directly, so these warnings are not relevant
google_genai_logger = logging.getLogger('google_genai.types')
google_genai_logger.setLevel(logging.ERROR)  # Only show errors, suppress warnings

# Audio configuration
SEND_SAMPLE_RATE = 16000   # Input audio must be 16kHz
RECEIVE_SAMPLE_RATE = 24000  # Output audio is 24kHz
SAMPLE_RATE = RECEIVE_SAMPLE_RATE  # For backward compatibility

# Model configuration - using the official model from Google AI Studio
MODEL = os.getenv('GEMINI_LIVE_MODEL', 'models/gemini-2.5-flash-native-audio-preview-09-2025')
if not MODEL.startswith('models/'):
    MODEL = f'models/{MODEL}'


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
    """Get the system instruction for the voice agent - matches reference exactly"""
    
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
1. GREETING: Introduce yourself warmly: "Hi! I'm Sage, your AI assistant for finding senior living communities."
2. INFORMATION GATHERING: Ask one at a time about Care Level, Budget, Location, Timeline, and Special Needs.
3. CONFIRM & SEARCH: When you have collected the info, say "Perfect! Let me search our database."
4. SMALL TALK: Chat naturally while waiting.

IMPORTANT RULES:
- Keep responses SHORT (2-3 sentences max for voice).
- Use natural speech patterns.
- Show empathy.
- {language_suffix}
"""


def get_live_config(language: str = 'english') -> types.LiveConnectConfig:
    """Get the Live API configuration - matches reference exactly"""
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=types.Content(
            parts=[types.Part(text=get_voice_system_instruction(language))]
        ),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Puck"  # Same as reference
                )
            )
        ),
        # Context window compression for longer conversations
        context_window_compression=types.ContextWindowCompressionConfig(
            trigger_tokens=25600,
            sliding_window=types.SlidingWindow(target_tokens=12800),
        ),
    )


class GeminiVoiceAgent:
    """Handles real-time voice conversations with Gemini - matches reference pattern"""
    
    def __init__(self, api_key: str, session_id: str, language: str = 'english'):
        self.api_key = api_key
        self.session_id = session_id
        self.language = language
        self.session = None
        self.is_connected = False
        self.collected_info = {}
        self.search_triggered = False
        self.recommendations_sent = False
        
        # Callbacks
        self.on_message_callback: Optional[Callable] = None
        self.on_audio_callback: Optional[Callable] = None
        self.on_status_callback: Optional[Callable] = None
        self.on_search_ready_callback: Optional[Callable] = None
        
        # Audio input queue (from client)
        self.audio_input_queue = asyncio.Queue()
        
        # Initialize client
        self.client = genai.Client(
            http_options={"api_version": "v1alpha"},
            api_key=api_key,
        )
    
    def parse_search_ready(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse the SEARCH_READY message from the agent"""
        import re
        
        if 'SEARCH_READY:' not in text:
            return None
        
        try:
            # Extract the parameters
            match = re.search(r'SEARCH_READY:\s*(.+?)(?:\.|$)', text, re.IGNORECASE)
            if not match:
                return None
            
            params_str = match.group(1)
            params = {}
            
            # Parse key=value pairs
            for pair in re.findall(r'(\w+)=\[([^\]]*)\]', params_str):
                key, value = pair
                params[key] = value.strip() if value.strip().lower() != 'none' else None
            
            # Map to our expected format
            return {
                'care_level': params.get('care_level', ''),
                'budget': params.get('budget', ''),
                'location': params.get('location', ''),
                'timeline': params.get('timeline', ''),
                'special_requirements': params.get('special_needs', '')
            }
        except Exception as e:
            logger.error(f"Error parsing SEARCH_READY: {e}")
            return None
    
    async def send_recommendations(self, recommendations: list):
        """Send recommendations back to the agent to speak to the user"""
        if not self.session or not recommendations:
            return
        
        # Format recommendations for the agent to speak
        results_text = "RESULTS: Here are the top matches:\n"
        
        for i, rec in enumerate(recommendations[:5], 1):
            name = rec.get('community_name', f"Community #{rec.get('community_id', i)}")
            price = rec.get('monthly_fee', rec.get('base_price', 'Price varies'))
            care = rec.get('care_level', 'Assisted Living')
            city = rec.get('city', '')
            score = rec.get('final_score', rec.get('score', 0))
            
            results_text += f"\n{i}. {name}"
            if city:
                results_text += f" in {city}"
            results_text += f" - ${price}/month, {care} care, match score {int(score*100)}%"
        
        results_text += "\n\nPlease present these to the caller in a friendly, conversational way."
        
        logger.info(f"Sending recommendations to agent: {results_text[:200]}...")
        
        try:
            await self.session.send(input=results_text, end_of_turn=True)
            self.recommendations_sent = True
        except Exception as e:
            logger.error(f"Error sending recommendations: {e}")
    
    async def run(self):
        """Main run loop - matches reference pattern exactly"""
        try:
            logger.info(f"Connecting to Gemini Live API for session {self.session_id}...")
            logger.info(f"Using model: {MODEL}")
            
            config = get_live_config(self.language)
            
            # Connect using async context manager (like reference)
            async with self.client.aio.live.connect(model=MODEL, config=config) as session:
                self.session = session
                self.is_connected = True
                
                logger.info(f"Gemini Voice Agent connected for session {self.session_id}")
                
                # Signal that we're ready
                if self.on_status_callback:
                    await self.on_status_callback('connected', 'Voice agent ready')
                
                # Use TaskGroup for concurrent tasks (like official Python example)
                async with asyncio.TaskGroup() as tg:
                    # Task 1: Send audio input to Gemini (processes queue immediately)
                    tg.create_task(self._send_audio_task())
                    
                    # Task 2: Receive responses from Gemini
                    tg.create_task(self._receive_responses_task())
                    
                    # Keep running until disconnected
                    while self.is_connected:
                        await asyncio.sleep(0.1)
                    
                    # Cancel tasks when done
                    raise asyncio.CancelledError("Session ended")
                        
        except asyncio.CancelledError:
            logger.info(f"Voice agent session cancelled for {self.session_id}")
        except ExceptionGroup as eg:
            logger.error(f"Voice agent task group error: {eg}")
            import traceback
            traceback.print_exception(eg)
        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            logger.info(f"Voice agent session ended for {self.session_id}")
            self.is_connected = False
            self.session = None
    
    async def _send_audio_task(self):
        """Send audio from queue to Gemini - matches reference pattern"""
        logger.info("Send audio task started")
        
        # Wait for session to be ready
        while not self.session and self.is_connected:
            await asyncio.sleep(0.1)
        
        if not self.session:
            logger.error("Session not available in send task")
            return
        
        while self.is_connected:
            try:
                # Get audio from queue (non-blocking with timeout)
                try:
                    audio_data = await asyncio.wait_for(self.audio_input_queue.get(), timeout=0.1)
                    
                    # Send immediately (like reference's sendRealtimeInput)
                    if self.session:
                        await self.session.send(
                            input={"data": audio_data, "mime_type": "audio/pcm"},
                            end_of_turn=False  # Continuous streaming
                        )
                except asyncio.TimeoutError:
                    continue
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error in send audio task: {e}")
                break
        
        logger.info("Send audio task ended")
    
    async def _receive_responses_task(self):
        """Receive responses from Gemini - matches reference pattern"""
        logger.info("Receive responses task started")
        accumulated_text = ""
        
        # Wait for session to be ready
        while not self.session and self.is_connected:
            await asyncio.sleep(0.1)
        
        if not self.session:
            logger.error("Session not available in receive task")
            return
        
        while self.is_connected:
            try:
                turn = self.session.receive()
                async for response in turn:
                    # Access nested structure directly (like TypeScript reference)
                    # message.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data
                    audio_data = None
                    text_data = None
                    
                    # Try to access server_content.model_turn.parts structure
                    try:
                        if hasattr(response, 'server_content') and response.server_content:
                            server_content = response.server_content
                            if hasattr(server_content, 'model_turn') and server_content.model_turn:
                                model_turn = server_content.model_turn
                                if hasattr(model_turn, 'parts') and model_turn.parts:
                                    for part in model_turn.parts:
                                        # Check for inline_data (audio)
                                        if hasattr(part, 'inline_data') and part.inline_data:
                                            if hasattr(part.inline_data, 'data'):
                                                audio_data = part.inline_data.data
                                        # Check for text
                                        elif hasattr(part, 'text') and part.text:
                                            text_data = part.text
                    except AttributeError:
                        # Fallback: try direct parts access
                        try:
                            if hasattr(response, 'parts') and response.parts:
                                for part in response.parts:
                                    if hasattr(part, 'inline_data') and part.inline_data:
                                        if hasattr(part.inline_data, 'data'):
                                            audio_data = part.inline_data.data
                                    elif hasattr(part, 'text') and part.text:
                                        text_data = part.text
                        except AttributeError:
                            pass
                    
                    # Handle audio data
                    if audio_data:
                        if self.on_audio_callback:
                            await self.on_audio_callback(audio_data)
                    
                    # Handle text
                    if text_data:
                        accumulated_text += text_data
                        logger.debug(f"Received text chunk: {text_data[:50]}...")
                        
                        if self.on_message_callback:
                            await self.on_message_callback('agent', text_data)
                    
                    # Handle interruptions
                    try:
                        if hasattr(response, 'server_content') and response.server_content:
                            if hasattr(response.server_content, 'interrupted') and response.server_content.interrupted:
                                logger.info("Response interrupted by user")
                                if self.on_status_callback:
                                    await self.on_status_callback('interrupted', 'Interrupted')
                    except AttributeError:
                        pass
                
                # Turn complete - check for SEARCH_READY trigger
                if accumulated_text and not self.search_triggered:
                    search_params = self.parse_search_ready(accumulated_text)
                    if search_params:
                        logger.info(f"SEARCH_READY detected: {search_params}")
                        self.search_triggered = True
                        self.collected_info = search_params
                        
                        if self.on_search_ready_callback:
                            await self.on_search_ready_callback(search_params)
                
                # Clear accumulated text for next turn
                accumulated_text = ""
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error in receive task: {e}")
                break
        
        logger.info("Receive responses task ended")
    
    async def send_audio(self, audio_data: bytes):
        """Queue audio data to send to Gemini (called from Flask handler)"""
        if not self.is_connected:
            return
        
        try:
            # Don't block if queue is full - drop oldest (like reference)
            if self.audio_input_queue.full():
                try:
                    self.audio_input_queue.get_nowait()
                except:
                    pass
            
            self.audio_input_queue.put_nowait(audio_data)
        except Exception as e:
            logger.error(f"Error queuing audio: {e}")
    
    async def send_text(self, text: str):
        """Send text message to Gemini directly"""
        if not self.is_connected or not self.session:
            return
        
        try:
            await self.session.send(input=text, end_of_turn=True)
        except Exception as e:
            logger.error(f"Error sending text: {e}")
    
    def disconnect(self):
        """Signal disconnect"""
        self.is_connected = False


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
    'SAMPLE_RATE',
    'SEND_SAMPLE_RATE',
    'RECEIVE_SAMPLE_RATE'
]
