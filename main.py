import asyncio
import os
from src.ai_client import generate_script
from src.tts_engine import generate_full_audio
from src.video_editor import create_short

def main():
    print("--- AutoShorts Generator (Spanish) ---")
    
# 1. Generate Script
# 1. Generate Script
from src.trends_finder import get_trending_topics
from src.ai_client import generate_script, generate_viral_hooks, generate_creative_topic
from src.constants import EVERGREEN_TOPICS, WHAT_IF_TOPICS, TOP_3_TOPICS
from src.tts_engine import get_random_voice
import random

def run_batch(count, topic=None, use_trends=False, style="curiosity", log_func=print):
    
    # Pre-fetch trends if requested
    trending_topics = []
    if use_trends:
        log_func("🌍 Buscando top tendencias en Google Trends...")
        trending_topics = get_trending_topics(count)
        log_func(f"   Tendencias encontradas: {trending_topics}")
    
    # Init History Manager once
    from src.history_manager import HistoryManager
    from src.history_manager import HistoryManager
    hm = HistoryManager()
    
    # Ensure output root exists
    os.makedirs("output", exist_ok=True)
    
    success_count = 0

    for i in range(count):
        log_func(f"\n--- Generando Video {i+1}/{count} ---")
        
        current_hook = None
        current_topic = topic
        
        if style == "what_if":
            if not current_topic:
                 # Check strict topic usage AND fuzzy title usage
                 available = [t for t in WHAT_IF_TOPICS if not hm.is_topic_used(t) and not hm.is_title_used(t)]
                 
                 if not available:
                     log_func("⚠️ Lista interna agotada. Inventando tema NUEVO con IA...")
                     # AI GENERATION FALLBACK
                     for _ in range(3): # Try 3 times to get a unique one
                         new_t = generate_creative_topic(style="what_if")
                         if new_t and not hm.is_topic_used(new_t) and not hm.is_title_used(new_t):
                             current_topic = new_t
                             break
                     
                     if not current_topic:
                          log_func("❌ No se pudo inventar tema único. Usando aleatorio repetido.")
                          current_topic = random.choice(WHAT_IF_TOPICS)
                 else:
                     current_topic = random.choice(available)
                     
            log_func(f"❓ Modo What If: {current_topic}")
            
            # Double check
            if hm.is_topic_used(current_topic) or hm.is_title_used(current_topic):
                 og_topic = current_topic
                 log_func(f"⚠️ Tema '{og_topic}' marcado como usado (Strict/Fuzzy). Intentando variar...")
                 # If it was manually passed or we ran out, we proceed but expect a variant.
                 # But if we just picked it from list, we shouldn't have picked it (filtered above).

        elif style == "top_3":
             # Similar logic for Top 3
             if not current_topic:
                 available = [t for t in TOP_3_TOPICS if not hm.is_title_used(t)]
                 
                 if not available:
                     log_func("⚠️ Lista 'Top 3' agotada. Inventando con IA...")
                     new_t = generate_creative_topic(style="top_3")
                     if new_t:
                         current_topic = new_t
                     else:
                         current_topic = random.choice(TOP_3_TOPICS)
                 else:
                     current_topic = random.choice(available)
            
             log_func(f"🏆 Modo Top 3: {current_topic}")
            
        elif use_trends and trending_topics:
            # New "Hook Adaptation" Logic
            # 1. Pick an Evergreen Topic
            base_topic = random.choice(EVERGREEN_TOPICS)
            log_func(f"🧠 Tema Base Evergreen: {base_topic}")
            
            # 2. Generate Hooks using Trends as Flavor
            log_func(f"⚡ Adaptando hooks con tendencias actuales...")
            hooks = generate_viral_hooks(base_topic, trending_topics)
            
            if hooks:
                # 3. Pick the best one (Random for now)
                current_hook = random.choice(hooks)
                log_func(f"🪝 Hook Seleccionado: '{current_hook}'")
                current_topic = base_topic # Pass base topic for context if needed, though hook drives it
            else:
                log_func("⚠️ Falló la generación de hooks virales. Usando método estándar.")
                current_topic = trending_topics[i % len(trending_topics)]
        
        # 1. Generate Script
        if current_hook:
            log_func(f"1. Generando guion basado en Hook Viral...")
            script = generate_script(specific_hook=current_hook, style=style)
        else:
            log_func(f"1. Generando guion con IA... (Tema: {current_topic if current_topic else 'Sorpresa'}, Estilo: {style})")
            
            # History Check for Generated Title
            # hm already initialized
            
            # Retry loop if title exists
            max_gen_retries = 3
            for attempt_gen in range(max_gen_retries):
                script = generate_script(topic=current_topic, style=style)
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
            log_func("Error al generar guion. Saltando...")
            continue
        
        log_func(f"   Título: {script.get('title', 'Sin título')}")

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
        log_func("2. Analizando escenas y generando activos...")
        
        scenes = script.get('scenes', [])
        log_func(f"   Escenas detectadas: {len(scenes)}")
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
        video_output_dir = os.path.join("output", safe_title)
        os.makedirs(video_output_dir, exist_ok=True)
        
        # We will collect clip paths to pass to editor
        processed_scenes = []
        used_footage_ids = set() # Track used Pexels IDs to avoid duplicates
        
        from src.tts_engine import generate_audio
        from src.background_generator import generate_scene_clip
        
        # Select Voice for this video
        selected_voice = get_random_voice()
        log_func(f"   🗣️ Voz seleccionada: {selected_voice}")

        for idx, scene in enumerate(scenes):
            log_func(f"   🎬 Escena {idx+1}: {scene.get('visual_concept', 'general')} [{scene.get('color_palette', 'dark')}]")
            
            # A. Generate Audio
            audio_path = os.path.join(video_output_dir, f"audio_{idx}.mp3")
            try:
                success, timings = asyncio.run(generate_audio(scene['text'], audio_path, voice=selected_voice))
                if not success: 
                     log_func(f"Error generando audio escena {idx}")
                     continue
                
                if not timings:
                    log_func(f"⚠️ Advertencia: No se recibieron tiempos de subtítulos para escena {idx}. Intentando alinear con Whisper...")
                    try:
                        from src.aligner import get_word_timings
                        timings = get_word_timings(audio_path, text_hint=scene['text'])
                        if timings:
                            log_func(f"   ✅ Timings recuperados con Whisper ({len(timings)} palabras).")
                        else:
                            log_func("   ❌ Whisper no devolvió timings. Usando fallback heurístico.")
                    except Exception as ew:
                        log_func(f"   ❌ Error en Whisper Align: {ew}. Usando fallback heurístico.")

                scene['timings'] = timings 
                
            except Exception as e:
                log_func(f"Error generando audio: {e}")
                continue
            
            # B. Duration
            # Need actual duration from file to be precise
            try:
                from moviepy.editor import AudioFileClip
                # It is safe to load here for duration check
                temp_audioclip = AudioFileClip(audio_path)
                real_duration = temp_audioclip.duration
                temp_audioclip.close()
            except:
                real_duration = 5.0

            scene['duration'] = real_duration
            
            # D. Visual Generation (Prioritizing Specific Overlays as Main Visuals)
            # Dynamic Pacing: Change visual every ~2.5 to 3 seconds.
            visual_clips_paths = []
            
            # Calculate clips needed based on duration (aggressive pacing)
            num_clips = int(real_duration / 2.5) 
            if num_clips < 1: num_clips = 1
            if num_clips > 4: num_clips = 4 # Cap to avoid too many downloads
            
            if num_clips > 1:
                log_func(f"      ⏱️ Escena larga ({real_duration:.1f}s) -> Dividiendo en {num_clips} clips.")
            
            sub_dur = real_duration / num_clips
            
            # CHECK FOR SPECIFIC VISUAL FIRST (Overlay Term)
            # If we have a specific person/place, we want THAT to be the visual, not a generic background.
            overlay_term = scene.get('visual_overlay_term')
            specific_visual_found = False
            specific_file_path = None
            
            if overlay_term and overlay_term.lower() != "null" and overlay_term.strip():
                 log_func(f"      🎯 Término específico detectado: '{overlay_term}'")
                 
                 # 1. Try to find a VIDEO of the specific term
                 target_vid_path = os.path.join(video_output_dir, f"scene_{idx}_specific.mp4")
                 from src.stock_client import get_stock_video
                 # Try strict search first
                 if get_stock_video(overlay_term, sub_dur, target_vid_path, used_ids=used_footage_ids):
                     log_func(f"      ✅ Video específico encontrado para '{overlay_term}'")
                     specific_visual_found = True
                     specific_file_path = target_vid_path
                 else:
                     # 2. Try to find an IMAGE (to be used as Ken Burns clip)
                     log_func(f"      ⚠️ No hay video para '{overlay_term}', buscando imagen...")
                     from src.stock_client import get_stock_image
                     target_img_path = os.path.join(video_output_dir, f"scene_{idx}_specific.jpg")
                     if get_stock_image(overlay_term, target_img_path):
                          log_func(f"      ✅ Imagen específica encontrada para '{overlay_term}' (Se usará con Ken Burns)")
                          specific_visual_found = True
                          specific_file_path = target_img_path
                     else:
                          log_func(f"      ❌ No se encontró nada para '{overlay_term}'. Usando fondo genérico.")

            # Generate Clips (filling with specific or generic)
            search_query_base = scene.get('visual_search_term_en', scene.get('visual_concept', 'mystery'))
            
            for clip_i in range(num_clips):
                # If we found a specific visual, use it!
                # If we have multiple clips, maybe we alternate or use it for the first one?
                # User preference: "Debería de ser algún clip".
                # Best logic: If specific found, use it for at least 50% or all if short.
                
                use_specific = False
                if specific_visual_found:
                    # If it's a video, we might want to loop it or uses it once?
                    # If it's an image, we can reuse it (Ken Burns will vary zoom direction randomly).
                    # Let's use the specific visual for ALL clips in this scene to maintain subject focus,
                    # UNLESS it's very long (then it might get boring).
                    # For now, simplistic: Use specific for everything if found.
                    use_specific = True

                
                if use_specific:
                    # We already have the file at specific_file_path
                    # We just append it. The editor will handle looping/cropping.
                    visual_clips_paths.append(specific_file_path)
                else:
                    # GENERIC FALLBACK
                    bg_path = os.path.join(video_output_dir, f"scene_{idx}_part{clip_i}.mp4")
                    
                    query = search_query_base
                    if clip_i == 1: query = f"{search_query_base} close up"
                    elif clip_i == 2: query = f"{search_query_base} detail"
                    elif clip_i == 3: query = f"{search_query_base} cinematic"
                    
                    # Try Stock
                    from src.stock_client import get_stock_video
                    stock_success = get_stock_video(query, sub_dur, bg_path, used_ids=used_footage_ids)
                    
                    if not stock_success:
                         # Fallback procedural
                         generate_scene_clip(
                            scene.get('visual_concept', 'mystery'),
                            scene.get('color_palette', 'dark'),
                            sub_dur,
                            bg_path
                         )
                    visual_clips_paths.append(bg_path)
            
            # FORCE GC after huge search
            import gc
            gc.collect()
            
            # Clean up old key to prevent confusion
            if 'image_overlay_path' in scene: del scene['image_overlay_path']

            scene['video_paths'] = visual_clips_paths
            scene['audio_path'] = audio_path
            processed_scenes.append(scene)

        # 3. Create Final Video
        output_file = os.path.join(video_output_dir, "short_final.mp4")
        
        # Calculate Title and Mood EARLY for metadata
        vid_title = script.get('title', '').upper()
        # Get Mood (Default to mystery)
        vid_mood = script.get('mood', 'mystery').lower()
        log_func(f"   🎵 Mood detectado: {vid_mood}")

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
                "mood": vid_mood
            }
            with open(os.path.join(video_output_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(seo_data, f, indent=4, ensure_ascii=False)
            log_func("📝 Metadata guardada.")
        except Exception as e_meta:
             log_func(f"⚠️ Error guardando metadata: {e_meta}")

        # New function signature for editor
        from src.video_editor import assemble_video
        
        # vid_title and vid_mood calculated above
        
        success = assemble_video(processed_scenes, "music", output_file, title_text=vid_title, mood=vid_mood)
        
        if success:
            log_func(f"¡ÉXITO! Video guardado en: {output_file}")
            success_count += 1
            # History already saved at start of loop
            pass
        else:
            log_func("Falló la creación del video.")

        # --- CLEANUP: Remove intermediate files (ALWAYS RUN) ---
        try:
            log_func("🧹 Limpiando archivos temporales...")
            
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
                    log_func(f"   ⚠️ No se pudo borrar {fname} (Posible Lock): {ex}")
            log_func("✨ Limpieza completada.")
        except Exception as e:
            log_func(f"⚠️ Error en limpieza general: {e}")

        # Final loop GC
        gc.collect()

    # DEBUG: List all files in output
    print(f"📂 Debug Output Content: {os.listdir('output')}")
    for root, dirs, files in os.walk("output"):
        print(f"  {root}: {files}")

    return success_count > 0

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
