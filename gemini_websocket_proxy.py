"""
WebSocket proxy for live Gemini streaming
Keeps API key server-side, streams audio and transcripts bidirectionally
"""
import os
import json
import asyncio
import base64
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class GeminiWebSocketProxy:
    """Proxy for streaming audio to/from Gemini Live API"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        self.client = genai.Client(api_key=self.api_key)
        self.session: Optional[any] = None
        
    async def start_session(self, system_instruction: str, tools: list):
        """Start Gemini live session"""
        self.session = await self.client.aio.live.connect(
            model='gemini-2.0-flash-exp',
            config=types.LiveConnectConfig(
                response_modalities=['AUDIO'],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Puck'
                        )
                    )
                ),
                system_instruction=system_instruction,
                tools=tools if tools else None
            )
        )
        return self.session
        
    async def send_audio(self, audio_base64: str):
        """Send audio chunk to Gemini"""
        if not self.session:
            raise RuntimeError("Session not started")
        await self.session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[types.Blob(
                    data=audio_base64,
                    mime_type='audio/pcm;rate=16000'
                )]
            ),
            end_of_turn=False
        )
        
    async def receive_messages(self):
        """Generator for receiving messages from Gemini"""
        if not self.session:
            raise RuntimeError("Session not started")
        async for message in self.session.receive():
            yield message
            
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None

