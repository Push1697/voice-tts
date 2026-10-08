import os
import time
import asyncio
from typing import Dict, Any, Optional

MMS_VOICES = [
    {
        "id": "facebook/mms-tts-hin",
        "name": "Meta MMS Hindi (Local Offline)",
        "language": "Hindi",
        "locale": "hi-IN",
        "gender": "Neutral / Native",
        "engine": "mms",
        "description": "100% Offline Neural VITS model. Runs on Apple Silicon MPS / NVIDIA CUDA / CPU."
    },
    {
        "id": "facebook/mms-tts-eng",
        "name": "Meta MMS English (Local Offline)",
        "language": "English",
        "locale": "en-US",
        "gender": "Neutral / Native",
        "engine": "mms",
        "description": "100% Offline Neural VITS model. Runs on Apple Silicon MPS / NVIDIA CUDA / CPU."
    }
]

_loaded_models = {}

def get_compute_device():
    """Detects best hardware device for PyTorch: MPS (Apple M4), CUDA (NVIDIA), or CPU."""
    try:
        import torch
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps"), "Apple Silicon MPS (Metal Performance Shaders)"
        elif torch.cuda.is_available():
            return torch.device("cuda"), f"NVIDIA CUDA ({torch.cuda.get_device_name(0)})"
        else:
            return torch.device("cpu"), "CPU"
    except Exception:
        return None, "Not Available"

def is_torch_available() -> bool:
    try:
        import torch
        import transformers
        return True
    except Exception:
        return False

def _load_model_sync(model_id: str):
    if model_id in _loaded_models:
        return _loaded_models[model_id]
    
    from transformers import VitsModel, AutoTokenizer
    import torch

    device, device_name = get_compute_device()
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = VitsModel.from_pretrained(model_id)
    if device:
        try:
            model = model.to(device)
        except Exception:
            device = torch.device("cpu")
            model = model.to(device)
            
    _loaded_models[model_id] = (model, tokenizer, device, device_name)
    return _loaded_models[model_id]

def _synthesize_mms_sync(text: str, model_id: str, output_path: str, speed: float = 1.0) -> Dict[str, Any]:
    import torch
    import scipy.io.wavfile
    import numpy as np

    start_time = time.time()
    model, tokenizer, device, device_name = _load_model_sync(model_id)
    
    inputs = tokenizer(text, return_tensors="pt")
    if device:
        inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        # VitsModel length_scale controls speaking rate (lower length_scale = faster speech)
        # length_scale = 1.0 / speed
        length_scale = float(1.0 / max(0.2, min(3.0, speed)))
        try:
            output = model(**inputs, speaking_rate=speed)
        except TypeError:
            # Fallback if speaking_rate is not direct kwarg
            try:
                output = model(**inputs)
            except Exception as e:
                raise e

    waveform = output.waveform[0].cpu().numpy()
    sample_rate = model.config.sampling_rate

    # If speed adjustment is needed and wasn't natively applied
    if abs(speed - 1.0) > 0.05 and 'speaking_rate' not in getattr(model.config, 'to_dict', lambda: {})():
        try:
            # High-fidelity speed adjustment via scipy interpolation / resampling
            num_samples = int(len(waveform) / speed)
            indices = np.linspace(0, len(waveform) - 1, num_samples)
            waveform = np.interp(indices, np.arange(len(waveform)), waveform)
        except Exception:
            pass

    # Normalize audio float32 to int16 for WAV compatibility
    audio_int16 = (waveform * 32767).astype(np.int16)
    scipy.io.wavfile.write(output_path, rate=sample_rate, data=audio_int16)
    
    elapsed_ms = round((time.time() - start_time) * 1000, 1)
    file_size_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0

    return {
        "engine": "mms",
        "voice": model_id,
        "speed": speed,
        "device_used": device_name,
        "elapsed_ms": elapsed_ms,
        "file_size_bytes": file_size_bytes,
        "sample_rate": sample_rate,
        "words_count": len(text.split()),
        "chars_count": len(text),
        "output_path": output_path
    }

async def generate_mms_speech(
    text: str,
    model_id: str,
    output_path: str,
    speed: float = 1.0
) -> Dict[str, Any]:
    """Runs local neural VITS inference in a worker thread."""
    return await asyncio.to_thread(_synthesize_mms_sync, text, model_id, output_path, speed)
