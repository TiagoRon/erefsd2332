from src.aligner import get_word_timings
import os

def test_aligner():
    # File from previous test
    audio_path = "test_tts_debug.mp3"
    
    if not os.path.exists(audio_path):
        print("❌ test_tts_debug.mp3 not found. Run test_tts_timings.py first.")
        return

    # 1. Exact Match Test
    script_exact = "Hola esto es una prueba de subtítulos para ver si coinciden"
    print(f"\n--- Testing Exact Match ---\nScript: {script_exact}")
    timings = get_word_timings(audio_path, text_hint=script_exact)
    print(f"Result: {len(timings)} words aligned.")
    for t in timings:
        print(f"{t['word']}: {t['start']:.2f} - {t['end']:.2f}")

    # 2. Mismatch Test (Script has extra words / Hallucination simulation)
    # Audio says: "Hola esto es una prueba..."
    # Script says: "Hola AMIGOS esto es una GRAN prueba..."
    script_diff = "Hola AMIGOS esto es una GRAN prueba de subtítulos para ver si coinciden"
    print(f"\n--- Testing Mismatch (Insertions) ---\nScript: {script_diff}")
    timings_diff = get_word_timings(audio_path, text_hint=script_diff)
    print(f"Result: {len(timings_diff)} words aligned.")
    for t in timings_diff:
        print(f"{t['word']}: {t['start']:.2f} - {t['end']:.2f}")

if __name__ == "__main__":
    test_aligner()
