// VaniForge Client Application Logic
document.addEventListener('DOMContentLoaded', () => {
    // State
    let allVoices = [];
    let selectedVoiceId = "hi-IN-SwaraNeural";
    let selectedEngine = "edge";
    let currentFilter = "all";
    let currentSpeed = 1.0;
    let currentPitch = 0;
    let isLooping = false;

    // Web Audio API Visualizer State
    let audioContext = null;
    let analyser = null;
    let audioSource = null;
    let visualizerAnimationId = null;

    // DOM Elements
    const textInput = document.getElementById('textInput');
    const charCount = document.getElementById('charCount');
    const wordCount = document.getElementById('wordCount');
    const clearTextBtn = document.getElementById('clearTextBtn');
    const voiceCardsContainer = document.getElementById('voiceCardsContainer');
    const langTabs = document.getElementById('langTabs');
    const speedSlider = document.getElementById('speedSlider');
    const speedValue = document.getElementById('speedValue');
    const pitchSlider = document.getElementById('pitchSlider');
    const pitchValue = document.getElementById('pitchValue');
    const speedChips = document.querySelectorAll('.speed-chip');
    const synthesizeBtn = document.getElementById('synthesizeBtn');
    const statusIndicator = document.getElementById('statusIndicator');

    // Player Elements
    const audioElement = document.getElementById('audioElement');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const playIcon = document.getElementById('playIcon');
    const pauseIcon = document.getElementById('pauseIcon');
    const replayBtn = document.getElementById('replayBtn');
    const loopBtn = document.getElementById('loopBtn');
    const timelineScrubber = document.getElementById('timelineScrubber');
    const currentTimeSpan = document.getElementById('currentTime');
    const totalDurationSpan = document.getElementById('totalDuration');
    const downloadAudioBtn = document.getElementById('downloadAudioBtn');
    const waveformCanvas = document.getElementById('waveformCanvas');
    const visualizerOverlay = document.getElementById('visualizerOverlay');
    const genMetricsBadge = document.getElementById('genMetricsBadge');

    // History & Telemetry Elements
    const historyList = document.getElementById('historyList');
    const historyCount = document.getElementById('historyCount');
    const deviceBadge = document.getElementById('deviceBadge');
    const osBadge = document.getElementById('osBadge');
    const ramBadge = document.getElementById('ramBadge');

    // Canvas Setup
    const canvasCtx = waveformCanvas.getContext('2d');

    // Presets Map
    const PRESETS = {
        'hindi-greet': "नमस्ते! VaniForge में आपका स्वागत है। आप अपनी स्थानीय हार्डवेयर गति और आवाज़ को यहाँ नियंत्रित कर सकते हैं।",
        'hindi-tech': "कृत्रिम बुद्धिमत्ता और मशीन लर्निंग तकनीक अब आपके कंप्यूटर के हार्डवेयर पर सीधे और अत्यधिक गति से काम कर रही है।",
        'english-natural': "Welcome to VaniForge Studio! Experience ultra-fast local neural speech synthesis powered directly by your machine's hardware.",
        'hinglish': "Hello dosto! Aaj hum apne local computer resources se ultra-fast speech generate kar rahe hain, bilkul high quality audio ke sath."
    };

    // 1. Initialize Hardware Telemetry
    async function loadTelemetry() {
        try {
            const res = await fetch('/api/system-info');
            if (!res.ok) return;
            const data = await res.json();
            
            osBadge.textContent = data.os || "Active";
            ramBadge.textContent = `${data.ram_available_gb} / ${data.ram_total_gb} GB`;
            
            if (data.is_apple_silicon || data.is_mps_available) {
                deviceBadge.textContent = "Apple Silicon M4 (MPS / Metal)";
            } else if (data.is_cuda_available) {
                deviceBadge.textContent = data.device_name || "NVIDIA CUDA";
            } else {
                deviceBadge.textContent = `${data.cpu_cores || 'Multi-core CPU'}`;
            }
        } catch (e) {
            deviceBadge.textContent = "Hardware Connected";
        }
    }

    // 2. Initialize Voices
    async function loadVoices() {
        try {
            const res = await fetch('/api/voices');
            if (!res.ok) throw new Error("Failed to load voices");
            const data = await res.json();
            allVoices = data.voices || [];
            renderVoiceCards();
        } catch (err) {
            voiceCardsContainer.innerHTML = `<div class="empty-history" style="color:#ef4444;">Failed to load voices. Backend offline?</div>`;
        }
    }

    function renderVoiceCards() {
        voiceCardsContainer.innerHTML = '';
        
        const filtered = allVoices.filter(v => {
            if (currentFilter === 'all') return true;
            if (currentFilter === 'Hindi') return v.language === 'Hindi';
            if (currentFilter === 'English (India)') return v.language === 'English (India)';
            if (currentFilter === 'English') return v.language.includes('English') && v.language !== 'English (India)';
            return true;
        });

        if (filtered.length === 0) {
            voiceCardsContainer.innerHTML = `<div class="empty-history">No voices match filter</div>`;
            return;
        }

        filtered.forEach(voice => {
            const card = document.createElement('div');
            card.className = `voice-card ${voice.id === selectedVoiceId ? 'selected' : ''}`;
            card.dataset.voiceId = voice.id;
            card.dataset.engine = voice.engine;

            let engineBadge = voice.engine === 'mms' ? 'Local Neural (Offline)' : (voice.engine === 'edge' ? 'Studio Neural' : 'OS Synthesizer');

            card.innerHTML = `
                <div class="voice-card-top">
                    <span class="voice-name">${voice.name}</span>
                    <span class="voice-gender-badge">${voice.gender || 'Neural'}</span>
                </div>
                <div class="voice-lang">${voice.language}</div>
                <div class="voice-engine-tag">${engineBadge}</div>
            `;

            card.addEventListener('click', () => {
                document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                selectedVoiceId = voice.id;
                selectedEngine = voice.engine;
            });

            voiceCardsContainer.appendChild(card);
        });
    }

    // Filter Tabs
    langTabs.addEventListener('click', (e) => {
        const btn = e.target.closest('.tab-btn');
        if (!btn) return;
        langTabs.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderVoiceCards();
    });

    // Text & Character Counters
    function updateTextStats() {
        const text = textInput.value.trim();
        charCount.textContent = `${textInput.value.length} characters`;
        const words = text ? text.split(/\s+/).length : 0;
        wordCount.textContent = `${words} words`;
    }
    textInput.addEventListener('input', updateTextStats);
    updateTextStats();

    clearTextBtn.addEventListener('click', () => {
        textInput.value = '';
        updateTextStats();
        textInput.focus();
    });

    // Preset Buttons
    document.querySelectorAll('.preset-btn[data-preset]').forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.dataset.preset;
            if (PRESETS[key]) {
                textInput.value = PRESETS[key];
                updateTextStats();
                // Auto switch filter for language convenience
                if (key.startsWith('hindi')) {
                    selectFilterTab('Hindi');
                } else if (key === 'english-natural') {
                    selectFilterTab('English');
                }
            }
        });
    });

    function selectFilterTab(filterName) {
        langTabs.querySelectorAll('.tab-btn').forEach(b => {
            if (b.dataset.filter === filterName) {
                b.click();
            }
        });
    }

    // Speed Slider & Quick Chips
    speedSlider.addEventListener('input', (e) => {
        currentSpeed = parseFloat(e.target.value);
        speedValue.textContent = `${currentSpeed.toFixed(2)}x`;
        updateSpeedChips(currentSpeed);
    });

    speedChips.forEach(chip => {
        chip.addEventListener('click', () => {
            currentSpeed = parseFloat(chip.dataset.speed);
            speedSlider.value = currentSpeed;
            speedValue.textContent = `${currentSpeed.toFixed(2)}x`;
            updateSpeedChips(currentSpeed);
        });
    });

    function updateSpeedChips(speed) {
        speedChips.forEach(c => {
            const val = parseFloat(c.dataset.speed);
            c.classList.toggle('active', Math.abs(val - speed) < 0.05);
        });
    }

    // Pitch Slider
    pitchSlider.addEventListener('input', (e) => {
        currentPitch = parseInt(e.target.value, 10);
        pitchValue.textContent = `${currentPitch > 0 ? '+' : ''}${currentPitch} Hz`;
    });

    // 3. Audio Synthesis Handler
    async function synthesizeSpeech() {
        const text = textInput.value.trim();
        if (!text) {
            statusIndicator.textContent = "Please enter some text first.";
            statusIndicator.style.color = "#f59e0b";
            return;
        }

        synthesizeBtn.disabled = true;
        statusIndicator.style.color = "var(--text-secondary)";
        statusIndicator.textContent = "Processing speech on system hardware...";
        genMetricsBadge.classList.add('hidden');

        try {
            const startTime = performance.now();
            const response = await fetch('/api/synthesize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    voice_id: selectedVoiceId,
                    engine: selectedEngine,
                    speed: currentSpeed,
                    pitch: currentPitch,
                    volume: 100
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Synthesis request failed.");
            }

            const data = await response.json();
            const clientLatency = Math.round(performance.now() - startTime);

            statusIndicator.textContent = "Speech synthesized successfully!";
            statusIndicator.style.color = "var(--accent-green)";

            // Show metrics badge
            genMetricsBadge.textContent = `⚡ Generated in ${data.metadata.generation_time_ms}ms (${data.metadata.words_per_sec || 0} wps)`;
            genMetricsBadge.classList.remove('hidden');

            // Load audio into player
            loadAudio(data.audio_url, true);

            // Refresh history
            loadHistory();

        } catch (err) {
            statusIndicator.textContent = `Error: ${err.message}`;
            statusIndicator.style.color = "#ef4444";
        } finally {
            synthesizeBtn.disabled = false;
        }
    }

    synthesizeBtn.addEventListener('click', synthesizeSpeech);

    // Keyboard Shortcut (Ctrl+Enter or Cmd+Enter)
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            synthesizeSpeech();
        }
    });

    // 4. Audio Player Controller
    function loadAudio(url, autoPlay = true) {
        audioElement.src = url;
        downloadAudioBtn.href = url;
        downloadAudioBtn.classList.remove('disabled');

        audioElement.onloadedmetadata = () => {
            totalDurationSpan.textContent = formatTime(audioElement.duration);
            timelineScrubber.max = audioElement.duration;
            timelineScrubber.value = 0;
            if (autoPlay) {
                playAudio();
            }
        };
    }

    function playAudio() {
        initAudioContext();
        audioElement.play().then(() => {
            playIcon.classList.add('hidden');
            pauseIcon.classList.remove('hidden');
            visualizerOverlay.classList.add('hidden');
        }).catch(err => {
            console.warn("Autoplay policy or audio error:", err);
        });
    }

    function pauseAudio() {
        audioElement.pause();
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
    }

    playPauseBtn.addEventListener('click', () => {
        if (audioElement.paused) {
            playAudio();
        } else {
            pauseAudio();
        }
    });

    replayBtn.addEventListener('click', () => {
        audioElement.currentTime = 0;
        playAudio();
    });

    loopBtn.addEventListener('click', () => {
        isLooping = !isLooping;
        audioElement.loop = isLooping;
        loopBtn.classList.toggle('active', isLooping);
    });

    audioElement.addEventListener('timeupdate', () => {
        currentTimeSpan.textContent = formatTime(audioElement.currentTime);
        timelineScrubber.value = audioElement.currentTime;
    });

    audioElement.addEventListener('ended', () => {
        if (!isLooping) {
            playIcon.classList.remove('hidden');
            pauseIcon.classList.add('hidden');
            visualizerOverlay.classList.remove('hidden');
        }
    });

    timelineScrubber.addEventListener('input', (e) => {
        audioElement.currentTime = parseFloat(e.target.value);
    });

    function formatTime(seconds) {
        if (!seconds || isNaN(seconds)) return "0:00";
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // 5. HTML5 Canvas Waveform Visualizer
    function initAudioContext() {
        if (audioContext) return;
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            audioContext = new AudioCtx();
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 128;
            analyser.smoothingTimeConstant = 0.8;

            audioSource = audioContext.createMediaElementSource(audioElement);
            audioSource.connect(analyser);
            analyser.connect(audioContext.destination);

            renderVisualizer();
        } catch (e) {
            console.warn("Web Audio API not allowed yet:", e);
        }
    }

    function renderVisualizer() {
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function draw() {
            visualizerAnimationId = requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);

            const width = waveformCanvas.width;
            const height = waveformCanvas.height;
            canvasCtx.clearRect(0, 0, width, height);

            const barWidth = (width / bufferLength) * 1.6;
            let barHeight;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                barHeight = (dataArray[i] / 255) * (height * 0.85);

                const gradient = canvasCtx.createLinearGradient(0, height, 0, 0);
                gradient.addColorStop(0, '#6366f1');
                gradient.addColorStop(0.5, '#06b6d4');
                gradient.addColorStop(1, '#34d399');

                canvasCtx.fillStyle = gradient;
                canvasCtx.beginPath();
                canvasCtx.roundRect(x, height - barHeight, barWidth - 2, barHeight, [4, 4, 0, 0]);
                canvasCtx.fill();

                x += barWidth;
            }
        }

        draw();
    }

    // 6. History Management
    async function loadHistory() {
        try {
            const res = await fetch('/api/history');
            if (!res.ok) return;
            const items = await res.json();
            renderHistory(items);
        } catch (e) {
            console.warn("Could not fetch history:", e);
        }
    }

    function renderHistory(items) {
        historyCount.textContent = `${items.length} items`;
        if (items.length === 0) {
            historyList.innerHTML = `<div class="empty-history">No generations yet. Type text and click Generate!</div>`;
            return;
        }

        historyList.innerHTML = '';
        items.forEach(item => {
            const el = document.createElement('div');
            el.className = 'history-item';
            el.innerHTML = `
                <div class="history-item-left">
                    <div class="history-text" title="${item.full_text || item.text}">${item.text}</div>
                    <div class="history-meta">${item.voice_id} • ${item.speed}x • ${item.generation_time_ms}ms • ${item.created_at || ''}</div>
                </div>
                <div class="history-item-actions">
                    <button type="button" class="btn-history-play" title="Play">▶ Play</button>
                    <button type="button" class="btn-history-del" title="Delete">✕</button>
                </div>
            `;

            el.querySelector('.btn-history-play').addEventListener('click', () => {
                loadAudio(item.audio_url, true);
            });

            el.querySelector('.btn-history-del').addEventListener('click', async (e) => {
                e.stopPropagation();
                try {
                    await fetch(`/api/history/${item.id}`, { method: 'DELETE' });
                    loadHistory();
                } catch (err) {}
            });

            historyList.appendChild(el);
        });
    }

    // Boot
    loadTelemetry();
    loadVoices();
    loadHistory();
});
