import os
import time
import edge_tts
from typing import Optional, Dict, Any

EDGE_VOICES = [
    {
        "id": "hi-IN-SwaraNeural",
        "name": "Swara (स्वर)",
        "language": "Hindi",
        "locale": "hi-IN",
        "gender": "Female",
        "engine": "edge",
        "description": "Warm, natural native Hindi female voice"
    },
    {
        "id": "hi-IN-MadhurNeural",
        "name": "Madhur (मधुर)",
        "language": "Hindi",
        "locale": "hi-IN",
        "gender": "Male",
        "engine": "edge",
        "description": "Clear, articulate native Hindi male voice"
    },
    {
        "id": "en-IN-NeerjaNeural",
        "name": "Neerja",
        "language": "English (India)",
        "locale": "en-IN",
        "gender": "Female",
        "engine": "edge",
        "description": "Authentic Indian English female voice"
    },
    {
        "id": "en-IN-PrabhatNeural",
        "name": "Prabhat",
        "language": "English (India)",
        "locale": "en-IN",
        "gender": "Male",
        "engine": "edge",
        "description": "Engaging Indian English male voice"
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny",
        "language": "English (US)",
        "locale": "en-US",
        "gender": "Female",
        "engine": "edge",
        "description": "Expressive American English female voice"
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy",
        "language": "English (US)",
        "locale": "en-US",
        "gender": "Male",
        "engine": "edge",
        "description": "Deep, confident American English male voice"
    },
    {
        "id": "en-US-AriaNeural",
        "name": "Aria",
        "language": "English (US)",
        "locale": "en-US",
        "gender": "Female",
        "engine": "edge",
        "description": "Professional, versatile US female voice"
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia",
        "language": "English (UK)",
        "locale": "en-GB",
        "gender": "Female",
        "engine": "edge",
        "description": "Refined British English female voice"
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan",
        "language": "English (UK)",
        "locale": "en-GB",
        "gender": "Male",
        "engine": "edge",
        "description": "Smooth British English male voice"
    }
]

def format_rate(speed: float) -> str:
    """Converts speed multiplier (e.g., 0.5 to 2.0) to edge-tts rate format (e.g., '+20%', '-30%')."""
    pct = int(round((speed - 1.0) * 100))
    pct = max(-50, min(100, pct))
    return f"{pct:+d}%"

def format_pitch(pitch: int) -> str:
    """Converts pitch offset (-50 to 50 Hz) to edge-tts pitch format."""
    p = max(-50, min(50, int(pitch)))
    return f"{p:+d}Hz"

async def generate_edge_speech(
    text: str,
    voice_id: str,
    output_path: str,
    speed: float = 1.0,
    pitch: int = 0,
    volume: int = 100
) -> Dict[str, Any]:
    """
    Synthesizes speech using edge-tts with rate/speed, pitch, and volume control.
    """
    start_time = time.time()
    
    # Format edge parameters
    rate_str = format_rate(speed)
    pitch_str = format_pitch(pitch)
    vol_str = f"{int(volume - 100):+d}%" if volume != 100 else "+0%"

    # Create Communicate instance
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_id,
        rate=rate_str,
        pitch=pitch_str,
        volume=vol_str
    )
    
    # Save audio stream to output file
    await communicate.save(output_path)
    
    elapsed_ms = round((time.time() - start_time) * 1000, 1)
    file_size_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    words_count = len(text.split())
    
    return {
        "engine": "edge",
        "voice": voice_id,
        "speed": speed,
        "pitch": pitch,
        "elapsed_ms": elapsed_ms,
        "file_size_bytes": file_size_bytes,
        "words_count": words_count,
        "chars_count": len(text),
        "rate_param": rate_str,
        "output_path": output_path
    }
