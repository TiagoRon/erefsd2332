import asyncio
from src.tts_engine import generate_audio, AVAILABLE_VOICES

async def test_all_voices():
    text = "Prueba de tiempos."
    print(f"Testing {len(AVAILABLE_VOICES)} voices...")
    
    for voice in AVAILABLE_VOICES:
        print(f"\n🗣️ Testing voice: {voice}")
        output_file = f"test_{voice}.mp3"
        try:
            success, timings = await generate_audio(text, output_file, voice=voice)
            if success:
                if timings:
                    print(f"   ✅ OK! ({len(timings)} words)")
                else:
                    print(f"   ⚠️ No timings (Audio generated but no WordBoundary)")
            else:
                print(f"   ❌ Generation Failed")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_voices())
