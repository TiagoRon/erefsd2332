import asyncio
import edge_tts
import os

import random

# List of high-quality Spanish Neural voices
AVAILABLE_VOICES = [
    "es-MX-DaliaNeural",  # Mexican Female
    "es-ES-AlvaroNeural", # Spanish Male
    "es-AR-TomasNeural",  # Argentine Male
    "es-MX-JorgeNeural",  # Mexican Male
    "es-US-AlonsoNeural", # US Spanish Male
    "es-US-PalomaNeural"  # US Spanish Female
]

def get_random_voice():
    return random.choice(AVAILABLE_VOICES)

async def generate_audio(text, output_file, voice=None):
    """
    Generates audio and returns a list of word-level timestamps.
    Returns: (success, metadata)
    metadata = [{'word': 'Hola', 'start': 0.0, 'end': 0.5}, ...]
    """
    if not voice:
        voice = get_random_voice() # Default random if not specified, though usually should be passed for consistency
        
    max_retries = 3
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            
            # We need to capture the subtitle data stream
            # edge-tts save() creates a file, but we want the VTT data too.
            # communicate.stream() yields chunks, some are audio, some are metadata.
            
            word_timings = []
            
            # We'll write the audio manually from the stream
            with open(output_file, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        # chunk structure for WordBoundary:
                        # {'type': 'WordBoundary', 'offset': 1234567, 'duration': 123456, 'text': 'word'}
                        # offset and duration are in 100ns units (ticks)
                        # 1s = 10,000,000 ticks
                        start_s = chunk["offset"] / 10_000_000
                        dur_s = chunk["duration"] / 10_000_000
                        word_timings.append({
                            "word": chunk["text"],
                            "start": start_s,
                            "end": start_s + dur_s
                        })

            return True, word_timings

        except Exception as e:
            print(f"⚠️ Error generating audio for '{text}' (Intento {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 * (attempt + 1)) # Backoff wait
            else:
                 print(f"❌ Falló definitivamente la generación de audio.")
                 return False, []
    
    # If we are here, success is True but we might have empty timings
    if not word_timings:
        print(f"⚠️ Warning: No WordBoundary events received for '{text[:20]}...'. Using fallback timing.")
        
    return True, word_timings

async def generate_full_audio(script_data, output_dir="output/temp_audio"):
    """
    Generates 3 separate audio files for hook, body, and climax.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    files = []
    parts = ["hook", "body", "climax"]
    
    for part in parts:
        text = script_data.get(part)
        if text:
            filename = os.path.join(output_dir, f"{part}.mp3")
            success = await generate_audio(text, filename)
            if success:
                files.append(filename)
            else:
                return None
    return files

if __name__ == "__main__":
    # Test run
    dummy_script = {"hook": "Hola", "body": "Mundo", "climax": "Adiós"}
    asyncio.run(generate_full_audio(dummy_script))



