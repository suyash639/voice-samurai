from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import base64
import uuid
from datetime import datetime

from services.voice_service import VoiceService
from services.storage_service import StorageService
from services.brain_service import BrainService

load_dotenv()

app = FastAPI(
    title="Voice Samurai Backend",
    description="Browser agent that turns websites into voice interfaces",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

voice_service = VoiceService()
storage_service = StorageService()
brain_service = BrainService()

@app.on_event("startup")
async def startup_event():
    """Log startup."""
    print("Voice Samurai Backend started successfully")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Voice Samurai Backend"}

@app.post("/api/v1/voice/command")
async def process_voice_command(
        audio: UploadFile = File(...),
        dom_context: str = Form(...)
):
    """
    Process voice command and return action plan with audio response.

    Args:
        audio: Audio file uploaded by the client
        dom_context: JSON string containing page DOM structure

    Returns:
        JSON response with transcript, actions, and audio response
    """
    try:
        audio_bytes = await audio.read()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        audio_filename = f"audio_logs/{timestamp}_{unique_id}.wav"

        try:
            audio_url = storage_service.upload_file(
                audio_bytes,
                audio_filename,
                bucket=os.getenv("VULTR_BUCKET_NAME", "voice-samurai-logs")
            )
            print(f"Audio uploaded to: {audio_url}")
        except Exception as e:
            print(f"Failed to upload audio: {str(e)}")
            # Continue processing even if storage fails

        print(f"Transcribing audio...")
        transcript = voice_service.transcribe_audio(audio_bytes)

        if not transcript or transcript.strip() == "":
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Failed to transcribe audio",
                    "transcript": "",
                    "actions": [],
                    "audio_response_base64": ""
                }
            )

        print(f"Transcript: {transcript}")

        print(f"Generating action plan...")
        action_plan = brain_service.decide_action(transcript, dom_context)

        print(f"Generating speech response...")
        speak_text = action_plan.get("speak_before", "Command processed")
        response_audio_bytes = voice_service.generate_speech(speak_text)

        audio_response_base64 = base64.b64encode(response_audio_bytes).decode("utf-8")

        response_data = {
            "transcript": transcript,
            "thought": action_plan.get("thought", ""),
            "speak_before": action_plan.get("speak_before", ""),
            "actions": action_plan.get("actions", []),
            "audio_response_base64": audio_response_base64,
            "audio_log_url": audio_url if 'audio_url' in locals() else None
        }

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        print(f"Error processing voice command: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "transcript": "",
                "actions": [],
                "audio_response_base64": ""
            }
        )

@app.post("/api/v1/health/diagnostic")
async def diagnostic():
    """Diagnostic endpoint to check service availability."""
    diagnostics = {
        "voice_service": "ready",
        "storage_service": "ready",
        "brain_service": "ready",
        "elevenlabs_key": "configured" if os.getenv("ELEVENLABS_API_KEY") else "missing",
        "openai_key": "configured" if os.getenv("OPENAI_API_KEY") else "missing",
        "vultr_credentials": "configured" if os.getenv("VULTR_ACCESS_KEY") else "missing"
    }
    return JSONResponse(status_code=200, content=diagnostics)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )
