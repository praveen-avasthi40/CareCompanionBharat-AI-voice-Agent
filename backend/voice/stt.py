import json
import whisper
from typing import Dict, Optional, List, Union
import numpy as np
import tempfile
import wave
import contextlib

class MultilingualSTT:
    """
    Speech-to-Text for Indian languages using Whisper
    Supports 13+ Indian languages with auto-detection
    """

    # Whisper language codes for Indian languages
    LANGUAGE_CODES = {
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
        'assamese': 'as',
        'sanskrit': 'sa'
    }

    # Model sizes with their characteristics
    MODEL_SIZES = {
        'tiny': {'size_mb': 75, 'speed': 'fast', 'accuracy': 'basic'},
        'base': {'size_mb': 145, 'speed': 'fast', 'accuracy': 'good'},
        'small': {'size_mb': 488, 'speed': 'medium', 'accuracy': 'better'},
        'medium': {'size_mb': 1500, 'speed': 'slow', 'accuracy': 'best'},
        'large': {'size_mb': 2900, 'speed': 'very slow', 'accuracy': 'excellent'},
        'turbo': {'size_mb': 1500, 'speed': 'fast', 'accuracy': 'excellent'}
    }

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Initialize Whisper model

        Args:
            model_size: "tiny", "base", "small", "medium", "large", "turbo"
            device: "cpu" or "cuda" (GPU)
        """
        self.model_size = model_size
        self.device = device

        # Validate model size
        if model_size not in self.MODEL_SIZES:
            print(f"⚠️ Unknown model size: {model_size}. Using 'base'")
            model_size = "base"

        print(f"🚀 Loading Whisper {model_size} model for Indian languages...")
        print(f"   Device: {device.upper()}")

        try:
            self.model = whisper.load_model(model_size, device=device)
            print(f"✅ STT Model loaded! ({self.MODEL_SIZES[model_size]['size_mb']} MB)")
            print(f"   Speed: {self.MODEL_SIZES[model_size]['speed']}")
            print(f"   Accuracy: {self.MODEL_SIZES[model_size]['accuracy']}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("⚠️ Falling back to CPU with base model")
            try:
                self.model = whisper.load_model("base", device="cpu")
                print("✅ Fallback model loaded")
            except:
                self.model = None
                print("❌ CRITICAL: Could not load any model!")

    def _preprocess_audio(self, audio_path: str) -> str:
        """
        Preprocess audio for better transcription
        - Convert to mono if stereo
        - Normalize volume
        - Remove silence
        """
        try:
            import librosa
            import soundfile as sf

            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)

            # Normalize volume
            audio = audio / np.max(np.abs(audio))

            # Simple VAD (remove silence)
            # Using librosa.effects.trim
            audio_trimmed, _ = librosa.effects.trim(audio, top_db=20)

            if len(audio_trimmed) < 1000:  # Too short, use original
                audio_trimmed = audio

            # Save to temp file
            temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            sf.write(temp_path, audio_trimmed, sr)

            return temp_path

        except ImportError:
            # librosa not available, return original
            return audio_path
        except Exception as e:
            print(f"⚠️ Preprocessing failed: {e}")
            return audio_path

    def detect_language(self, audio_path: str) -> str:
        """
        Auto-detect language from audio

        Args:
            audio_path: Path to audio file

        Returns:
            Language name (e.g., 'hindi', 'tamil')
        """
        if not self.model:
            return 'english'

        try:
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)

            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            _, probs = self.model.detect_language(mel)
            detected_code = max(probs, key=probs.get)

            # Convert code to language name
            for lang_name, code in self.LANGUAGE_CODES.items():
                if code == detected_code:
                    return lang_name

            # If not found in our mapping, return based on code
            code_to_lang = {
                'hi': 'hindi', 'ta': 'tamil', 'te': 'telugu', 'bn': 'bengali',
                'en': 'english', 'mr': 'marathi', 'gu': 'gujarati', 'pa': 'punjabi',
                'ur': 'urdu', 'kn': 'kannada', 'ml': 'malayalam', 'or': 'odia',
                'as': 'assamese'
            }
            return code_to_lang.get(detected_code, 'english')

        except Exception as e:
            print(f"⚠️ Language detection failed: {e}")
            return 'english'

    def transcribe(self,
                   audio_path: str,
                   language: Optional[str] = None,
                   task: str = "transcribe",
                   **kwargs) -> Dict:
        """
        Transcribe audio to text

        Args:
            audio_path: Path to audio file
            language: Language code (auto-detected if None)
            task: "transcribe" or "translate" (to English)
            **kwargs: Additional Whisper parameters

        Returns:
            Dict with text, language, segments, and metadata
        """
        if not self.model:
            return {
                'text': 'नमस्ते, कैसे हैं आप?',
                'language': language or 'hindi',
                'segments': [],
                'error': 'Model not loaded'
            }

        # Preprocess audio
        processed_path = self._preprocess_audio(audio_path)

        try:
            # Detect language if not provided
            if not language:
                language = self.detect_language(processed_path)
                print(f"🎤 Auto-detected language: {language}")
            else:
                print(f"🎤 Transcribing in: {language}")

            lang_code = self.LANGUAGE_CODES.get(language, 'hi')

            # Get transcription
            result = self.model.transcribe(
                processed_path,
                language=lang_code,
                task=task,
                fp16=False,  # CPU compatibility
                verbose=False,
                **kwargs
            )

            # Clean up temp file if created
            if processed_path != audio_path and os.path.exists(processed_path):
                try:
                    os.unlink(processed_path)
                except:
                    pass

            return {
                'text': result['text'].strip(),
                'language': language,
                'confidence': result.get('segments', [{}])[0].get('confidence', 0.0) if result.get('segments') else 0.0,
                'segments': result['segments'],
                'duration': result.get('segments', [{}])[-1].get('end', 0) if result.get('segments') else 0
            }

        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return {
                'text': '',
                'language': language or 'english',
                'segments': [],
                'error': str(e)
            }

    def transcribe_file(self, audio_path: str, language: Optional[str] = None) -> str:
        """Simple transcribe - returns only text"""
        result = self.transcribe(audio_path, language)
        return result['text']

    def transcribe_batch(self, audio_paths: List[str], language: Optional[str] = None) -> List[Dict]:
        """Transcribe multiple audio files"""
        results = []
        for i, path in enumerate(audio_paths):
            print(f"Processing {i+1}/{len(audio_paths)}: {os.path.basename(path)}")
            results.append(self.transcribe(path, language))
        return results

    def get_audio_info(self, audio_path: str) -> Dict:
        """Get audio file information"""
        try:
            with contextlib.closing(wave.open(audio_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                channels = f.getnchannels()
                width = f.getsampwidth()

            return {
                'duration_seconds': duration,
                'sample_rate': rate,
                'channels': channels,
                'bit_depth': width * 8,
                'file_size': os.path.getsize(audio_path)
            }
        except:
            # Fallback using librosa if wave fails
            try:
                import librosa
                audio, sr = librosa.load(audio_path, sr=None)
                return {
                    'duration_seconds': len(audio) / sr,
                    'sample_rate': sr,
                    'channels': 1,
                    'file_size': os.path.getsize(audio_path)
                }
            except:
                return {'error': 'Could not read audio info'}

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return list(self.LANGUAGE_CODES.keys())

    def get_model_info(self) -> Dict:
        """Return model information"""
        return {
            'model_size': self.model_size,
            'device': self.device,
            'supported_languages': len(self.LANGUAGE_CODES),
            'languages': self.get_supported_languages(),
            'model_details': self.MODEL_SIZES.get(self.model_size, {})
        }


# ===== CONVENIENCE FUNCTIONS =====

def create_stt(model_size: str = "base", device: str = "cpu") -> MultilingualSTT:
    """Factory function to create STT instance"""
    return MultilingualSTT(model_size=model_size, device=device)


def quick_transcribe(audio_path: str, language: str = None) -> str:
    """Quick one-line transcription"""
    stt = MultilingualSTT("tiny")
    return stt.transcribe_file(audio_path, language)


# ===== TEST FUNCTION =====
if __name__ == "__main__":
    print("🔍 Testing Multilingual STT...")
    print("=" * 50)

    # Initialize with tiny model for quick testing
    stt = MultilingualSTT(model_size="tiny")

    print("\n📝 Model Info:")
    print(json.dumps(stt.get_model_info(), indent=2))

    print("\n🌐 Supported Languages:")
    print(f"   {', '.join(stt.get_supported_languages())}")
    print(f"   Total: {len(stt.get_supported_languages())}")

    print("\n💡 Usage Examples:")
    print('   # Basic transcription')
    print('   result = stt.transcribe("audio.wav")')
    print('   print(result["text"])  # नमस्ते, कैसे हैं आप?')
    print()
    print('   # With specific language')
    print('   result = stt.transcribe("audio.wav", language="tamil")')
    print()
    print('   # Batch transcription')
    print('   results = stt.transcribe_batch(["file1.wav", "file2.wav"])')
    print()
    print('   # Quick one-liner')
    print('   text = quick_transcribe("audio.wav")')

    print("\n✅ STT module ready!")

    # If there's a test audio file, try it
    import os
    test_files = [f for f in os.listdir('.') if f.endswith(('.wav', '.mp3'))]
    if test_files:
        print(f"\n🎤 Found test audio: {test_files[0]}")
        result = stt.transcribe(test_files[0])
        print(f"   Detected language: {result['language']}")
        print(f"   Transcription: {result['text'][:100]}...")