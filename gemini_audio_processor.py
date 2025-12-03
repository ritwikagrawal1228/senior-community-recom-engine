"""
Gemini 2.5 Flash Audio Processor via OpenRouter
Handles audio file processing using Gemini 2.5 Flash through OpenRouter API
"""
import os
import json
import time
import base64
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiAudioProcessor:
    """
    Audio processor using Gemini 2.5 Flash via OpenRouter
    - Supports direct audio file input via base64 encoding
    - Extracts structured client requirements
    - Lightweight and fast
    """

    def __init__(self):
        """Initialize OpenRouter API"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found in environment variables. "
                "Please add it to your .env file"
            )

        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_name = os.getenv('OPENROUTER_MODEL', 'google/gemini-2.5-flash')
        
        # OpenRouter requires HTTP-Referer header
        self.app_url = os.getenv('APP_URL', 'https://your-app.com')
        self.app_name = os.getenv('APP_NAME', 'Senior Living Recommendations')

    def process_audio_file(self, audio_path: str, language: str = 'english') -> Dict[str, Any]:
        """
        Process audio file and extract client requirements
        Uses OpenRouter API with base64-encoded audio

        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language constraint ('english', 'hindi', 'spanish')

        Returns:
            Dict with structured client requirements
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            # Validate file exists and is readable
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                raise ValueError(f"Audio file is empty: {audio_path}")
            
            # Check file extension
            file_ext = Path(audio_path).suffix.lower()
            supported_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac']
            if file_ext not in supported_extensions:
                raise ValueError(
                    f"Unsupported audio format '{file_ext}'. "
                    f"Supported formats: {', '.join(supported_extensions)}"
                )
            
            # Map file extensions to OpenRouter audio formats
            format_map = {
                '.mp3': 'mp3',
                '.wav': 'wav',
                '.m4a': 'm4a',
                '.ogg': 'ogg',
                '.webm': 'webm',
                '.flac': 'flac'
            }
            audio_format = format_map.get(file_ext, 'mp3')
            
            # Read and encode audio file to base64
            logger.info(f"Reading and encoding audio file: {audio_path}")
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Generate content with audio + extraction prompt
            extraction_prompt = self._create_extraction_prompt(language)
            
            # Prepare messages for OpenRouter API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": extraction_prompt
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": audio_format
                            }
                        }
                    ]
                }
            ]
            
            # Retry logic with exponential backoff for API overload errors
            response = self._retry_api_call(
                lambda: self._make_openrouter_request(messages, temperature=0.0),
                operation_name="audio processing"
            )
            
            result_text = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not result_text:
                raise ValueError("OpenRouter API returned empty response")
            
            # Clean up markdown code blocks if present
            if result_text.strip().startswith('```'):
                result_text = result_text.strip()
                if result_text.startswith('```json'):
                    result_text = result_text[7:]
                elif result_text.startswith('```'):
                    result_text = result_text[3:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
            
            parsed = json.loads(result_text)

            # Handle if Gemini returns a list instead of dict
            if isinstance(parsed, list):
                client_requirements = parsed[0] if parsed else {}
            else:
                client_requirements = parsed

            return client_requirements

        except Exception as e:
            raise RuntimeError(f"Failed to process audio: {str(e)}") from e

    def process_text_input(self, text: str, language: str = 'english') -> Dict[str, Any]:
        """
        Process text input (for testing without audio)

        Args:
            text: Client intake conversation text
            language: Language constraint ('english', 'hindi', 'spanish')

        Returns:
            Dict with structured client requirements
        """
        try:
            extraction_prompt = self._create_extraction_prompt(language)
            full_prompt = extraction_prompt + "\n\nCLIENT CONVERSATION:\n" + text

            # Prepare messages for OpenRouter API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": full_prompt
                        }
                    ]
                }
            ]

            # Retry logic with exponential backoff for API overload errors
            response = self._retry_api_call(
                lambda: self._make_openrouter_request(messages, temperature=0.1),
                operation_name="text processing"
            )

            result_text = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not result_text:
                raise ValueError("OpenRouter API returned empty response")
            
            parsed = json.loads(result_text)

            # Handle if Gemini returns a list instead of dict
            if isinstance(parsed, list):
                client_requirements = parsed[0] if parsed else {}
            else:
                client_requirements = parsed

            return client_requirements

        except Exception as e:
            raise RuntimeError(f"Failed to process text: {str(e)}") from e

    def _make_openrouter_request(self, messages: list, temperature: float = 0.0) -> Dict[str, Any]:
        """
        Make a request to OpenRouter API
        
        Args:
            messages: List of message objects
            temperature: Sampling temperature
            
        Returns:
            API response as dictionary
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.app_url,  # Required by OpenRouter
            "X-Title": self.app_name  # Optional but recommended
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"}  # Force JSON output
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        return response.json()

    def _retry_api_call(self, api_call_func, operation_name: str = "API call", max_retries: int = 5, initial_delay: float = 1.0):
        """
        Retry API call with exponential backoff for transient errors
        
        Args:
            api_call_func: Function that makes the API call (lambda)
            operation_name: Name of operation for logging
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            
        Returns:
            API response
            
        Raises:
            RuntimeError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return api_call_func()
            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response else None
                error_str = str(e).lower()
                
                # Check if it's a retryable error (503, 429, overload, unavailable)
                is_retryable = (
                    status_code == 503 or
                    status_code == 429 or
                    status_code == 502 or  # Bad Gateway
                    status_code == 504 or  # Gateway Timeout
                    'unavailable' in error_str or
                    'overloaded' in error_str or
                    'rate limit' in error_str or
                    'quota' in error_str or
                    'too many requests' in error_str
                )
                
                if not is_retryable:
                    # Not a retryable error, raise immediately
                    raise
                
                # If this is the last attempt, don't wait
                if attempt == max_retries - 1:
                    break
                
                # Calculate exponential backoff delay
                delay = initial_delay * (2 ** attempt)
                # Cap delay at 30 seconds
                delay = min(delay, 30.0)
                
                logger.warning(
                    f"⚠️ {operation_name} failed (attempt {attempt + 1}/{max_retries}): HTTP {status_code} - {str(e)[:100]}... "
                    f"Retrying in {delay:.1f}s..."
                )
                
                time.sleep(delay)
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check if it's a retryable error
                is_retryable = (
                    '503' in error_str or
                    '429' in error_str or
                    'unavailable' in error_str or
                    'overloaded' in error_str or
                    'rate limit' in error_str or
                    'quota' in error_str or
                    'timeout' in error_str or
                    'connection' in error_str
                )
                
                if not is_retryable:
                    # Not a retryable error, raise immediately
                    raise
                
                # If this is the last attempt, don't wait
                if attempt == max_retries - 1:
                    break
                
                # Calculate exponential backoff delay
                delay = initial_delay * (2 ** attempt)
                delay = min(delay, 30.0)
                
                logger.warning(
                    f"⚠️ {operation_name} failed (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}... "
                    f"Retrying in {delay:.1f}s..."
                )
                
                time.sleep(delay)
        
        # All retries exhausted
        error_msg = f"{operation_name} failed after {max_retries} attempts"
        logger.error(f"❌ {error_msg}: {str(last_exception)}")
        raise RuntimeError(f"{error_msg}. Last error: {str(last_exception)}") from last_exception

    def _create_extraction_prompt(self, language: str = 'english') -> str:
        """Create the extraction prompt for Gemini"""
        language_instruction = ""
        if language.lower() == 'english':
            language_instruction = "\nLANGUAGE CONSTRAINT: Only process and respond in English. Ignore any other languages spoken in the conversation."
        elif language.lower() == 'hindi':
            language_instruction = "\nLANGUAGE CONSTRAINT: Only process and respond in Hindi. Ignore any other languages spoken in the conversation."
        elif language.lower() == 'spanish':
            language_instruction = "\nLANGUAGE CONSTRAINT: Only process and respond in Spanish. Ignore any other languages spoken in the conversation."

        # Use regular string concatenation instead of f-string to avoid format specifier issues
        prompt = """
You are analyzing a senior living client intake conversation (either audio or text).""" + language_instruction + """
Extract the following information and return it as JSON:

{
  "care_level": "string (must be exactly one of: 'Independent Living', 'Assisted Living', 'Memory Care')",
  "enhanced": "boolean (true if they need Enhanced Assisted Living - higher medical care, nursing support, diabetes management, oxygen, etc.)",
  "enriched": "boolean (true if they need Enriched Housing Program - apartment-style with support services, meals, housekeeping, transportation)",
  "budget": "number (maximum monthly budget in dollars, extract just the number. If not mentioned, use null)",
  "timeline": "string (must be exactly one of: 'immediate', 'near-term', 'flexible')",
  "location_preference": "string (preferred ZIP code as 5-digit string OR city/area description like 'West side of Rochester'. If not mentioned, use null)",
  "special_needs": {
    "pets": "boolean (true if they have pets)",
    "apartment_type_preference": "string (if mentioned, e.g., 'studio', '1 bedroom', '2 bedroom')",
    "other": "string (any other special requirements)"
  },
  "client_name": "string (if mentioned, otherwise null)",
  "notes": "string (any additional important information)"
}

IMPORTANT DEFINITIONS:
- "Independent Living": Client is largely self-sufficient, needs minimal assistance
- "Assisted Living": Client needs help with daily activities (bathing, medication, meals)
- "Memory Care": Client has dementia/Alzheimer's requiring specialized care
- "Enhanced": Higher level medical care with nursing support (diabetes management, oxygen, foley/ostomy, injectable meds, etc.)
- "Enriched": Apartment-style supportive services (meals, housekeeping, transportation)
- "immediate": Needs to move in 0-1 months
- "near-term": Needs to move in 1-6 months
- "flexible": Timeline is 6+ months or unspecified

CRITICAL RULES:
1. For "care_level", use EXACTLY one of the three options listed
2. For "timeline", use EXACTLY one of: "immediate", "near-term", or "flexible"
3. For "budget", extract ONLY the numeric value (no $, no commas). If there is not budget mentioned set 50000 as the budget. 
4. For "location_preference" (IMPORTANT - READ CAREFULLY):
   - **PREFERRED**: Extract 5-digit ZIP code if mentioned (e.g., "14534", "14611", "14618")
   - Look for phrases like "ZIP 14534", "in 14611", "near 14618", "close to ZIP 14534"
   - If ZIP is implied by area name, infer the ZIP code:
     * "Brighton" or "Brighton area" = "14618"
     * "Pittsford" = "14534"
     * "Webster" = "14580"
     * "Penfield" = "14526"
     * "Greece" = "14626"
     * "Downtown Rochester" or "central Rochester" = "14604" (default to downtown)
     * "West Rochester" or "west side" = "14611"
     * "East Rochester" or "east side" = "14618"
     * "Rochester area" or "anywhere in Rochester" or just "Rochester" = "14604" (default to downtown)
     * "anywhere" without city = null
   - If city/area mentioned WITHOUT specific ZIP and not in the list above, use the area description
   - If nothing location-related is mentioned, use null
5. If something is not mentioned, use null (not "unknown" or empty string)
6. Return ONLY valid JSON, no markdown formatting, no extra text

Extract all available information from the conversation.
"""
        return prompt


def test_gemini_processor():
    """Test the Gemini audio processor with sample text"""
    print("="*80)
    print("TESTING GEMINI 2.5 FLASH AUDIO PROCESSOR (via OpenRouter)")
    print("="*80)

    processor = GeminiAudioProcessor()

    # Sample client conversation
    sample_conversation = """
    Consultant: Hello, I'm calling to help you find a senior living community. Can you tell me what type of care you're looking for?

    Client: Hi, yes. My mother needs assisted living. She's 82 and needs help with bathing and taking her medications. She's diabetic and needs some nursing support for her diabetes management.

    Consultant: I understand. What's your budget for monthly costs?

    Client: We can afford around $6,000 per month, maybe a bit more if it's really good.

    Consultant: And when are you looking to move her in?

    Client: Ideally within the next 2-3 months. We'd like to find something soon.

    Consultant: Do you have a preferred location or area?

    Client: We live in the 14534 ZIP code area, so somewhere close to that would be ideal. She also has a small cat that's very important to her.

    Consultant: Perfect, that helps a lot. I'll find some good options for you.
    """

    print("\n" + "-"*80)

    try:
        requirements = processor.process_text_input(sample_conversation)

        print("\n" + "="*80)
        print("EXTRACTED CLIENT REQUIREMENTS:")
        print("="*80)
        print(json.dumps(requirements, indent=2))
        print("="*80)

        return requirements

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    test_gemini_processor()
