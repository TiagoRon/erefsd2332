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
    
    print(f"🔧 Config: Count={count}, Topic={topic if topic else 'Random'}, Style={style}")
    
    # 2. Run Batch
    try:
        run_batch(count=count, topic=topic, style=style, log_func=print)
        print("✅ Cloud Batch Completed Successfully.")
    except Exception as e:
        print(f"❌ Cloud Batch Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cloud_main()
