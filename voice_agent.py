"""
Gemini Real-Time Voice Agent for Senior Living Consultations
Uses Gemini 2.5 Flash Native Audio via google-genai SDK
Based on official Google AI Studio example
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

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

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
   - Introduce yourself warmly: "Hi! I'm Sage, your AI assistant for finding senior living communities."
   - Explain you'll ask a few questions to find the best matches
   - Ask if they're looking for themselves or a loved one

2. INFORMATION GATHERING (Ask one at a time, naturally):
   - Care Level: "What type of care are you looking for? Independent living, assisted living, or memory care?"
   - Budget: "What's your monthly budget range? For example, $3,000 to $5,000?"
   - Location: "What area or ZIP code do you prefer?"
   - Timeline: "When are you hoping to move? Immediately, in a few months, or just planning ahead?"
   - Special Needs: "Any special requirements? Like pets, couples, or specific medical needs?"

3. CONFIRM & SEARCH:
   When you have collected: care_level, budget, location, and timeline, you MUST say EXACTLY:
   "SEARCH_READY: care_level=[value], budget=[value], location=[value], timeline=[value], special_needs=[value or none]"
   
   Then say: "Perfect! Let me search our database of over 500 communities. This usually takes about 2 minutes. While I search, is there anything specific you're hoping to find in a community?"

4. SMALL TALK (While waiting for results):
   - Keep the conversation going naturally for 2-3 minutes
   - Ask about their interests, hobbies, what activities they enjoy
   - Share general info about what to expect in senior living
   - Periodically say "Still searching..." or "Almost done..."

5. WHEN YOU RECEIVE RESULTS:
   You will receive a message starting with "RESULTS:" containing the recommendations.
   Present them enthusiastically:
   - "Great news! I found some excellent matches for you!"
   - Present top 3 clearly with: name, location, price, care level, and why it's a good fit
   - Ask if they have questions about any community

IMPORTANT RULES:
- Keep responses SHORT (2-3 sentences max for voice)
- Use natural speech patterns
- Show empathy when discussing sensitive topics
- The SEARCH_READY message is critical - it triggers the actual search
- {language_suffix}
"""


def get_live_config(language: str = 'english') -> types.LiveConnectConfig:
    """Get the Live API configuration"""
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Puck"  # Friendly voice
                )
            )
        ),
        system_instruction=types.Content(
            parts=[types.Part(text=get_voice_system_instruction(language))]
        ),
        # Context window compression for longer conversations
        context_window_compression=types.ContextWindowCompressionConfig(
            trigger_tokens=25600,
            sliding_window=types.SlidingWindow(target_tokens=12800),
        ),
    )


class GeminiVoiceAgent:
    """Handles real-time voice conversations with Gemini using the official SDK"""
    
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
        self.on_search_ready_callback: Optional[Callable] = None  # Called when agent is ready to search
        
        # Audio queues
        self.audio_in_queue = None
        self.audio_out_queue = None
        
        # Tasks
        self._receive_task = None
        self._send_task = None
        
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
        """Main run loop - connects and handles the entire session lifecycle using TaskGroup"""
        try:
            logger.info(f"Connecting to Gemini Live API for session {self.session_id}...")
            logger.info(f"Using model: {MODEL}")
            
            config = get_live_config(self.language)
            
            # Use async with for both connection and task group (like official example)
            async with (
                self.client.aio.live.connect(model=MODEL, config=config) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.is_connected = True
                self.audio_in_queue = asyncio.Queue()
                self.audio_out_queue = asyncio.Queue(maxsize=5)
                
                logger.info(f"✅ Gemini Voice Agent connected for session {self.session_id}")
                
                # Signal that we're ready
                if self.on_status_callback:
                    await self.on_status_callback('connected', 'Voice agent ready')
                
                # Create concurrent tasks (like official Google example)
                tg.create_task(self._send_realtime_task())  # Sends audio from queue to Gemini
                tg.create_task(self._receive_task())         # Receives from Gemini
                
                # Start conversation - this will trigger the greeting
                await session.send(input="Hello, I'm ready to start the consultation.", end_of_turn=True)
                
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
            logger.error(f"❌ Failed to connect to Gemini: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            logger.info(f"Voice agent session ended for {self.session_id}")
            self.is_connected = False
            self.session = None
    
    async def _send_realtime_task(self):
        """Continuously send queued audio/text to Gemini (runs as concurrent task)"""
        logger.info("Send realtime task started")
        while self.is_connected:
            try:
                # Wait for item with timeout to allow checking is_connected
                try:
                    msg = await asyncio.wait_for(self.audio_out_queue.get(), timeout=0.1)
                    if self.session:
                        await self.session.send(input=msg)
                except asyncio.TimeoutError:
                    continue
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error in send task: {e}")
                break
        logger.info("Send realtime task ended")
    
    async def _receive_task(self):
        """Receive responses from Gemini and forward to callbacks (runs as concurrent task)"""
        logger.info("Receive task started")
        accumulated_text = ""
        
        while self.is_connected:
            try:
                turn = self.session.receive()
                async for response in turn:
                    # Handle audio data - send immediately to client
                    if response.data:
                        if self.on_audio_callback:
                            await self.on_audio_callback(response.data)
                    
                    # Handle text
                    if response.text:
                        accumulated_text += response.text
                        logger.debug(f"Received text chunk: {response.text[:50]}...")
                        
                        if self.on_message_callback:
                            await self.on_message_callback('agent', response.text)
                
                # Turn complete - check for SEARCH_READY trigger
                if accumulated_text and not self.search_triggered:
                    search_params = self.parse_search_ready(accumulated_text)
                    if search_params:
                        logger.info(f"🔍 SEARCH_READY detected: {search_params}")
                        self.search_triggered = True
                        self.collected_info = search_params
                        
                        if self.on_search_ready_callback:
                            await self.on_search_ready_callback(search_params)
                
                # Clear accumulated text for next turn
                accumulated_text = ""
                
                # Clear audio queue on turn complete (for interruptions - like official example)
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error in receive task: {e}")
                break
        
        logger.info("Receive task ended")
    
    async def send_audio(self, audio_data: bytes):
        """Queue audio data to send to Gemini"""
        if not self.is_connected:
            return
        
        try:
            # Don't block if queue is full - drop oldest
            if self.audio_out_queue.full():
                try:
                    self.audio_out_queue.get_nowait()
                except:
                    pass
            
            self.audio_out_queue.put_nowait({"data": audio_data, "mime_type": "audio/pcm"})
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
