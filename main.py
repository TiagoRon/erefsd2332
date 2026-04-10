import asyncio
import os
import sys
import codecs

# Force UTF-8 for console output on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
from src.ai_client import generate_script
from src.tts_engine import generate_full_audio
from src.video_editor import create_short

def main():
    print("--- AutoShorts Generator (Spanish) ---")
    
# 1. Generate Script
# 1. Generate Script
from src.trends_finder import get_trending_topics
from src.ai_client import generate_script, generate_viral_hooks, generate_creative_topic
from src.constants import EVERGREEN_TOPICS, WHAT_IF_TOPICS, TOP_3_TOPICS, DARK_FACTS_TOPICS, HISTORY_TOPICS, CUSTOM_TOPICS
from src.tts_engine import get_random_voice
import random

def run_batch(count, topic=None, use_trends=False, style="curiosity", log_func=print, 
              watermark_text="", lang="en", is_test=False, 
              progress_callback=None, is_cancelled=None, loc=None):
    
    # Pre-fetch trends if requested
    trending_topics = []
    if use_trends:
        log_func(loc.get("log_searching_trends") if loc else "🌍 Searching top trends on Google Trends...")
        trending_topics = get_trending_topics(count)
        log_func((loc.get("log_trends_found") if loc else "   Trends found: ") + str(trending_topics))
    
    # Init History Manager once
    from src.history_manager import HistoryManager
    hm = HistoryManager()
    
    # Ensure output root exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    success_count = 0
    generated_folders = []

    for i in range(count):
        # Cancellation Check
        if is_cancelled and is_cancelled():
            log_func(loc.get("status_cancelled") if loc else "Generation cancelled by user.")
            break

        def report_prog(local_pct, status_text, sub_text=""):
            if progress_callback:
                overall_pct = (i + local_pct) / count
                vid_title = f"Video {i+1}/{count}"
                if 'script' in locals() and isinstance(script, dict) and script.get('title'):
                    vid_title = script.get('title')
                progress_callback(overall_pct, title=vid_title, status=status_text, sub_status=sub_text)

        status_base = loc.get("status_processing").format(count) if loc else f"Processing {count} video(s)..."
        report_prog(0.02, status_base, "Generando idea y guion con Inteligencia Artificial...")

        log_func(f"\n--- {loc.get('title_generator') if loc else 'Generating Video'} {i+1}/{count} ---")
        
        current_hook = None
        current_topic = topic
        
        if style == "what_if":
            if not current_topic:
                 log_func(loc.get("log_inventing_whatif") if loc else "🧠 Inventing unique 'What If' topic with AI...")
                 for _ in range(3):
                     new_t = generate_creative_topic(style="what_if", lang=lang)
                     if new_t and not hm.is_topic_used(new_t) and not hm.is_title_used(new_t):
                         current_topic = new_t
                         break
                 
                 if not current_topic:
                     log_func(loc.get("log_ai_failed_fallback") if loc else "⚠️ AI failed or duplicated. Using fallback list...")
                     available = [t for t in WHAT_IF_TOPICS if not hm.is_topic_used(t) and not hm.is_title_used(t)]
                     current_topic = random.choice(available) if available else random.choice(WHAT_IF_TOPICS)
                     
            log_func(f"❓ Modo What If: {current_topic}")
            
            # Double check
            if hm.is_topic_used(current_topic) or hm.is_title_used(current_topic):
                 og_topic = current_topic
                 log_func(f"⚠️ Tema '{og_topic}' marcado como usado (Strict/Fuzzy). Intentando variar...")

        elif style == "top_3":
             # Similar logic for Top 3
             if not current_topic:
                 log_func(loc.get("log_inventing_top3") if loc else "🧠 Inventing unique 'Top 3' topic with AI...")
                 for _ in range(3):
                     new_t = generate_creative_topic(style="top_3", lang=lang)
                     if new_t and not hm.is_title_used(new_t):
                         current_topic = new_t
                         break
                 
                 if not current_topic:
                     log_func(loc.get("log_ai_failed_fallback") if loc else "⚠️ AI failed or duplicated. Using fallback list...")
                     available = [t for t in TOP_3_TOPICS if not hm.is_title_used(t)]
                     current_topic = random.choice(available) if available else random.choice(TOP_3_TOPICS)
            
        elif style == "dark_facts":
            if not current_topic:
                 log_func(loc.get("log_inventing_darkfacts") if loc else "🧠 Inventing unique 'Dark Facts' topic with AI...")
                 for _ in range(3):
                     new_t = generate_creative_topic(style="dark_facts", lang=lang)
                     if new_t and not hm.is_title_used(new_t):
                         current_topic = new_t
                         break
                 
                 if not current_topic:
                     log_func(loc.get("log_ai_failed_fallback") if loc else "⚠️ AI failed or duplicated. Using fallback list...")
                     available = [t for t in DARK_FACTS_TOPICS if not hm.is_title_used(t)]
                     current_topic = random.choice(available) if available else random.choice(DARK_FACTS_TOPICS)
            
            log_func(f"💀 Modo Dark Facts: {current_topic}")

        elif style == "history":
            if not current_topic:
                 log_func(loc.get("log_inventing_history") if loc else "🧠 Inventing unique 'History' topic with AI...")
                 for _ in range(3):
                     new_t = generate_creative_topic(style="history", lang=lang)
                     if new_t and not hm.is_title_used(new_t):
                         current_topic = new_t
                         break
                 
                 if not current_topic:
                     log_func(loc.get("log_ai_failed_fallback") if loc else "⚠️ AI failed or duplicated. Using fallback list...")
                     available = [t for t in HISTORY_TOPICS if not hm.is_title_used(t)]
                     current_topic = random.choice(available) if available else random.choice(HISTORY_TOPICS)
            
            log_func(f"📜 Modo History: {current_topic}")

        elif style == "custom":
            if not current_topic:
                 log_func(loc.get("log_inventing_custom") if loc else "🧠 Inventing unique 'Custom' idea with AI...")
                 for _ in range(3):
                     new_t = generate_creative_topic(style="custom", lang=lang)
                     if new_t and not hm.is_title_used(new_t):
                         current_topic = new_t
                         break
                 
                 if not current_topic:
                     log_func(loc.get("log_ai_failed_fallback") if loc else "⚠️ AI failed or duplicated. Using fallback list...")
                     available = [t for t in CUSTOM_TOPICS if not hm.is_title_used(t)]
                     current_topic = random.choice(available) if available else random.choice(CUSTOM_TOPICS)
            
            log_func(f"✨ Modo Custom: {current_topic}")
            
        elif use_trends and trending_topics:
            # New "Hook Adaptation" Logic
            # 1. Pick an Evergreen Topic
            base_topic = random.choice(EVERGREEN_TOPICS)
            log_func(f"🧠 {(loc.get('log_base_evergreen') if loc else 'Base Evergreen Topic:')} {base_topic}")
            
            # 2. Generate Hooks using Trends as Flavor
            log_func(loc.get("log_adapting_hooks") if loc else "⚡ Adapting hooks with current trends...")
            hooks = generate_viral_hooks(base_topic, trending_topics, lang=lang)
            
            if hooks:
                # 3. Pick the best one (Random for now)
                current_hook = random.choice(hooks)
                log_func(f"🪝 {(loc.get('log_hook_selected') if loc else 'Selected Hook:')} '{current_hook}'")
                current_topic = base_topic # Pass base topic for context if needed, though hook drives it
            else:
                log_func(loc.get("log_hook_failed") if loc else "⚠️ Failed to generate viral hooks. Using standard method.")
                current_topic = trending_topics[i % len(trending_topics)]
        
        # 1. Generate Script
        if current_hook:
            log_func(loc.get('log_gen_script_hook') if loc else "1. Generating script based on Viral Hook...")
            script = generate_script(specific_hook=current_hook, style=style, is_test=is_test, lang=lang)
        else:
            log_func(f"1. {(loc.get('log_gen_script_ai') if loc else 'Generating script with AI...')} (Topic: {current_topic if current_topic else 'Surprise'}, Style: {style})")
            
            # History Check for Generated Title
            # hm already initialized
            
            # Retry loop if title exists
            max_gen_retries = 3
            for attempt_gen in range(max_gen_retries):
                script = generate_script(topic=current_topic, style=style, is_test=is_test, lang=lang)
                if script and script.get('title'):
                    if hm.is_title_used(script['title']):
                        log_func(f"⚠️ Título generado ya existe en historial: '{script['title']}'. Reintentando...")
                        if attempt_gen == max_gen_retries - 1:
                            log_func("❌ Se acabaron los reintentos de título único. Usando igual.")
                    else:
                        break # Title is unique
                else:
                    break

        if not script:
            log_func(loc.get('log_script_error_skip') if loc else "Error generating script. Skipping...")
            continue
        
        log_func(f"   {(loc.get('log_title') if loc else 'Title:')} {script.get('title', 'Untitled')}")

        # --- IMPORTANT: Save to History IMMEDIATELY to prevent duplicates even if crash ---
        try:
            # hm initialized at start
            if script.get('title'):
                hm.add_title(script.get('title'))
            
            if style == "what_if" and current_topic:
                 hm.add_used_topic(current_topic)
            elif current_topic:
                 hm.add_trend(current_topic)
            log_func("✅ Agregado a historial (Preventivo) para no repetir.")
        except Exception as e:
            log_func(f"⚠️ Error guardando historial: {e}")
        
        # 2. Process Scenes (New V2.0 Logic)
        log_func(loc.get('log_analyzing_scenes') if loc else "2. Analyzing scenes and generating assets...")
        report_prog(0.10, status_base, loc.get('prog_compiling_scenes') if loc else "Compiling scenes and generating voices (TTS)...")
        
        scenes = script.get('scenes', [])
        log_func(f"   {(loc.get('log_scenes_detected') if loc else 'Scenes detected:')} {len(scenes)}")
        if not scenes:
            # Fallback for old prompt format ?
            # If AI fails to give scenes, we construct 'dummy' scenes from old keys if present
            if 'hook' in script:
                 log_func("⚠️ ALERTA: La IA devolvió el formato antiguo (3 partes). Usando Fallback. (Posible error de Prompt)")
                 scenes = [
                     {'text': script['hook'], 'visual_concept': 'mystery', 'color_palette': 'dark'},
                     {'text': script['body'], 'visual_concept': 'science', 'color_palette': 'neon'},
                     {'text': script['climax'], 'visual_concept': 'danger', 'color_palette': 'red'}
                 ]
            else:
                log_func("Error: El guion no tiene escenas validas.")
                log_func(f"Keys recibidas: {list(script.keys())}")
                continue

        # Create Output Folder
        safe_title = "".join([c for c in script.get('title', 'Video') if c.isalnum() or c in (' ', '-', '_')]).strip().replace(" ", "_")
        video_output_dir = os.path.join(OUTPUT_DIR, safe_title)
        os.makedirs(video_output_dir, exist_ok=True)
        
        # We will collect clip paths to pass to editor
        processed_scenes = []
        used_footage_ids = set() # Track used Pexels IDs to avoid duplicates
        
        from src.tts_engine import generate_audio
        from src.background_generator import generate_scene_clip
        from src.stock_client import get_stock_video, get_stock_image, get_wikipedia_image, get_giphy_video, get_youtube_clip, get_best_clip
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Select Voice for this video
        selected_voice = get_random_voice(lang=lang)
        log_func(f"   🗣️ {(loc.get('log_voice_selected') if loc else 'Selected Voice:')} {selected_voice}")

        # ====================================================================
        # PHASE 1: Generate ALL TTS audio in PARALLEL (async)
        # ====================================================================
        log_func("⚡ Fase 1: Generando TODOS los audios TTS en paralelo...")
        report_prog(0.10, status_base, loc.get('prog_compiling_scenes') if loc else "Generating all voices in parallel (TTS)...")
        
        for scene in scenes:
            scene['text'] = scene.get('text', '').replace('*', '')
        
        async def batch_tts():
            tasks = []
            for idx, scene in enumerate(scenes):
                audio_path = os.path.join(video_output_dir, f"audio_{idx}.mp3")
                tasks.append(generate_audio(scene['text'], audio_path, voice=selected_voice))
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        tts_results = asyncio.run(batch_tts())
        
        # Process TTS results and get durations
        for idx, scene in enumerate(scenes):
            if is_cancelled and is_cancelled():
                log_func("🛑 Generación abortada por el usuario.")
                try:
                    import shutil
                    shutil.rmtree(video_output_dir)
                except: pass
                return
            
            audio_path = os.path.join(video_output_dir, f"audio_{idx}.mp3")
            result = tts_results[idx]
            
            if isinstance(result, Exception):
                log_func(f"Error generando audio escena {idx}: {result}")
                continue
            
            success, timings = result
            if not success:
                log_func(f"Error generando audio escena {idx}")
                continue
            
            # Whisper fallback only if TTS didn't return timings
            if not timings:
                log_func(f"⚠️ No timings from TTS for scene {idx}. Trying Whisper...")
                try:
                    from src.aligner import get_word_timings
                    timings = get_word_timings(audio_path, text_hint=scene['text'])
                    if timings:
                        log_func(f"   ✅ Timings recovered with Whisper ({len(timings)} words).")
                except Exception as ew:
                    log_func(f"   ❌ Whisper failed: {ew}. Using linear fallback.")
                    from src.aligner import linear_fallback
                    timings = linear_fallback(scene['text'].split())
            
            scene['timings'] = timings
            scene['audio_path'] = audio_path
            
            # Get duration
            try:
                from moviepy.editor import AudioFileClip
                temp_audioclip = AudioFileClip(audio_path)
                scene['duration'] = temp_audioclip.duration
                temp_audioclip.close()
            except:
                scene['duration'] = 5.0
            
            log_func(f"   🎬 Scene {idx+1}: TTS OK ({scene['duration']:.1f}s)")
        
        log_func(f"✅ Todos los audios generados.")
        
        # ====================================================================
        # PHASE 2: Download ALL visual clips in PARALLEL (ThreadPool)
        # ====================================================================
        log_func("⚡ Fase 2: Descargando TODOS los clips visuales en paralelo...")
        report_prog(0.30, status_base, loc.get('prog_downloading_mat') if loc else "Downloading all visual clips in parallel...")
        
        # Cache: overlay_term -> local file path (to avoid downloading same entity multiple times)
        # Protected by a lock since download_scene_clips runs in multiple threads.
        import threading
        yt_cache = {}   # overlay_term -> yt_path (video) or None (failed)
        img_cache = {}  # overlay_term -> img_path (photo) or None (failed)
        cache_lock = threading.Lock()


        def download_scene_clips(idx, scene):
            """Download all visual clips for one scene. Runs in its own thread."""
            if is_cancelled and is_cancelled():
                return idx, []
            
            real_duration = scene.get('duration', 5.0)
            visual_clips_paths = []
            
            num_clips = int(real_duration / 2.5)
            if num_clips < 1: num_clips = 1
            if num_clips > 4: num_clips = 4
            
            sub_dur = real_duration / num_clips
            overlay_term = scene.get('visual_overlay_term')
            # Normalize: treat "null" string as absent
            if overlay_term and (overlay_term.strip().lower() in ("null", "none", "", "n/a")):
                overlay_term = None
            search_query_base = scene.get('visual_search_term_en', scene.get('visual_concept', 'mystery'))
            
            # ---------------------------------------------------------------
            # For SPECIFIC entity scenes (overlay_term present):
            # Strategy: try YouTube ONCE (cached), then Wikipedia photo (cached),
            # then Pexels image (cached). Reuse across sub-clips.
            # Only fall back to generic Pexels VIDEO if all specific sources fail.
            # ---------------------------------------------------------------
            if overlay_term:
                specific_clip_path = None   # video clip (YouTube)
                specific_img_path = None    # photo (Wikipedia / Pexels image)
                
                # --- Try YouTube (cached per overlay_term) ---
                with cache_lock:
                    if overlay_term in yt_cache:
                        specific_clip_path = yt_cache[overlay_term]
                        if specific_clip_path:
                            print(f"   ♻️ Reutilizando clip de YouTube en caché: {overlay_term}")
                        need_yt_download = False
                    else:
                        # Reserve the slot before releasing lock so other threads don't try to download too
                        yt_cache[overlay_term] = None
                        need_yt_download = True
                
                if need_yt_download:
                    yt_path = os.path.join(video_output_dir, f"yt_cache_{idx}_{overlay_term[:30].replace(' ','_')}.mp4")
                    if get_best_clip(overlay_term, yt_path, sub_dur):
                        with cache_lock:
                            yt_cache[overlay_term] = yt_path
                        specific_clip_path = yt_path
                    # else: stays None in cache (failed)
                
                # --- Try Wikipedia image (cached per overlay_term) ---
                with cache_lock:
                    if overlay_term in img_cache:
                        specific_img_path = img_cache[overlay_term]
                        if specific_img_path:
                            print(f"   ♻️ Reutilizando imagen en caché: {overlay_term}")
                        need_img_download = False
                    else:
                        img_cache[overlay_term] = None  # Reserve slot
                        need_img_download = True
                
                if need_img_download:
                    wiki_img_path = os.path.join(video_output_dir, f"img_cache_{idx}_{overlay_term[:30].replace(' ','_')}.jpg")
                    if get_wikipedia_image(overlay_term, wiki_img_path):
                        with cache_lock:
                            img_cache[overlay_term] = wiki_img_path
                        specific_img_path = wiki_img_path
                    else:
                        # Try Pexels image as photo fallback
                        pexels_img_path = os.path.join(video_output_dir, f"pexels_img_{idx}_{overlay_term[:30].replace(' ','_')}.jpg")
                        if get_stock_image(overlay_term, pexels_img_path):
                            with cache_lock:
                                img_cache[overlay_term] = pexels_img_path
                            specific_img_path = pexels_img_path
                        # else: stays None in cache (failed)

                
                # --- Fill sub-clips: prefer video clip, then photo, then generic ---
                for clip_i in range(num_clips):
                    if is_cancelled and is_cancelled():
                        break
                    
                    if clip_i == 0 and specific_clip_path:
                        # Use the YouTube clip ONLY for the first sub-clip (fast appearance)
                        visual_clips_paths.append(specific_clip_path)
                    elif clip_i == 0 and specific_img_path:
                        # Use the photo ONLY for the first sub-clip (fast appearance)
                        visual_clips_paths.append(specific_img_path)
                    else:
                        # For subsequent sub-clips (or if specific failed), use generic Pexels video (fast pacing)
                        bg_path = os.path.join(video_output_dir, f"scene_{idx}_part{clip_i}.mp4")
                        query = search_query_base
                        if clip_i == 1: query = f"{search_query_base} close up"
                        elif clip_i >= 2: query = f"{search_query_base} cinematic"
                        stock_ok = get_stock_video(query, sub_dur, bg_path, used_ids=used_footage_ids, is_cancelled=is_cancelled)
                        if not stock_ok:
                            generate_scene_clip(
                                scene.get('visual_concept', 'mystery'),
                                scene.get('color_palette', 'dark'),
                                sub_dur, bg_path
                            )
                        visual_clips_paths.append(bg_path)
                
                return idx, visual_clips_paths

            # ---------------------------------------------------------------
            # GENERIC scenes (no overlay_term): use Pexels stock video as before
            # ---------------------------------------------------------------
            for clip_i in range(num_clips):
                if is_cancelled and is_cancelled():
                    break
                    
                bg_path = os.path.join(video_output_dir, f"scene_{idx}_part{clip_i}.mp4")
                
                query = search_query_base
                if clip_i == 1: query = f"{search_query_base} close up"
                elif clip_i == 2: query = f"{search_query_base} detail"
                elif clip_i == 3: query = f"{search_query_base} cinematic"
                
                stock_success = get_stock_video(query, sub_dur, bg_path, used_ids=used_footage_ids, is_cancelled=is_cancelled)
                
                if not stock_success:
                    generate_scene_clip(
                        scene.get('visual_concept', 'mystery'),
                        scene.get('color_palette', 'dark'),
                        sub_dur,
                        bg_path
                    )
                visual_clips_paths.append(bg_path)
            
            return idx, visual_clips_paths
        
        # Launch all scene downloads in parallel (3 concurrent workers)
        valid_scene_indices = [i for i, s in enumerate(scenes) if 'audio_path' in s]
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for idx in valid_scene_indices:
                futures[executor.submit(download_scene_clips, idx, scenes[idx])] = idx
            
            completed = 0
            for future in as_completed(futures):
                try:
                    scene_idx, clips = future.result()
                    scenes[scene_idx]['video_paths'] = clips
                    if 'image_overlay_path' in scenes[scene_idx]:
                        del scenes[scene_idx]['image_overlay_path']
                    completed += 1
                    report_prog(0.30 + 0.15 * completed / max(len(valid_scene_indices), 1), status_base, f"Downloaded clips for scene {scene_idx + 1}/{len(scenes)}...")
                    log_func(f"   ✅ Scene {scene_idx + 1}: {len(clips)} clips downloaded")
                except Exception as e:
                    log_func(f"Error downloading scene clips: {e}")
        
        # Collect processed scenes in original order
        for idx in valid_scene_indices:
            if 'video_paths' in scenes[idx]:
                processed_scenes.append(scenes[idx])
        
        # Force GC after all downloads
        import gc
        gc.collect()
        
        log_func(f"✅ {len(processed_scenes)} escenas procesadas en paralelo.")

        # 3. Create Final Video
        if is_cancelled and is_cancelled():
            log_func("🛑 Generación abortada por el usuario antes de ensamblar. Limpiando...")
            try:
                import shutil
                shutil.rmtree(video_output_dir)
            except Exception as ec:
                log_func(f"Error limpiando cancelación: {ec}")
            return
            
        output_file = os.path.join(video_output_dir, "short_final.mp4")
        
        # Calculate Title and Mood EARLY for metadata
        vid_title = script.get('title', '').upper()
        # Get Mood (Default to mystery)
        vid_mood = script.get('mood', 'mystery').lower()
        log_func(f"   🎵 {(loc.get('log_mood_detected') if loc else 'Mood detected:')} {vid_mood}")

        # --- SAVE METADATA EARLY (Robustness) ---
        try:
             # Save metadata TXT
            with open(os.path.join(video_output_dir, "metadata.txt"), "w", encoding="utf-8") as f:
                f.write(f"Título: {script.get('title')}\n")
                f.write(f"Hashtags: {' '.join(script.get('hashtags', []))}\n")
                
                # --- NEW TAGS SECTION ---
                tags_str = script.get('tags_string', '')
                if not tags_str and script.get('tags'):
                    # Fallback if AI forgot tags_string but gave tags list
                    tags_str = ",".join(script.get('tags', []))
                
                f.write(f"Etiquetas Youtube (Copia y pega):\n{tags_str}\n\n")
                
                f.write("Guion:\n")
                for s in scenes:
                    f.write(f"- {s['text']}\n")
            
            # Save PRO SEO Metadata (JSON)
            import json
            seo_data = {
                "title": script.get('title'),
                "seo_title": script.get('seo_title'),
                "seo_description": script.get('seo_description'),
                "tags": script.get('tags', []),
                "tags_string": script.get('tags_string', ''),
                "hashtags": script.get('hashtags', []),
                "mood": vid_mood,
                "style": style
            }
            with open(os.path.join(video_output_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(seo_data, f, indent=4, ensure_ascii=False)
            log_func("📝 Metadata guardada.")
        except Exception as e_meta:
             log_func(f"⚠️ Error guardando metadata: {e_meta}")

        # New function signature for editor
        from src.video_editor import assemble_video
        
        # vid_title and vid_mood calculated above
        
        success = assemble_video(processed_scenes, os.path.join(BASE_DIR, "music"), output_file, title_text=vid_title, mood=vid_mood, watermark_text=watermark_text, is_cancelled=is_cancelled, progress_callback=report_prog)
        
        if is_cancelled and is_cancelled():
            log_func("🛑 Render abortado por el usuario. Eliminando archivos corruptos...")
            try:
                import shutil
                shutil.rmtree(video_output_dir)
            except: pass
            return
            
        if success:
            log_func(f"{(loc.get('log_success_vid') if loc else 'SUCCESS! Video saved in:')} {output_file}")
            success_count += 1
            generated_folders.append(video_output_dir)
            # History already saved at start of loop
            pass
        else:
            log_func(loc.get('log_fail_vid') if loc else "Video creation failed.")

        # --- CLEANUP: Remove intermediate files (ALWAYS RUN) ---
        try:
            log_func(loc.get('log_cleaning_temp') if loc else "🧹 Cleaning up temporary files...")
            
            # Force GC and wait for Windows file locks
            import gc
            import time
            gc.collect()
            time.sleep(2) # Give OS time to release handles

            for fname in os.listdir(video_output_dir):
                # Keep final video and metadata
                if fname == "short_final.mp4" or fname.endswith(".txt") or fname.endswith(".json"):
                    continue
                
                # Delete everything else
                file_path = os.path.join(video_output_dir, fname)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as ex:
                    log_func(f"   ⚠️ {(loc.get('log_could_not_delete') if loc else 'Could not delete')} {fname} (Lock?): {ex}")
            log_func(f"✨ {(loc.get('log_cleanup_done') if loc else 'Cleanup completed.')}")
        except Exception as e:
            log_func(f"⚠️ {(loc.get('log_cleanup_error') if loc else 'General cleanup error:')} {e}")

        # Final loop GC
        gc.collect()

    # DEBUG: List all files in output
    print(f"📂 Debug Output Content: {os.listdir(OUTPUT_DIR)}")
    for root, dirs, files in os.walk(OUTPUT_DIR):
        print(f"  {root}: {files}")

    return generated_folders

def main():
    import sys
    import os
    
    # Check for Environment Variables (Automated Mode)
    env_count = os.getenv("VIDEO_COUNT")
    env_topic = os.getenv("VIDEO_TOPIC")
    env_style = os.getenv("VIDEO_STYLE", "curiosity")
    
    if env_count:
        try:
            count = int(env_count)
        except ValueError:
            count = 1
        topic = env_topic if env_topic else None
        print(f"🤖 Ejecución Automática detectada. Generando {count} video(s). Tema: {topic}, Estilo: {env_style}")
    else:
        # Interactive Mode
        try:
            count = int(input("¿Cuántos videos quieres generar? (Enter para 1): ") or 1)
            topic = input("¿Tema específico? (Deja vacío para aleatorio): ").strip() or None
        except ValueError:
            count = 1
            topic = None
            
            
    if run_batch(count, topic, style=env_style):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
