import os
import requests
import random
import json
import subprocess
import string
import threading
import time

yt_dlp_lock = threading.Lock()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def get_wikipedia_image(query, output_path):
    """
    Searches Wikipedia for the main high-res image of an article and downloads it.
    Returns True if successful, False otherwise.
    """
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "pageimages",
            "format": "json",
            "piprop": "original",
            "titles": query,
            "redirects": 1
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        print(f"   🏛️ Buscando imagen histórica en Wikipedia: '{query}'...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id == "-1": continue
                if "original" in page_info and "source" in page_info["original"]:
                    img_url = page_info["original"]["source"]
                    
                    # Avoid svg vectors as Pillow might fail, fallback gracefully
                    if img_url.lower().endswith(".svg"): continue
                    
                    print(f"      ✅ Imagen histórica encontrada ({img_url.split('/')[-1]})")
                    img_resp = requests.get(img_url, headers=headers, timeout=15)
                    with open(output_path, 'wb') as f:
                        f.write(img_resp.content)
                    return True
    except Exception as e:
        print(f"      ❌ Error buscando en Wikipedia: {e}")
        
    return False


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

def get_stock_video(query, duration_min, output_path, orientation='portrait', used_ids=None, is_cancelled=None, strict_match=False):
    """
    Searches Pexels for a video matching the query and downloads it.
    If strict_match is True, it filters out fuzzy results by checking if the query is in the video URL.
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
    
    # Strategy: Try EXACT query first, then mild modifiers for variety
    # IMPORTANT: Raw query FIRST for best relevance. Avoid abstract modifiers.
    # Added modern, high-quality, professional modifiers
    cinematic_modifiers = ["cinematic 4k", "high quality realistic", "documentary professional", "unreal engine 5 cinematic", "real footage 8k"]
    modifier = random.choice(cinematic_modifiers)
    
    search_attempts = [
        query,                             # 1. Raw query (best relevance)
        f"{query} {modifier}",             # 2. With modern cinematic modifier
        f"{' '.join(query.split()[:2])} documentary 4k",  # 3. First 2 words + documentary 4k
        " ".join(query.split()[:2])        # 4. First 2 words only (broad fallback)
    ]
    
    
    # Track usage if provided
    if used_ids is None:
        used_ids = set()

    videos = [] # Initialize to avoid UnboundLocalError if no matches found

    for attempt_q in search_attempts:
        if not attempt_q or len(attempt_q) < 3: continue
        
        params = {
            "query": attempt_q,
            "per_page": 20, # Large pool for better content matching
            "orientation": orientation,
            "locale": "en-US"
        }
        
        try:
            print(f"   🔍 Searching Pexels for: '{attempt_q}'...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                fetched_videos = data.get('videos', [])
                
                # Filter duplicates and apply strict match if requested
                valid_videos = []
                for v in fetched_videos:
                    if v['id'] in used_ids: continue
                    
                    if strict_match:
                         v_url = v.get('url', '').lower()
                         name_dashed = query.lower().replace(" ", "-")
                         # To be slightly lenient, we check if the MAIN query word is in the url
                         if name_dashed not in v_url:
                              continue # Reject fuzzy hallucination
                    
                    valid_videos.append(v)
                
                if valid_videos:
                    print(f"      ✅ Found {len(valid_videos)} new videos for '{attempt_q}' (filtered {len(fetched_videos) - len(valid_videos)} matches/duplicates)")
                    videos = valid_videos
                    break # Found something!
                else:
                    if strict_match:
                         print(f"      ⚠️ Found {len(fetched_videos)} videos but NONE passed the strict name filter. Trying next query...")
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
    # Target: 720p (720x1280 or similar). No need for higher since output is 720p.
    
    best_file = None
    target_pixels = 720 * 1280 # ~0.9 MP (matches output resolution)
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
            for chunk in vid_response.iter_content(chunk_size=65536):
                if is_cancelled and is_cancelled():
                    print("🛑 Download Cancelled by User.")
                    return False
                f.write(chunk)
        return True
    except Exception as e:
        print(f"   ❌ Error downloading video: {e}")
        return False

def get_giphy_video(query, output_path):
    """
    Searches Giphy and downloads an MP4 version of the GIF.
    """
    print(f"   👾 Búsqueda de Giphy para: {query}")
    # Usando una api key de prueba temporal pública (usada a menudo en desarrollo, o una genérica).
    # Idealmente, deberías usar tu propia API key de Giphy.
    GIPHY_API_KEY = os.getenv("GIPHY_API_KEY", "P1YIfu6s9a28q7j2v2XG02N3vX6P70gZ") 
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={query}&limit=5&rating=g"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            gifs = data.get('data', [])
            if gifs:
                gif = random.choice(gifs)
                # Intentar agarrar el MP4 directamente
                mp4_url = gif.get('images', {}).get('original', {}).get('mp4')
                if mp4_url:
                    print(f"      ✅ GIF (MP4) encontrado en Giphy.")
                    resp = requests.get(mp4_url, timeout=15)
                    with open(output_path, 'wb') as f:
                        f.write(resp.content)
                    return True
        print("      ⚠️ No se encontró GIF o MP4.")
    except Exception as e:
        print(f"      ❌ Error buscando en Giphy: {e}")
    return False

def get_youtube_clip(query, output_path, duration=4.0):
    """
    Searches YouTube for a specific movie/scene/person and downloads a short clip.
    Uses yt-dlp with multiple search strategies to maximize hit rate for movies/actors.
    Returns True if successful, False otherwise.
    """
    print(f"   🎥 Buscando en YouTube: '{query}'...")
    try:
        import yt_dlp
    except ImportError:
        print("      ❌ Error: yt-dlp no está instalado. Ejecuta: pip install yt-dlp")
        return False

    # Multiple search strategies in order of specificity
    # We prioritize the raw query FIRST because the AI is now trained to provide smart
    # contextual suffixes (like 'logo b-roll', 'interview', 'scene').
    search_attempts = [
        f"ytsearch1:{query}",
        f"ytsearch1:{query} escena oficial",
        f"ytsearch1:{query} scene",
        f"ytsearch1:{query} clip",
        f"ytsearch1:{query} anime scene",
        f"ytsearch1:{query} short scene",
    ]

    ydl_opts_info = {
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,  # Don't hang forever
    }
    
    if os.path.exists("cookies.txt"):
        # Solo cargar si el archivo tiene algo útil, para evitar clavar a yt-dlp con archivos vacíos
        try:
            with open("cookies.txt", "r") as f:
                if ".youtube.com" in f.read():
                    ydl_opts_info["cookiefile"] = "cookies.txt"
        except: pass

    video = None
    url = None
    vid_duration = 0

    with yt_dlp_lock:
        time.sleep(random.uniform(1.0, 3.0)) # Stagger requests to avoid IP bot block
        for search_q in search_attempts:
            try:
                with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                    print(f"      🔍 Probando búsqueda: '{search_q}'...")
                    info = ydl.extract_info(search_q, download=False)
                    candidate = None
                    if info and 'entries' in info and len(info['entries']) > 0:
                        candidate = info['entries'][0]
                    elif info:
                        candidate = info

                    if candidate and candidate.get('duration', 0) > 0:
                        video = candidate
                        vid_duration = video.get('duration', 0)
                        url = video.get('webpage_url') or video.get('url')
                        print(f"      ✅ Encontrado: '{video.get('title', '?')}' ({vid_duration}s)")
                        break  # Successful — stop trying
            except Exception as e:
                print(f"      ⚠️ Búsqueda fallida ({search_q}): {e}")
                continue

    if not video or not url:
        print(f"      ⚠️ No se encontró ningún video en YouTube para '{query}'.")
        return False

    # Fetch the climax/core of the video (30% in) to ensure relevance and skip intros.
    if vid_duration <= duration:
        start_time = 0
    else:
        start_time = max(0, int(vid_duration * 0.30))

    end_time = start_time + duration

    # Download the specific section
    # Use a .mp4 output; yt-dlp may append a format suffix so we look for the file after
    temp_output = output_path.replace(".mp4", "_yt_raw.mp4")

    ydl_opts_download = {
        # Prefer video+audio merged; fallback to single pre-merged file if ffmpeg fails to mux
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best',
        'outtmpl': temp_output,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 20,
        'merge_output_format': 'mp4',
        # Download only the needed section cleanly (RE-ENCODE)
        # We explicitly omit 'force_keyframes_at_cuts' to ensure ffmpeg re-encodes the snippet
        # cleanly, providing an I-Frame at t=0 so MoviePy doesn't generate grey/glitchy screens!
        'download_ranges': yt_dlp.utils.download_range_func(None, [(start_time, end_time)]),
    }
    
    if os.path.exists("cookies.txt"):
        try:
            with open("cookies.txt", "r") as f:
                if ".youtube.com" in f.read():
                    ydl_opts_download["cookiefile"] = "cookies.txt"
        except: pass

    try:
        print(f"      ⏱️ Extrayendo {duration}s desde t={start_time}s...")
        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_dl:
            ydl_dl.download([url])
    except Exception as e:
        print(f"      ❌ Error descargando segmento: {e}")
        return False

    # yt-dlp may write file with exact path or add a suffix — find it
    if os.path.exists(temp_output):
        try:
            os.rename(temp_output, output_path)
        except Exception as e:
            print(f"      ❌ No se pudo mover el archivo: {e}")
            return False
        print(f"      🎉 Clip de YouTube extraído con éxito!")
        return True
    else:
        # Try looking for any file created in the same dir matching the base name
        base_no_ext = temp_output.replace(".mp4", "")
        parent_dir = os.path.dirname(temp_output)
        base_name = os.path.basename(base_no_ext)
        for f in os.listdir(parent_dir):
            if f.startswith(base_name) and f.endswith(".mp4"):
                try:
                    os.rename(os.path.join(parent_dir, f), output_path)
                    print(f"      🎉 Clip de YouTube extraído con éxito! (Nombre alternativo: {f})")
                    return True
                except Exception as e:
                    print(f"      ❌ Renombrado fallido: {e}")
        print(f"      ❌ Falló la descarga: archivo no encontrado en {parent_dir}")
        return False


def _download_with_ytdlp(url, output_path, duration=4.0, start_offset_pct=0.30, label=""):
    """
    Internal helper: downloads a clip segment from a given URL using yt-dlp.
    Reuses cookies.txt if available. Applies start_offset_pct into the video
    to skip intros and grab the "core" content.
    Returns True on success.
    """
    try:
        import yt_dlp
    except ImportError:
        print(f"      ❌ yt-dlp no está instalado.")
        return False

    # First, extract info to get duration
    ydl_opts_info = {
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,
    }

    if os.path.exists("cookies.txt"):
        try:
            with open("cookies.txt", "r") as f:
                cookie_content = f.read()
                if ".youtube.com" in cookie_content or "twitter" in cookie_content or "reddit" in cookie_content:
                    ydl_opts_info["cookiefile"] = "cookies.txt"
        except: pass

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return False
            vid_duration = info.get('duration', 0) or 0
    except Exception as e:
        print(f"      ❌ [{label}] Error extrayendo info: {e}")
        return False

    if vid_duration <= duration:
        start_time = 0
    else:
        start_time = max(0, int(vid_duration * start_offset_pct))

    end_time = start_time + duration
    temp_output = output_path.replace(".mp4", f"_{label}_raw.mp4")

    ydl_opts_download = {
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best',
        'outtmpl': temp_output,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 20,
        'merge_output_format': 'mp4',
        'download_ranges': yt_dlp.utils.download_range_func(None, [(start_time, end_time)]),
    }

    if os.path.exists("cookies.txt"):
        try:
            with open("cookies.txt", "r") as f:
                content = f.read()
                if ".youtube.com" in content or "twitter" in content or "reddit" in content:
                    ydl_opts_download["cookiefile"] = "cookies.txt"
        except: pass

    try:
        print(f"      ⏱️ [{label}] Extrayendo {duration}s desde t={start_time}s...")
        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_dl:
            ydl_dl.download([url])
    except Exception as e:
        print(f"      ❌ [{label}] Error descargando segmento: {e}")
        return False

    # Find the output file (yt-dlp may vary the name)
    if os.path.exists(temp_output):
        try:
            os.rename(temp_output, output_path)
            print(f"      🎉 [{label}] Clip extraído con éxito!")
            return True
        except Exception as e:
            print(f"      ❌ [{label}] Error moviendo archivo: {e}")
            return False
    else:
        parent_dir = os.path.dirname(temp_output)
        base_name = os.path.basename(temp_output.replace(".mp4", ""))
        for f in os.listdir(parent_dir):
            if f.startswith(base_name) and f.endswith(".mp4"):
                try:
                    os.rename(os.path.join(parent_dir, f), output_path)
                    print(f"      🎉 [{label}] Clip extraído con éxito! (nombre alt: {f})")
                    return True
                except: pass
        return False


def get_reddit_clip(query, output_path, duration=4.0):
    """
    Searches Reddit for video posts matching the query using the public JSON API.
    Downloads the best matching video clip using yt-dlp's native Reddit support.
    Returns True if successful, False otherwise.
    
    Strategy: Searches relevant subreddits via Reddit's public JSON search,
    finds posts with video, then downloads using yt-dlp.
    """
    print(f"   🟠 Buscando clip en Reddit: '{query}'...")

    # Reddit's public JSON search (no auth needed)
    search_url = "https://www.reddit.com/search.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Try multiple search strategies
    search_queries = [
        f"{query} scene",
        query,
        f"{query} clip",
    ]

    for sq in search_queries:
        params = {
            "q": sq,
            "type": "link",
            "sort": "relevance",
            "t": "all",
            "limit": 15,
        }

        try:
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"      ⚠️ Reddit API respondió {response.status_code}")
                continue

            data = response.json()
            posts = data.get('data', {}).get('children', [])

            # Filter for video posts
            video_posts = []
            for post in posts:
                pd = post.get('data', {})
                # Reddit-hosted video
                if pd.get('is_video') and pd.get('media', {}).get('reddit_video', {}).get('fallback_url'):
                    video_posts.append({
                        'url': f"https://www.reddit.com{pd['permalink']}",
                        'title': pd.get('title', ''),
                        'score': pd.get('score', 0),
                        'duration': pd.get('media', {}).get('reddit_video', {}).get('duration', 0),
                    })
                # External video links (v.redd.it, streamable, etc.)
                elif pd.get('post_hint') == 'hosted:video':
                    video_posts.append({
                        'url': f"https://www.reddit.com{pd['permalink']}",
                        'title': pd.get('title', ''),
                        'score': pd.get('score', 0),
                        'duration': 0,
                    })

            if not video_posts:
                continue

            # Sort by score (most upvoted = usually best quality/relevance)
            video_posts.sort(key=lambda x: x['score'], reverse=True)

            # Try top 3 candidates
            for vp in video_posts[:3]:
                print(f"      📌 Reddit: '{vp['title'][:60]}...' (⬆{vp['score']})")
                
                with yt_dlp_lock:
                    time.sleep(random.uniform(0.5, 1.5))
                    if _download_with_ytdlp(vp['url'], output_path, duration=duration, label="Reddit"):
                        return True
                print(f"      ⚠️ Descarga falló, probando siguiente...")

        except Exception as e:
            print(f"      ❌ Error buscando en Reddit: {e}")
            continue

    print(f"      ⚠️ No se encontró clip en Reddit para '{query}'.")
    return False


def get_twitter_clip(query, output_path, duration=4.0):
    """
    Searches for video clips from Twitter/X using the Nitter search and yt-dlp.
    Uses yt-dlp's native Twitter extractor which works without authentication
    for public tweets containing video.
    Returns True if successful, False otherwise.
    
    Strategy: Uses yt-dlp's built-in Twitter search capabilities; if that fails,
    falls back to scraping public Nitter instances for tweet URLs with video.
    """
    print(f"   🐦 Buscando clip en Twitter/X: '{query}'...")

    try:
        import yt_dlp
    except ImportError:
        print("      ❌ yt-dlp no está instalado.")
        return False

    # Strategy 1: Use yt-dlp to search on Twitter directly
    # yt-dlp doesn't have a "twittersearch:" prefix, so we try nitter/syndication
    # Instead, we use a known trick: search via syndication API or direct URL patterns

    # Strategy 2: Use Nitter (public Twitter mirror) to find tweets with video
    nitter_instances = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://nitter.cz",
    ]

    search_queries = [
        f"{query} scene",
        query,
        f"{query} clip",
    ]

    for nitter_base in nitter_instances:
        for sq in search_queries:
            try:
                search_url = f"{nitter_base}/search?f=videos&q={requests.utils.quote(sq)}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                response = requests.get(search_url, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue

                # Parse tweet links from Nitter HTML (they contain /status/ paths)
                import re
                # Find tweet status URLs in the HTML
                tweet_paths = re.findall(r'href="(/[^/]+/status/\d+)', response.text)
                
                if not tweet_paths:
                    continue

                # Deduplicate while preserving order
                seen = set()
                unique_paths = []
                for tp in tweet_paths:
                    if tp not in seen:
                        seen.add(tp)
                        unique_paths.append(tp)

                # Try to download from the real Twitter URL
                for tp in unique_paths[:3]:
                    twitter_url = f"https://twitter.com{tp}"
                    print(f"      📌 Twitter: {twitter_url}")
                    
                    with yt_dlp_lock:
                        time.sleep(random.uniform(0.5, 2.0))
                        if _download_with_ytdlp(twitter_url, output_path, duration=duration, label="Twitter"):
                            return True
                    print(f"      ⚠️ Descarga falló, probando siguiente...")

            except Exception as e:
                print(f"      ⚠️ Error con Nitter ({nitter_base}): {e}")
                continue

    print(f"      ⚠️ No se encontró clip en Twitter para '{query}'.")
    return False


def get_dailymotion_clip(query, output_path, duration=4.0):
    """
    Searches Dailymotion for a video clip matching the query and downloads it.
    Dailymotion has a public API and yt-dlp supports it natively without auth issues.
    Returns True if successful, False otherwise.
    """
    print(f"   🔵 Buscando clip en Dailymotion: '{query}'...")

    # Dailymotion public API v2 (no key needed for search)
    search_url = "https://api.dailymotion.com/videos"
    
    search_queries = [query, f"{query} scene", " ".join(query.split()[:3])]

    for sq in search_queries:
        params = {
            "search": sq,
            "fields": "id,title,url,duration",
            "sort": "relevance",
            "limit": 10,
            "longer_than": 3,   # At least 3 seconds
            "shorter_than": 600, # At most 10 min (skip full movies)
        }

        try:
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                continue

            data = response.json()
            videos = data.get('list', [])

            if not videos:
                continue

            # Try top candidates
            for vid in videos[:3]:
                dm_url = vid.get('url', '')
                if not dm_url:
                    dm_url = f"https://www.dailymotion.com/video/{vid['id']}"
                
                print(f"      📌 Dailymotion: '{vid.get('title', '?')[:50]}' ({vid.get('duration', 0)}s)")
                
                with yt_dlp_lock:
                    time.sleep(random.uniform(0.3, 1.0))
                    if _download_with_ytdlp(dm_url, output_path, duration=duration, label="Dailymotion"):
                        return True
                print(f"      ⚠️ Descarga falló, probando siguiente...")

        except Exception as e:
            print(f"      ❌ Error buscando en Dailymotion: {e}")
            continue

    print(f"      ⚠️ No se encontró clip en Dailymotion para '{query}'.")
    return False


def get_best_clip(query, output_path, duration=4.0):
    """
    Orchestrator: tries multiple platforms in order of reliability and content quality.
    Order: Reddit → Dailymotion → Twitter → YouTube (last resort, often blocked).
    Returns True if ANY source succeeds, False if all fail.
    """
    print(f"\n🌐 Buscando clip REAL para: '{query}' (multi-plataforma)...")

    # 1. Reddit (best for clips virales, escenas, anime, cultura pop)
    if get_reddit_clip(query, output_path, duration):
        print(f"   ✅ Clip obtenido de Reddit!")
        return True

    # 2. Dailymotion (buen catálogo de clips de TV, películas, documentales)
    if get_dailymotion_clip(query, output_path, duration):
        print(f"   ✅ Clip obtenido de Dailymotion!")
        return True

    # 3. Twitter (bueno para clips noticiosos, momentos virales)
    if get_twitter_clip(query, output_path, duration):
        print(f"   ✅ Clip obtenido de Twitter!")
        return True

    # 4. YouTube (último recurso — a menudo bloqueado por bots)
    print(f"   ⚠️ Ninguna fuente alternativa funcionó. Intentando YouTube como fallback...")
    if get_youtube_clip(query, output_path, duration):
        print(f"   ✅ Clip obtenido de YouTube (fallback)!")
        return True

    print(f"   ❌ No se pudo obtener clip de NINGUNA fuente para '{query}'.")
    return False
