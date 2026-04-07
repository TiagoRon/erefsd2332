import os
import sys
from main import run_batch
from dotenv import load_dotenv

def cloud_main():
    """
    Entry point for Cloud/Docker execution.
    Reads configuration from Environment Variables.
    """
    # Load env vars from .env if present (for local testing)
    load_dotenv()
    
    print("--- AutoShorts Generator (Cloud Mode) ---")
    
    # 1. Get Configuration from ENV
    try:
        count = int(os.environ.get("VIDEO_COUNT", "1"))
    except ValueError:
        count = 1
        
    topic = os.environ.get("VIDEO_TOPIC", "").strip()
    if not topic: topic = None
    
    style = os.environ.get("VIDEO_STYLE", "curiosity")
    watermark = os.environ.get("WATERMARK_TEXT", "@AIShortsGenerator")
    lang = os.environ.get("LANGUAGE", "es")
    
    print(f"🔧 Config: Count={count}, Topic={topic if topic else 'Random'}, Style={style}, Lang={lang}")
    
    # 2. Run Batch
    try:
        generated = run_batch(count=count, topic=topic, style=style, watermark_text=watermark, lang=lang, log_func=print)
        if not generated:
             print("❌ Cloud Batch Failed: No videos were successfully generated (Possible API Key issue).")
             sys.exit(1)
        print("✅ Cloud Batch Completed Successfully.")
    except Exception as e:
        print(f"❌ Cloud Batch Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cloud_main()
