import os
import time
import asyncio
from typing import List, Dict, Any, Optional

def _get_pyttsx3_engine():
    try:
        import pyttsx3
        engine = pyttsx3.init()
        return engine
    except Exception as e:
        return None

def get_system_voices() -> List[Dict[str, Any]]:
    """
    Returns list of installed operating system voices via pyttsx3.
    """
    engine = _get_pyttsx3_engine()
    if not engine:
        return []
    
    voices = []
    try:
        raw_voices = engine.getProperty('voices') or []
        for v in raw_voices:
            # Detect language hints
            lang = "System Default"
            v_name_lower = v.name.lower()
            if "hindi" in v_name_lower or "hi-" in str(getattr(v, 'languages', '')).lower():
                lang = "Hindi"
            elif "india" in v_name_lower or "in-" in str(getattr(v, 'languages', '')).lower():
                lang = "English (India)"
            elif "us" in v_name_lower:
                lang = "English (US)"
            elif "gb" in v_name_lower or "uk" in v_name_lower:
                lang = "English (UK)"
            else:
                lang = "English"

            voices.append({
                "id": v.id,
                "name": f"{v.name} (OS)",
                "language": lang,
                "gender": "Unknown",
                "engine": "system",
                "description": f"Native OS synthesizer voice ({v.name})"
            })
    except Exception:
        pass
    finally:
        try:
            engine.stop()
        except Exception:
            pass
            
    return voices

def _synthesize_system_sync(text: str, voice_id: Optional[str], output_path: str, speed: float = 1.0, volume: int = 100):
    import pyttsx3
    engine = pyttsx3.init()
    try:
        if voice_id:
            engine.setProperty('voice', voice_id)
        
        # Base rate is around 180-200 WPM
        base_rate = 190
        target_rate = int(base_rate * speed)
        target_rate = max(80, min(400, target_rate))
        engine.setProperty('rate', target_rate)
        
        # Volume: 0.0 to 1.0
        engine.setProperty('volume', max(0.0, min(1.0, volume / 100.0)))
        
        engine.save_to_file(text, output_path)
        engine.runAndWait()
    finally:
        try:
            engine.stop()
        except Exception:
            pass

async def generate_system_speech(
    text: str,
    voice_id: Optional[str],
    output_path: str,
    speed: float = 1.0,
    volume: int = 100
) -> Dict[str, Any]:
    """
    Synthesizes speech using OS native engine in a non-blocking background thread.
    """
    start_time = time.time()
    await asyncio.to_thread(_synthesize_system_sync, text, voice_id, output_path, speed, volume)
    elapsed_ms = round((time.time() - start_time) * 1000, 1)
    file_size_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0

    return {
        "engine": "system",
        "voice": voice_id or "default",
        "speed": speed,
        "elapsed_ms": elapsed_ms,
        "file_size_bytes": file_size_bytes,
        "words_count": len(text.split()),
        "chars_count": len(text),
        "output_path": output_path
    }
