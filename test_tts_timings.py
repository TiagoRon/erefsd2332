import asyncio
from src.tts_engine import generate_audio

async def test_tts():
    text = "Hola, esto es una prueba de subtítulos para ver si coinciden."
    print(f"Testing TTS with: '{text}'")
    
    output_file = "test_tts_debug.mp3"
    success, timings = await generate_audio(text, output_file)
    
    if success:
        print("✅ TTS Success")
        print(f"Timings: {len(timings)} words")
        for t in timings:
            print(t)
    else:
        print("❌ TTS Failed")

    if not timings:
        print("⚠️ No timings received!")

if __name__ == "__main__":
    asyncio.run(test_tts())
