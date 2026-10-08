import utils.session
import os
import sys
import time
import uuid
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.tts_engines.hardware import get_system_telemetry
from backend.tts_engines.edge_engine import EDGE_VOICES, generate_edge_speech
from backend.tts_engines.system_engine import get_system_voices, generate_system_speech
from backend.tts_engines.mms_engine import MMS_VOICES, is_torch_available, generate_mms_speech, get_compute_device
from backend.utils import clean_script_text

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = BASE_DIR / "outputs" / "history.json"

app = FastAPI(
    title="VaniForge - Neural & Local TTS Studio",
    description="Cross-Platform Hindi & English Text-to-Speech Engine with Local Hardware Acceleration",
    version="1.0.0"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=15000, description="Text to synthesize")
    voice_id: str = Field(default="hi-IN-SwaraNeural", description="Voice identifier")
    engine: str = Field(default="edge", description="Engine: 'edge', 'mms', or 'system'")
    speed: float = Field(default=1.0, ge=0.5, le=2.5, description="Speaking rate multiplier")
    pitch: int = Field(default=0, ge=-50, le=50, description="Pitch offset in Hz (-50 to +50)")
    volume: int = Field(default=100, ge=0, le=100, description="Volume level 0 to 100%")

# In-Memory & File History Manager
def load_history() -> List[Dict[str, Any]]:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history: List[Dict[str, Any]]):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

@app.get("/api/system-info")
async def get_system_info():
    """Returns local system resources, CPU, RAM, and hardware acceleration status."""
    telemetry = get_system_telemetry()
    torch_available = is_torch_available()
    device, device_name = get_compute_device() if torch_available else (None, "PyTorch not loaded")
    
    telemetry["torch_available"] = torch_available
    telemetry["neural_device"] = device_name
    return telemetry

@app.get("/api/voices")
async def get_voices():
    """Returns all available Hindi and English voices categorized by engine and language."""
    all_voices = []
    
    # 1. Edge Neural Voices (Studio Quality)
    all_voices.extend(EDGE_VOICES)
    
    # 2. Local MMS Neural Voices (Offline Hardware Accelerated)
    all_voices.extend(MMS_VOICES)
    
    # 3. Native OS Voices
    try:
        sys_voices = get_system_voices()
        all_voices.extend(sys_voices)
    except Exception:
        pass
        
    return {
        "count": len(all_voices),
        "voices": all_voices,
        "torch_available": is_torch_available()
    }

@app.post("/api/synthesize")
async def synthesize_speech(req: SynthesizeRequest):
    """
    Synthesizes speech from text using the chosen engine, voice, and speed parameters.
    """
    text_stripped = clean_script_text(req.text).strip()
    if not text_stripped:
        text_stripped = req.text.strip()
    if not text_stripped:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Unique file identifier
    file_id = f"speech_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    is_wav = req.engine in ["system", "mms"]
    extension = ".wav" if is_wav else ".mp3"
    filename = f"{file_id}{extension}"
    file_path = str(OUTPUT_DIR / filename)

    start_time = time.time()
    result_meta = {}

    try:
        if req.engine == "edge":
            result_meta = await generate_edge_speech(
                text=text_stripped,
                voice_id=req.voice_id,
                output_path=file_path,
                speed=req.speed,
                pitch=req.pitch,
                volume=req.volume
            )
        elif req.engine == "mms":
            if not is_torch_available():
                raise HTTPException(
                    status_code=400,
                    detail="PyTorch & Transformers are required for local offline MMS models."
                )
            result_meta = await generate_mms_speech(
                text=text_stripped,
                model_id=req.voice_id,
                output_path=file_path,
                speed=req.speed
            )
        elif req.engine == "system":
            result_meta = await generate_system_speech(
                text=text_stripped,
                voice_id=req.voice_id,
                output_path=file_path,
                speed=req.speed,
                volume=req.volume
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported engine: '{req.engine}'")

    except Exception as e:
        # If output file was partially created, clean up
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")

    total_time_ms = round((time.time() - start_time) * 1000, 1)
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    words = len(text_stripped.split())
    words_per_sec = round(words / (total_time_ms / 1000.0), 1) if total_time_ms > 0 else 0

    item_meta = {
        "id": file_id,
        "filename": filename,
        "audio_url": f"/api/audio/{filename}",
        "text": text_stripped[:120] + ("..." if len(text_stripped) > 120 else ""),
        "full_text": text_stripped,
        "voice_id": req.voice_id,
        "engine": req.engine,
        "speed": req.speed,
        "pitch": req.pitch,
        "volume": req.volume,
        "words_count": words,
        "chars_count": len(text_stripped),
        "file_size_bytes": file_size,
        "generation_time_ms": total_time_ms,
        "words_per_sec": words_per_sec,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Record in history
    history = load_history()
    history.insert(0, item_meta)
    save_history(history)

    return {
        "success": True,
        "audio_url": f"/api/audio/{filename}",
        "filename": filename,
        "metadata": item_meta
    }

@app.get("/api/audio/{filepath:path}")
async def get_audio_file(filepath: str):
    """Streams generated audio file securely from OUTPUT_DIR."""
    target_path = (OUTPUT_DIR / filepath).resolve()
    if not str(target_path).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    media_type = "audio/wav" if target_path.suffix.lower() == ".wav" else "audio/mpeg"
    return FileResponse(
        path=str(target_path),
        media_type=media_type,
        filename=target_path.name
    )

@app.get("/api/history")
async def get_history():
    """Returns past generated audio clips."""
    return load_history()

@app.delete("/api/history/{item_id}")
async def delete_history_item(item_id: str):
    """Deletes an item from generation history and cleans up its audio file."""
    history = load_history()
    new_history = []
    deleted = False

    for item in history:
        if item.get("id") == item_id:
            filename = item.get("filename")
            if filename:
                fpath = OUTPUT_DIR / filename
                if fpath.exists():
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass
            deleted = True
        else:
            new_history.append(item)

    if deleted:
        save_history(new_history)
        return {"success": True, "message": "Item deleted."}
    raise HTTPException(status_code=404, detail="Item not found")

# Mount frontend directory for static UI serving
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "VaniForge TTS API is running. Frontend not found."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
