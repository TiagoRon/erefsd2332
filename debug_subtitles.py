
from src.video_editor import create_karaoke_clips
from moviepy.editor import ColorClip, CompositeVideoClip
import os

def test_subtitles():
    print("Testing Subtitle Generation...")
    
    # Long phrase that might cause issues
    text = "Esternocleidomastoideo y la desoxirribonucleico son palabras extremadamente largas para probar el ajuste"
    
    # Synthetic timings
    words = text.split()
    timings = []
    t = 0
    for w in words:
        timings.append({'word': w, 'start': t, 'end': t+0.5})
        t += 0.5
        
    print(f"Text: {text}")
    print("Generating clips...")
    
    clips = create_karaoke_clips(timings, duration=t, start_offset=0, raw_text=text, width=1080, height=1920)
    
    # Put them on a grey background to see boundaries
    bg = ColorClip(size=(1080, 1920), color=(50, 50, 50), duration=t)
    
    final = CompositeVideoClip([bg] + clips, size=(1080, 1920))
    
    output_file = "debug_subs.mp4"
    final.write_videofile(output_file, fps=24)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    test_subtitles()
