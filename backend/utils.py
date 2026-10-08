import re

def clean_script_text(raw_text: str) -> str:
    """Removes video timing cues, bracketed directions, and cleans quotation marks."""
    # Remove bracketed timecodes/directions like [0-3 sec | HOOK], [3–8 sec | STRUGGLE], [MUSIC]
    text = re.sub(r'\[[^\]]*\]', '', raw_text)
    # Remove curly quotes
    text = text.replace('“', ' ').replace('”', ' ').replace('"', ' ')
    # Normalize multiple whitespaces and linebreaks
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n\n'.join(lines)

if __name__ == "__main__":
    test_input = """Ek waqt tha… jab is aadmi ke paas na paisa tha, na koi filmi background.”
[3–8 sec | STRUGGLE]
“Lekin theatre se shuru hui ek journey ne… Nana Patekar ko Bollywood ke sabse powerful actors mein khada kar diya.”
[8–16 sec | POWER]
“Unki khaasiyat sirf unki awaaz nahi thi…
unki aankhein, unki khamoshi, aur dialogue ke beech ka woh pause—sab kuch bolta tha.”
[16–23 sec | EMOTION]
“Woh character ko sirf play nahi karte the…
use itna real bana dete the, ki audience actor ko bhool jaati thi.”
[23–30 sec | CURIOSITY END]
“Lekin jis struggle ne Nana ko yeh banaya…
uski kahani shayad unki films se bhi zyada interesting hai."""

    cleaned = clean_script_text(test_input)
    print("=== CLEANED OUTPUT ===")
    print(cleaned)
