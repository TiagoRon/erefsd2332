import os
import requests
import random
import json

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def get_stock_image(query, output_path):
    """
    Searches Pexels for an image matching the query and downloads it.
    Returns True if successful, False otherwise.
    """
    if not PEXELS_API_KEY:
        print("⚠️ PEXELS_API_KEY not found. Skipping stock image.")
        return False

    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    url = "https://api.pexels.com/v1/search"
    
    attempts = [query, f"{query} - vertical", f"{query} portrait"]
    
    for q in attempts:
        if not q: continue
        params = {
            "query": q,
            "per_page": 5,
            "orientation": "landscape", # Better for overlays usually, or square
            "locale": "en-US"
        }
        
        try:
            print(f"   🖼️ Searching Pexels Image: '{q}'...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                photos = data.get('photos', [])
                if photos:
                    # Pick random
                    photo = random.choice(photos)
                    # Prefer 'large2x' or 'original'
                    img_url = photo['src'].get('large2x', photo['src'].get('original', photo['src'].get('large')))
                    
                    print(f"      ✅ Found image for '{q}' (ID: {photo['id']})")
                    
                    # Download
                    img_resp = requests.get(img_url, timeout=15)
                    with open(output_path, 'wb') as f:
                        f.write(img_resp.content)
                    return True
        except Exception as e:
            print(f"      ❌ Image search error: {e}")
    
    return False

def get_stock_video(query, duration_min, output_path, orientation='portrait', used_ids=None):
    """
    Searches Pexels for a video matching the query and downloads it.
    Returns True if successful, False otherwise.
    """
    if not PEXELS_API_KEY:
        print("⚠️ PEXELS_API_KEY not found in environment. Skipping stock footage.")
        return False

    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    # Search params
    url = "https://api.pexels.com/videos/search"
    
    # Strategy: Try specific -> Try broad -> Try simplified
    search_attempts = [
        f"{query} cinematic",         # 1. Ideal
        query,                        # 2. Raw
        " ".join(query.split()[:2])   # 3. First 2 words (Main subject usually)
    ]
    
    
    # Track usage if provided
    if used_ids is None:
        used_ids = set()

    for attempt_q in search_attempts:
        if not attempt_q or len(attempt_q) < 3: continue
        
        params = {
            "query": attempt_q,
            "per_page": 15, # Increased to have more candidates after filtering duplicates
            "orientation": orientation,
            "size": "medium",
            "locale": "en-US"
        }
        
        try:
            print(f"   🔍 Searching Pexels for: '{attempt_q}'...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                fetched_videos = data.get('videos', [])
                
                # Filter duplicates immediately
                valid_videos = [v for v in fetched_videos if v['id'] not in used_ids]
                
                if valid_videos:
                    print(f"      ✅ Found {len(valid_videos)} new videos for '{attempt_q}' (filtered {len(fetched_videos) - len(valid_videos)} duplicates)")
                    videos = valid_videos
                    break # Found something!
                else:
                    print(f"      ⚠️ Found {len(fetched_videos)} videos but ALL were duplicates. Trying next query...")
            
        except Exception as e:
            print(f"      ❌ Search error: {e}")
            
    if not videos:
        print(f"   ⚠️ No unique videos found after all attempts for '{query}'.")
        return False
            
    # Pick a random one from the candidates
    video_data = random.choice(videos)
    used_ids.add(video_data['id']) # Mark as used
    
    video_files = video_data.get('video_files', [])
    
    # PERFORMANCE OPTIMIZATION: Select best quality EFFICIENTLY
    # User Request: Don't download massive files if not needed.
    # Target: 1080p (1080x1920 or similar). Avoid 4K/UHD unless only option.
    
    best_file = None
    target_pixels = 1080 * 1920 # ~2 MP
    min_diff = float('inf')
    
    # 1. First pass: Look for HD (Mp4)
    candidates = [vf for vf in video_files if vf['file_type'] == 'video/mp4']
    
    if not candidates:
        candidates = video_files # Fallback to any type
        
    for vf in candidates:
        width = vf.get('width', 0)
        height = vf.get('height', 0)
        res = width * height
        
        # Calculate how far this is from target resolution
        # We prefer being slightly above target, or exactly on it.
        # But we strongly want to avoid Massive 4K (8MP+) if strictly not needed.
        
        diff = abs(res - target_pixels)
        
        # Penalize very low res (below 720p)
        if res < 720 * 1280:
             diff += 2000000 # Add penalty
             
        if diff < min_diff:
            min_diff = diff
            best_file = vf
            
    if not best_file:
        # Fallback to logic: Max Res (Old behavior)
        max_res = 0
        for vf in video_files:
             if vf['file_type'] == 'video/mp4':
                res = vf['width'] * vf['height']
                if res > max_res:
                    max_res = res
                    best_file = vf
    
    if not best_file:
        return False
        
    download_url = best_file['link']
    
    # Download
    print(f"   ⬇️ Downloading stock video... (ID: {video_data['id']} | {best_file['width']}x{best_file['height']})")
    try:
        vid_response = requests.get(download_url, stream=True, timeout=20)
        
        # PARTIAL DOWNLOAD SIMULATION (If stream allows stopping?)
        # Sadly standard MP4 atoms might be at the end. We must download full file usually.
        # But we optimized by choosing a smaller file (HD vs 4K).
        
        with open(output_path, 'wb') as f:
            for chunk in vid_response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"   ❌ Error downloading video: {e}")
        return False
