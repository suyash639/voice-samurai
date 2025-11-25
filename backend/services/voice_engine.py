import requests
from typing import Optional
from config import config

class VoiceEngine:
    """Handles ElevenLabs speech-to-text and text-to-speech."""

    def __init__(self):
        self.api_key = config.ELEVENLABS_API_KEY
        self.base_url = config.ELEVENLABS_BASE_URL
        self.voice_id = config.ELEVENLABS_VOICE_ID

    def transcribe(self, file_obj: bytes) -> str:
        """
        Transcribe audio using ElevenLabs Scribe.

        Args:
            file_obj: Audio file bytes

        Returns:
            Transcribed text
        """
        try:
            headers = {
                "xi-api-key": self.api_key
            }

            files = {
                "audio": ("audio.wav", file_obj, "audio/wav")
            }

            response = requests.post(
                f"{self.base_url}/speech-to-text",
                headers=headers,
                files=files,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("text", "")
            else:
                raise Exception(f"ElevenLabs API error: {response.text}")

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    def speak(self, text: str) -> bytes:
        """
        Generate speech from text using ElevenLabs TTS.

        Args:
            text: Text to convert to speech

        Returns:
            Audio file bytes
        """
        try:
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "text": text,
                "model_id": config.ELEVENLABS_TTS_MODEL,
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
            else:
                raise Exception(f"ElevenLabs TTS error: {response.text}")

        except Exception as e:
            raise Exception(f"Speech generation failed: {str(e)}")
