"""
Real-time Gemini Live API streaming handler
Manages bidirectional audio/text streaming with Gemini 2.0
"""
import os
import json
import asyncio
import base64
from typing import Optional, Callable
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class GeminiLiveStream:
    """Handles real-time streaming with Gemini Live API"""
    
    def __init__(self, system_instruction: str, on_message: Callable, language_config: Optional[dict] = None):
        """
        Args:
            system_instruction: System prompt for Gemini
            on_message: Callback function to send messages to client
            language_config: Language configuration dict with keys: name, code, gemini_language_code, instruction_suffix
        """
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")

        self.client = genai.Client(api_key=self.api_key)
        self.system_instruction = system_instruction
        self.on_message = on_message
        self.language_config = language_config or {'gemini_language_code': 'en-US'}
        self.session = None
        self.loop = None
        self.running = False
        
    async def start(self):
        """Start Gemini live session"""
        print("[GEMINI LIVE] Starting session...")
        lang_code = self.language_config.get('gemini_language_code', 'en-US')
        print(f"[GEMINI LIVE] Language: {lang_code}")
        print(f"[GEMINI LIVE] System instruction includes strict language enforcement")
        
        # Build config with explicit language settings
        config_dict = {
            'response_modalities': ['AUDIO', 'TEXT'],
            'speech_config': types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Puck',
                        language_code=lang_code
                    )
                )
            ),
            'system_instruction': self.system_instruction
        }
        
        # Add input audio transcription language restriction
        # This forces Gemini to only transcribe in the specified language
        try:
            config_dict['input_audio_transcription'] = types.InputAudioTranscriptionConfig(
                language_code=lang_code
            )
        except (AttributeError, TypeError):
            # Fallback if the API structure is different
            try:
                config_dict['input_audio_transcription'] = {
                    'language_code': lang_code
                }
            except:
                pass
        
        self.session = await self.client.aio.live.connect(
            model='gemini-2.0-flash-exp',
            config=types.LiveConnectConfig(**config_dict)
        )
        
        self.running = True
        print("[GEMINI LIVE] Session started")
        
        # Start receiving messages
        asyncio.create_task(self._receive_loop())
        
    async def _receive_loop(self):
        """Continuously receive messages from Gemini"""
        try:
            async for message in self.session.receive():
                if not self.running:
                    break
                    
                # Parse and forward message to client
                msg_data = self._parse_gemini_message(message)
                if msg_data:
                    self.on_message(msg_data)
                    
        except Exception as e:
            print(f"[GEMINI LIVE] Receive error: {e}")
            self.on_message({'type': 'error', 'message': str(e)})
            
    def _parse_gemini_message(self, message) -> Optional[dict]:
        """Parse Gemini message into client-friendly format"""
        result = {}
        
        # Extract transcription
        if hasattr(message, 'server_content'):
            sc = message.server_content
            
            if hasattr(sc, 'input_transcription') and sc.input_transcription:
                transcript_text = sc.input_transcription.text
                
                # STRICT FILTER: Only allow English characters, numbers, and basic punctuation
                # Block any non-ASCII characters (Hindi, Spanish accents, etc.)
                import re
                # Check if text contains non-English characters
                if re.search(r'[^\x00-\x7F]', transcript_text):
                    # Contains non-ASCII characters - likely Hindi or other language
                    print(f"[LANGUAGE FILTER] Blocked non-English transcription: {transcript_text[:50]}...")
                    # Return None to ignore this transcription
                    return None
                
                result['type'] = 'user_transcript'
                result['text'] = transcript_text
                return result
                
            if hasattr(sc, 'output_transcription') and sc.output_transcription:
                result['type'] = 'model_transcript'
                result['text'] = sc.output_transcription.text
                return result
                
            # Extract audio
            if hasattr(sc, 'model_turn') and sc.model_turn:
                parts = sc.model_turn.parts
                for part in parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        result['type'] = 'model_audio'
                        result['data'] = part.inline_data.data
                        return result
        
        # Extract function calls (for dashboard updates)
        if hasattr(message, 'tool_call') and message.tool_call:
            if hasattr(message.tool_call, 'function_calls'):
                for fc in message.tool_call.function_calls:
                    result['type'] = 'function_call'
                    result['name'] = fc.name
                    result['args'] = fc.args
                    result['id'] = fc.id
                    return result
        
        return None
        
    async def send_audio(self, audio_base64: str, end_of_turn: bool = False):
        """Send audio chunk to Gemini"""
        if not self.session or not self.running:
            return
            
        try:
            await self.session.send(
                input=types.LiveClientRealtimeInput(
                    media_chunks=[types.Blob(
                        data=audio_base64,
                        mime_type='audio/pcm;rate=16000'
                    )]
                ),
                end_of_turn=end_of_turn
            )
        except Exception as e:
            print(f"[GEMINI LIVE] Send audio error: {e}")
            
    async def send_tool_response(self, function_id: str, response: dict):
        """Send function call response back to Gemini"""
        if not self.session or not self.running:
            return
            
        try:
            await self.session.send(
                tool_response=types.LiveClientToolResponse(
                    function_responses=[types.FunctionResponse(
                        id=function_id,
                        response=response
                    )]
                )
            )
        except Exception as e:
            print(f"[GEMINI LIVE] Tool response error: {e}")
            
    async def stop(self):
        """Stop the session"""
        print("[GEMINI LIVE] Stopping session...")
        self.running = False
        if self.session:
            await self.session.close()
            self.session = None
        print("[GEMINI LIVE] Session stopped")

