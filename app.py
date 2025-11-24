import re
import time
import torch
import asyncio
import numpy as np
from typing import Optional
from NeuTTS.engine import TTSEngine
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.responses import StreamingResponse


try:
    tts_engine = TTSEngine()
    user_voice_map = {}
    print("✅ TTSEngine loaded successfully.")
except Exception as e:
    print(f"❌ Error loading TTSEngine: {e}")
    tts_engine = None

app = FastAPI(title="Streaming TTS Service", version="1.0")

@app.get("/set_voice/", summary="Register a voice file and get a unique User ID.")
async def set_voice(
    audio_file: str = Query(..., description="The filename of the custom reference audio for the voice."),
    user_id: Optional[str] = Query(None, description="Optional: A preferred unique User ID.")
):
    """
    Registers a new speaker voice using a reference audio file. 
    It assigns or uses a unique User ID for this voice profile.
    
    This is the function that calls `tts_engine.add_speaker(audio_file)`.
    """
    if tts_engine is None:
        raise HTTPException(status_code=503, detail="TTS Engine is not available.")
        
    try:
        # The engine handles creating a unique ID if one isn't provided/valid.
        final_user_id = tts_engine.add_speaker(audio_file, speaker_id=user_id)
        user_voice_map[final_user_id] = audio_file # Store the mapping
        
        return {
            "message": "Speaker voice registered successfully.",
            "user_id": final_user_id,
            "audio_file": audio_file
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to register speaker: {e}")


async def stream_audio_generator(input_text: str, user_id: str, display_audio: bool):
    """
    An asynchronous generator that yields converted 16-bit PCM audio chunks.
    """
    if tts_engine is None:
        raise RuntimeError("TTS Engine is not initialized.")
        
    try:
        async for wav_float32 in tts_engine.stream_audio(input_text, user_id, display_audio=display_audio):
            # 1. Convert float32 array (-1.0 to 1.0) to int16 PCM (-32768 to 32767)
            wav_int16 = (wav_float32 * 32767).astype(np.int16)
            
            # 2. Convert the int16 NumPy array to raw bytes
            yield wav_int16.tobytes()
            
    except Exception as e:
        print(f"Error during audio generation: {e}")
        pass


@app.post("/v1/audio/speech", summary="Stream TTS audio (OpenAI compatible).")
async def tts_stream(
    input: str = Body(..., embed=True, description="The text to generate audio for."),
    voice: str = Body(..., embed=True, description="The 'voice' maps to our custom speaker user_id."),
    model: str = Body("tts-1", embed=True, description="Placeholder model name."), 
    response_format: str = Body("pcm", embed=True, description="Desired audio format.") 
):
    # In your logic, map the 'voice' back to your 'user_id'
    ## model and response format do not matter currently
    user_id = voice
    try:
        audio_generator = stream_audio_generator(
            input_text=input, 
            user_id=user_id, 
            display_audio=False
        )
        
        return StreamingResponse(
            audio_generator,
            media_type="application/octet-stream" 
            # The client must know the format (SR=24000, 16-bit, mono, little-endian)
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TTS generation failed: {e}")
