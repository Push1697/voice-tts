import os
import sys
import asyncio
from pathlib import Path
import edge_tts

# Ensure utf-8 console output on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "nana_patekar"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Audio plan with fine-tuned rate, pitch, and dramatic pauses
PLAN_SEGMENTS = [
    {
        "index": 1,
        "segment_id": "01_hook_struggle",
        "title": "Hook & Humble Beginnings",
        "time_slot": "0–3 sec",
        "mood": "Somber, gritty, reflective",
        "text_hinglish": "Ek waqt tha… jab is aadmi ke paas na paisa tha, na koi filmi background.",
        "text_devanagari": "एक वक्त था… जब इस आदमी के पास ना पैसा था, ना कोई फिल्मी बैकग्राउंड।",
        "rate": "-7%",      # ~0.93x speed for dramatic weight
        "pitch": "-2Hz",    # Slightly deeper authority
        "voice": "hi-IN-MadhurNeural"
    },
    {
        "index": 2,
        "segment_id": "02_theatre_rise",
        "title": "Rise from Theatre to Stature",
        "time_slot": "3–8 sec",
        "mood": "Rising energy, impactful, powerful",
        "text_hinglish": "Lekin theatre se shuru hui ek journey ne… Nana Patekar ko Bollywood ke sabse powerful actors mein khada kar diya.",
        "text_devanagari": "लेकिन थिएटर से शुरू हुई एक जर्नी ने… नाना पाटेकर को बॉलीवुड के सबसे पावरफुल एक्टर्स में खड़ा कर दिया।",
        "rate": "+2%",      # ~1.02x speed for momentum
        "pitch": "+0Hz",
        "voice": "hi-IN-MadhurNeural"
    },
    {
        "index": 3,
        "segment_id": "03_power_presence",
        "title": "Iconic Screen Presence",
        "time_slot": "8–16 sec",
        "mood": "Deep reverence, measured, captivating",
        "text_hinglish": "Unki khaasiyat sirf unki awaaz nahi thi… unki aankhein, unki khamoshi, aur dialogue ke beech ka woh pause—sab kuch bolta tha.",
        "text_devanagari": "उनकी खासियत सिर्फ उनकी आवाज नहीं थी… उनकी आंखें, उनकी खामोशी, और डायलॉग के बीच का वो पॉज़—सब कुछ बोलता था।",
        "rate": "-5%",      # ~0.95x speed to let the 'pause' land heavily
        "pitch": "-2Hz",
        "voice": "hi-IN-MadhurNeural"
    },
    {
        "index": 4,
        "segment_id": "04_emotional_depth",
        "title": "Total Character Immersion",
        "time_slot": "16–23 sec",
        "mood": "Emotionally gripping, artistic respect",
        "text_hinglish": "Woh character ko sirf play nahi karte the… use itna real bana dete the, ki audience actor ko bhool jaati thi.",
        "text_devanagari": "वो कैरेक्टर को सिर्फ प्ले नहीं करते थे… उसे इतना रियल बना देते थे, कि ऑडियंस एक्टर को भूल जाती थी।",
        "rate": "-3%",      # ~0.97x speed
        "pitch": "-1Hz",
        "voice": "hi-IN-MadhurNeural"
    },
    {
        "index": 5,
        "segment_id": "05_curiosity_cliffhanger",
        "title": "The Cliffhanger Hook",
        "time_slot": "23–30 sec",
        "mood": "Mysterious, anticipation, hook for full video",
        "text_hinglish": "Lekin jis struggle ne Nana ko yeh banaya… uski kahani shayad unki films se bhi zyada interesting hai.",
        "text_devanagari": "लेकिन जिस स्ट्रगल ने नाना को ये बनाया… उसकी कहानी शायद उनकी फिल्मों से भी ज्यादा इंटरेस्टिंग है।",
        "rate": "+0%",      # 1.00x clean pacing
        "pitch": "+0Hz",
        "voice": "hi-IN-MadhurNeural"
    }
]

async def generate_voiceover():
    print("=" * 60)
    print("[INFO] Generating Nana Patekar Voiceover Audio Plan")
    print(f"[INFO] Output Directory: {OUTPUT_DIR}")
    print("=" * 60)

    # 1. Generate individual segment audio files (Stems)
    for seg in PLAN_SEGMENTS:
        stem_filename = f"{seg['segment_id']}.mp3"
        stem_path = OUTPUT_DIR / stem_filename
        
        # Devanagari provides the crispest native phonetic inflections in Hindi TTS
        text_to_speak = seg["text_devanagari"]
        
        comm = edge_tts.Communicate(
            text=text_to_speak,
            voice=seg["voice"],
            rate=seg["rate"],
            pitch=seg["pitch"]
        )
        await comm.save(str(stem_path))
        file_size = stem_path.stat().st_size
        print(f"[OK] Segment {seg['index']}/5 ({seg['time_slot']}): {stem_filename} ({file_size:,} bytes)")

    # 2. Generate Master Unified Audio Track
    master_text = (
        "एक वक्त था… जब इस आदमी के पास ना पैसा था, ना कोई फिल्मी बैकग्राउंड।\n\n"
        "लेकिन थिएटर से शुरू हुई एक जर्नी ने… नाना पाटेकर को बॉलीवुड के सबसे पावरफुल एक्टर्स में खड़ा कर दिया।\n\n"
        "उनकी खासियत सिर्फ उनकी आवाज नहीं थी… उनकी आंखें, उनकी खामोशी, और डायलॉग के बीच का वो पॉज़—सब कुछ बोलता था।\n\n"
        "वो कैरेक्टर को सिर्फ प्ले नहीं करते थे… उसे इतना रियल बना देते थे, कि ऑडियंस एक्टर को भूल जाती थी।\n\n"
        "लेकिन जिस स्ट्रगल ने नाना को ये बनाया… उसकी कहानी शायद उनकी फिल्मों से भी ज्यादा इंटरेस्टिंग है।"
    )
    master_path = OUTPUT_DIR / "nana_patekar_master_full.mp3"
    comm_master = edge_tts.Communicate(
        text=master_text,
        voice="hi-IN-MadhurNeural",
        rate="-4%",
        pitch="-1Hz"
    )
    await comm_master.save(str(master_path))
    print(f"\n[OK] Master Voiceover Track: {master_path.name} ({master_path.stat().st_size:,} bytes)")
    print("=" * 60)
    print("All audio files generated successfully!")

if __name__ == "__main__":
    asyncio.run(generate_voiceover())
