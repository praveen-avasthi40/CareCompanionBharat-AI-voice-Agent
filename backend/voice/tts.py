import os
import io
import tempfile
from typing import Optional, Dict
import requests
from gtts import gTTS
import base64

class IndianTTS:
    """
    Text-to-Speech for Indian languages
    Supports: Hindi, Tamil, Telugu, Bengali, English, Marathi, Gujarati
    Uses ElevenLabs (premium) with gTTS fallback
    """

    # Language codes for gTTS
    GTTS_LANGUAGE_CODES = {
        'hindi': 'hi',
        'tamil': 'ta',
        'telugu': 'te',
        'bengali': 'bn',
        'english': 'en',
        'marathi': 'mr',
        'gujarati': 'gu',
        'punjabi': 'pa',
        'urdu': 'ur',
        'kannada': 'kn',
        'malayalam': 'ml',
        'odia': 'or',
        'assamese': 'as'
    }

    # ElevenLabs voice IDs (you can change these)
    ELEVENLABS_VOICES = {
        'hindi': '21m00Tcm4TlvDq8ikWAM',  # Default voice - change as needed
        'tamil': '21m00Tcm4TlvDq8ikWAM',
        'telugu': '21m00Tcm4TlvDq8ikWAM',
        'bengali': '21m00Tcm4TlvDq8ikWAM',
        'english': '21m00Tcm4TlvDq8ikWAM',
    }

    def __init__(self):
        """Initialize TTS with API keys"""
        print("🚀 Initializing TTS...")

        # Load ElevenLabs API key from .env
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        # Check if ElevenLabs is available
        self.use_elevenlabs = bool(self.elevenlabs_key)

        if self.use_elevenlabs:
            print("✅ ElevenLabs enabled (premium quality)")
        else:
            print("ℹ️ ElevenLabs key not found, using gTTS (free)")

        print("✅ TTS Ready!")

    def text_to_speech(self, text: str, language: str = 'hindi') -> bytes:
        """
        Convert text to speech
        Returns audio bytes (MP3 format)
        """
        # Try ElevenLabs first if available
        if self.use_elevenlabs and language in self.ELEVENLABS_VOICES:
            try:
                audio = self._elevenlabs_tts(text, language)
                if audio:
                    return audio
            except Exception as e:
                print(f"ElevenLabs failed, falling back to gTTS: {e}")

        # Fallback to gTTS
        return self._gtts_tts(text, language)

    def _elevenlabs_tts(self, text: str, language: str) -> Optional[bytes]:
        """Use ElevenLabs API for high-quality TTS"""
        voice_id = self.ELEVENLABS_VOICES.get(language, self.elevenlabs_voice)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_key
        }

        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return response.content
        else:
            print(f"ElevenLabs error: {response.status_code}")
            return None

    def _gtts_tts(self, text: str, language: str) -> bytes:
        """Use gTTS for free TTS (supports Indian languages)"""
        lang_code = self.GTTS_LANGUAGE_CODES.get(language, 'hi')

        # gTTS for Indian languages
        tts = gTTS(text=text, lang=lang_code, slow=False)

        # Save to bytes
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()

    def get_supported_languages(self) -> Dict:
        """Return supported languages with their codes"""
        return {
            'gtts': list(self.GTTS_LANGUAGE_CODES.keys()),
            'elevenlabs': list(self.ELEVENLABS_VOICES.keys()) if self.use_elevenlabs else []
        }

    def save_to_file(self, text: str, filename: str, language: str = 'hindi'):
        """Save TTS output to file"""
        audio_bytes = self.text_to_speech(text, language)
        with open(filename, 'wb') as f:
            f.write(audio_bytes)
        print(f"✅ Audio saved to {filename}")


# Test function
if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Create TTS instance
    tts = IndianTTS()

    print("\n📝 Supported languages:")
    langs = tts.get_supported_languages()
    print(f"   gTTS: {', '.join(langs['gtts'][:5])}...")
    print(f"   ElevenLabs: {', '.join(langs['elevenlabs'])}")

    # Test in different languages
    print("\n🎤 Testing TTS...")

    test_texts = {
        'hindi': "नमस्ते, मैं केयरकंपेनियन बोल रहा हूँ। आप कैसे हैं?",
        'tamil': "வணக்கம், நான் கேர்கம்பேனியன் பேசுகிறேன். எப்படி இருக்கிறீர்கள்?",
        'telugu': "నమస్కారం, నేను కేర్‌కంపానియన్ మాట్లాడుతున్నాను. ఎలా ఉన్నారు?",
        'bengali': "নমস্কার, আমি কেয়ারকম্প্যানিয়ন বলছি। কেমন আছেন?",
        'english': "Hello, this is CareCompanion speaking. How are you?"
    }

    # Test each language (just first 2 for speed)
    for lang, text in list(test_texts.items())[:2]:
        print(f"\n{lang.upper()}: {text[:50]}...")
        audio = tts.text_to_speech(text, lang)
        print(f"   ✅ Generated {len(audio)} bytes of audio")

    # Save a sample file
    sample_file = "test_hindi.mp3"
    tts.save_to_file(test_texts['hindi'], sample_file, 'hindi')
    print(f"\n✅ Sample file created: {sample_file}")