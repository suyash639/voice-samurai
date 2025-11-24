import requests
import os
from typing import Tuple
import base64

class VoiceService:
    """Service for handling ElevenLabs speech-to-text and text-to-speech."""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio to text using ElevenLabs STT.
        Falls back to Whisper API if ElevenLabs is not available.

        Args:
            audio_bytes: Raw audio file bytes

        Returns:
            Transcribed text
        """
        try:
            headers = {
                "xi-api-key": self.api_key
            }

            files = {
                "audio": ("audio.wav", audio_bytes, "audio/wav")
            }

            response = requests.post(
                f"{self.base_url}/speech-to-text",
                headers=headers,
                files=files,
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get("text", "")

            return self._transcribe_with_whisper(audio_bytes)

        except Exception as e:
            print(f"ElevenLabs transcription failed: {str(e)}")
            return self._transcribe_with_whisper(audio_bytes)

    def _transcribe_with_whisper(self, audio_bytes: bytes) -> str:
        """Fallback transcription using OpenAI Whisper API."""
        try:
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
            }

            files = {
                "file": ("audio.wav", audio_bytes, "audio/wav"),
                "model": (None, "whisper-1")
            }

            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get("text", "")

            raise Exception(f"Whisper API error: {response.text}")

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    def generate_speech(self, text: str) -> bytes:
        """
        Generate speech from text using ElevenLabs TTS.

        Args:
            text: Text to convert to speech

        Returns:
            Audio bytes
        """
        try:
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            response = requests.post(
                f"{self.base_url}/text-to-speech/{self.voice_id}",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.content

            raise Exception(f"ElevenLabs TTS error: {response.text}")

        except Exception as e:
            raise Exception(f"Speech generation failed: {str(e)}")