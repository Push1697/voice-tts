# VaniForge 🎙️ Neural Text-to-Speech Studio

An ultra-fast, local hardware-accelerated Text-to-Speech (TTS) workstation supporting **Hindi (हिन्दी)** and **English** voices with real-time speed, pitch, and acoustics control. Built to leverage local system resources on **Windows (CUDA / CPU)** and **macOS (Apple Silicon Mac mini M4 with Metal/MPS acceleration)**.

---

## ✨ Key Features

- 🇮🇳 **Native Hindi Voice Synthesis**: Authentic Devanagari script pronunciation and bilingual Hinglish phrasing.
- 🇬🇧/🇺🇸 **Studio English Voices**: Indian English (`en-IN`), US English (`en-US`), and British English (`en-GB`).
- ⚡ **Granular Speed Tuning**: Real-time speaking rate multiplier from `0.5x` (slow) up to `2.0x` (fast).
- 🎵 **Pitch & Tone Control**: Deep resonance (-30Hz) to crisp pitch (+30Hz).
- 🚀 **Hardware Acceleration & Telemetry**:
  - **Mac mini M4 / Apple Silicon**: Native Metal Performance Shaders (`torch.backends.mps`) & Apple Neural Engine.
  - **Windows**: NVIDIA CUDA acceleration (`torch.cuda`) or high-throughput multi-core CPU.
  - Real-time display of CPU load, RAM allocation, and active compute accelerator.
- 🌊 **Audio Waveform Visualizer**: Live HTML5 Web Audio API frequency analysis canvas.
- 📦 **Session Library & History**: Save, replay, download (MP3/WAV), and inspect generation latency.
- 🔌 **Multiple Synthesis Engines**:
  1. **Studio Neural (Edge-TTS)**: Studio broadcast fidelity, zero setup delay, low latency.
  2. **Offline Neural VITS (Meta MMS)**: 100% offline, local GPU/MPS execution (`facebook/mms-tts-hin` and `facebook/mms-tts-eng`).
  3. **Native OS Synthesizer (pyttsx3)**: Built-in operating system voices.

---

## 🚀 Quick Start Guide

### 🪟 Windows Setup

1. Double-click **`run.bat`** or run in PowerShell:
   ```powershell
   .\run.bat
   ```
2. The launcher automatically configures `.venv`, verifies dependencies, starts the server, and opens your browser at:
   ```
   http://127.0.0.1:8000
   ```

---

### 🍏 Mac mini M4 (Apple Silicon) Setup

The engine is optimized for the M4 chip's unified memory architecture and Metal Performance Shaders (MPS):

1. Open Terminal on your Mac mini M4 and navigate to the project folder:
   ```bash
   cd voice-tts
   ```
2. Make `run.sh` executable (first time only):
   ```bash
   chmod +x run.sh
   ```
3. Run the launcher:
   ```bash
   ./run.sh
   ```
4. It will automatically detect Apple Silicon (`arm64`), configure Python, and launch the studio at `http://127.0.0.1:8000`.

#### Manual Setup (Alternative):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

---

## 🎙️ Supported Voices

| Voice ID | Display Name | Language | Engine | Gender |
| :--- | :--- | :--- | :--- | :--- |
| `hi-IN-SwaraNeural` | **Swara (स्वर)** | Hindi | Studio Neural | Female |
| `hi-IN-MadhurNeural` | **Madhur (मधुर)** | Hindi | Studio Neural | Male |
| `en-IN-NeerjaNeural` | **Neerja** | English (India) | Studio Neural | Female |
| `en-IN-PrabhatNeural` | **Prabhat** | English (India) | Studio Neural | Male |
| `en-US-JennyNeural` | **Jenny** | English (US) | Studio Neural | Female |
| `en-US-GuyNeural` | **Guy** | English (US) | Studio Neural | Male |
| `en-GB-SoniaNeural` | **Sonia** | English (UK) | Studio Neural | Female |
| `facebook/mms-tts-hin` | **Meta MMS Hindi** | Hindi | Local Neural (VITS) | Neutral |
| `facebook/mms-tts-eng` | **Meta MMS English** | English | Local Neural (VITS) | Neutral |

---

## 🏗️ Project Architecture

```
voice-tts/
├── backend/
│   ├── app.py                      # FastAPI REST server & static UI router
│   └── tts_engines/
│       ├── edge_engine.py          # Edge Neural TTS handler (speed/pitch/volume)
│       ├── mms_engine.py           # Meta MMS VITS offline neural engine (MPS/CUDA)
│       ├── system_engine.py        # Native OS voice wrapper (pyttsx3)
│       └── hardware.py             # System telemetry & hardware accelerator detector
├── frontend/
│   ├── index.html                  # Responsive UI layout & audio player
│   ├── style.css                   # Glassmorphic dark theme & animations
│   └── app.js                      # Web Audio API visualizer & API controller
├── outputs/                        # Cached audio files & session history
├── requirements.txt                # Core cross-platform dependencies
├── requirements-neural.txt         # Offline neural model dependencies
├── run.bat                         # Windows 1-click launcher
└── run.sh                          # macOS (Mac mini M4) 1-click launcher
```

---

## ⚙️ REST API Endpoints

- `GET /api/system-info`: Hardware telemetry (OS, CPU cores, RAM, GPU/MPS acceleration status).
- `GET /api/voices`: Full catalog of available Hindi and English voices.
- `POST /api/synthesize`: Synthesize text to speech with JSON payload:
  ```json
  {
    "text": "नमस्ते, आपका स्वागत है!",
    "voice_id": "hi-IN-SwaraNeural",
    "engine": "edge",
    "speed": 1.25,
    "pitch": 0,
    "volume": 100
  }
  ```
- `GET /api/audio/{filename}`: Audio stream endpoint for playback and download.
- `GET /api/history`: Recent generations log.
