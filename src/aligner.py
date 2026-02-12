
import whisper
import os

# Load model once globally to avoid reloading
# "tiny" is usually sufficient for single-language fast alignment and usually < 1GB VRAM
model = None

def load_model():
    global model
    if model is None:
        print("⏳ Loading Whisper model (tiny)...")
        model = whisper.load_model("tiny")
        print("✅ Whisper model loaded.")

import difflib

def get_word_timings(audio_path, text_hint=None):
    """
    Uses OpenAI Whisper to detect speech and aligns the 'text_hint' (Script)
    to the audio using Anchor-Based Alignment (Difflib).
    
    Strategy:
    1. Transcribe audio to get 'Detected Words' with timestamps.
    2. Find 'Anchors': Words that are identical in both Script and Detected text.
    3. Lock Anchors to their detected timestamps.
    4. Interpolate timestamps for mismatched/missing words (Hallucinations/Skips) 
       between the locked Anchors.
    """
    load_model()
    
    # 1. Transcribe
    try:
        # Use simple transcription
        result = model.transcribe(audio_path, word_timestamps=True, language="es")
    except Exception as e:
        print(f"❌ Whisper Error: {e}")
        return []

    # Collect Whisper Words (The "Truth" of Timing, but "Lie" of Text)
    detected_words = []
    for segment in result.get('segments', []):
        for w in segment.get('words', []):
            detected_words.append({
                'word': w['word'].strip().lower().replace('.', '').replace(',', ''),
                'start': w['start'],
                'end': w['end']
            })
            
    if not text_hint:
        return [{'word': w['word'], 'start': w['start'], 'end': w['end']} for segment in result.get('segments', []) for w in segment.get('words', [])]

    # 2. Prepare Script Words (The "Truth" of Text)
    script_words_raw = text_hint.split()
    script_words_norm = [w.lower().replace('.', '').replace(',', '') for w in script_words_raw]
    
    if not script_words_raw: return []
    if not detected_words: 
        # Fallback: Linear
        return linear_fallback(script_words_raw)

    # 3. Match Sequences
    # We match normalized lists
    matcher = difflib.SequenceMatcher(None, script_words_norm, [w['word'] for w in detected_words])
    
    final_timings = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        
        if tag == 'equal':
            # Perfect Match! Copy timestamps directly.
            for k in range(i2 - i1):
                script_idx = i1 + k
                detect_idx = j1 + k
                
                final_timings.append({
                    'word': script_words_raw[script_idx],
                    'start': detected_words[detect_idx]['start'],
                    'end': detected_words[detect_idx]['end']
                })
                
                
                
        elif tag == 'replace' or tag == 'delete':
            # Mismatch region where Script has words (a[i1:i2]).
            # 'replace': Script words differ from Detected words.
            # 'delete': Script has words that are NOT in Detected (Whisper missed them).
            # Action: Interpolate these Script words into the available time gap.
            
            # 1. Determine Time Boundaries (Anchors)
            # Start: End of previous block OR Start of audio
            start_time = final_timings[-1]['end'] if final_timings else detected_words[0]['start']
            
            # End: Start of next block (if available) OR End of mapped audio
            if j2 < len(detected_words):
                end_time = detected_words[j2]['start']
            else:
                # End of audio
                if j2 > 0: end_time = detected_words[j2-1]['end']
                else: end_time = start_time + 1.0
                
            # 2. Interpolate
            words_to_fit = script_words_raw[i1:i2]
            if not words_to_fit: continue
            
            duration = end_time - start_time
            
            # SLACK STEALING: If gap is too tight (e.g. < 0.1s), borrow time from previous word
            # to ensure the inserted words are visible.
            if duration < 0.2 and final_timings:
                prev_dur = final_timings[-1]['end'] - final_timings[-1]['start']
                # Steal up to half of previous word, max 0.3s
                steal_amount = min(0.3, prev_dur / 2)
                if steal_amount > 0.05:
                    start_time -= steal_amount
                    final_timings[-1]['end'] -= steal_amount
                    duration += steal_amount
            
            # Safety clamp
            if duration < 0.1: duration = 0.1 
            
            # Character weights
            total_chars = sum(len(w) for w in words_to_fit)
            if total_chars == 0: total_chars = 1
            
            curr_t = start_time
            for w in words_to_fit:
                w_dur = (len(w) / total_chars) * duration
                final_timings.append({
                    'word': w,
                    'start': curr_t,
                    'end': curr_t + w_dur
                })
                curr_t += w_dur
        
        elif tag == 'insert':
            # Detected has words [j1:j2] that Script doesn't.
            # Ignore (Whisper hallucination).
            pass

    return final_timings

def linear_fallback(words):
    print("⚠️ Using Linear Fallback.")
    curr = 0.0
    res = []
    for w in words:
        dur = 0.3
        res.append({'word': w, 'start': curr, 'end': curr+dur})
        curr += dur
    return res

if __name__ == "__main__":
    # Test
    # Create a dummy mp3 first or use existing
    pass
