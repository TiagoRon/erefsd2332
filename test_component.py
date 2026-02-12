
from src.video_editor import EffectsManager, create_karaoke_clips
from moviepy.editor import ColorClip, CompositeVideoClip
import os

def test_generation():
    print("Testing Video Generation Components...")
    
    # 1. Create Background
    print("Creating Background...")
    bg = ColorClip(size=(1080, 1920), color=(0, 0, 255), duration=3) # Blue
    
    # 2. Create Subtitles
    print("Creating Subtitles...")
    text = "Hello World Testing"
    timings = [
        {'word': 'Hello', 'start': 0.0, 'end': 1.0},
        {'word': 'World', 'start': 1.0, 'end': 2.0},
        {'word': 'Testing', 'start': 2.0, 'end': 3.0}
    ]
    
    overlays = create_karaoke_clips(timings, duration=3, start_offset=0, raw_text=text)
    print(f"Generated {len(overlays)} overlay clips.")
    
    # 3. Composite
    print("Compositing...")
    final = CompositeVideoClip([bg] + overlays, size=(1080, 1920))
    
    # 4. Write
    print("Writing video to test_output.mp4...")
    final.write_videofile("test_output.mp4", fps=24, codec='libx264')
    print("Done.")

if __name__ == "__main__":
    test_generation()
