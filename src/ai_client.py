import os
from google import genai
from google.genai import types
import json
from dotenv import load_dotenv

load_dotenv()

def generate_script(topic=None, specific_hook=None, style="curiosity"):
    """

    Generates a 3-sentence script for a YouTube Short using Google Gemini (New SDK).
    Returns a dictionary with 'hook', 'body', 'climax', 'title', 'hashtags'.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    client = genai.Client(api_key=api_key)

    if style == "what_if":
        if topic:
             topic_instruction = f"TOPIC: 'What would happen if {topic}?'. Generate a speculative scientific/social scenario."
        else:
             topic_instruction = "TOPIC: Choose a RANDOM 'What If' scenario (e.g. What if the moon disappeared? What if we never slept?)."
             
        system_instruction = """
        STYLE: "WHAT IF" SCENARIO.
        - Hook: MUST start with "¿Qué pasaría si..." or "Imagina si...".
        - Body: logical but dramatic consequences.
        - Climax: existential or mind-blowing conclusion.
        - Climax: existential or mind-blowing conclusion.
        """
    elif style == "top_3":
         if topic:
             topic_instruction = f"TOPIC: '{topic}'."
         else:
             topic_instruction = "TOPIC: Choose a RANDOM 'Top 3' list (e.g. Top 3 Most Dangerous Roads)."
         
         system_instruction = """
         STYLE: "TOP 3 RANKING" (Countdown).
         - Hook: Intro the topic quickly. "Estos son los 3..."
         - Structure: 
            - Scene 1 (Body start): "Número 3: [Item name]..."
            - Scene 2 (Body mid): "Número 2: [Item name]..."
            - Climax (End): "Y el número 1: [Item name]..."
         - Tone: Energetic, fast-paced.
         """
    else:
        # Default Curiosity
        if topic and not specific_hook:
            topic_instruction = f"TOPIC: '{topic}'. Generate a curiosity script specifically about this topic."
        elif specific_hook:
            topic_instruction = f"""
            CORE INSTRUCTION: You must write a script that starts EXACTLY with this hook: "{specific_hook}".
            The script must be about the implied topic of the hook.
            Do NOT change the hook text.
            """
        else:
            topic_instruction = "TOPIC: Choose a RANDOM, UNIQUE curiosity about history, science, space, nature, or psychology. Do NOT use the octopus example."
        
        system_instruction = "STYLE: CURIOSITY / DID YOU KNOW."

    prompt = f"""
    You are not generating a background.
    You are generating a SHORT-FORM VIDEO PLAN where visuals must MATCH the narration moment by moment.
    
    {topic_instruction}
    {system_instruction}
    
    TASK:
    1. Break script into **5 to 7 SHORT VISUAL SCENES**.
    2. Analyze the EMOTIONAL TONE (Mood) of the script.
    3. Generate VIRAL SEO METADATA (Title, Description, Tags).
    4. **TAGS OPTIMIZATION**:
       - Generate 15-20 high-traffic YouTube tags.
       - Mix broad keywords (e.g., "History", "Science") and specific long-tail keywords (e.g., "Hidden truths about Titanic").
       - **CRITICAL**: The `tags_string` field must be a SINGLE string of comma-separated tags.
       - **CRITICAL**: The total length of `tags_string` MUST BE under 500 characters.
    
    RULES:
    1. **Hyper-Fast Pacing**: visual changes every 2-4 seconds.
    2. **5-7 Scenes Total**: DO NOT output just 3 scenes. Break longer sentences into multiple visual beats.
    3. **Visual Variety**: Use different angles (close-up, wide, drone) for consecutive shots.
    4. **Stock Footage Keywords (CRITICAL - IN ENGLISH)**:
       - `visual_search_term_en` MUST be a **CONCRETE, LITERAL description** of a video clip in ENGLISH.
       - **BAD**: "mystery", "fear", "science", "connection", "void", "deep ocean". (Stock sites return nothing good for these).
       - **GOOD**: "dark alley rain", "man screaming slow motion", "blue dna helix rotating", "hands shaking", "black hole simulation", "octopus swimming underwater".
       - **RELEVANCE**: If the text is about an octopus, the visual MUST be about an octopus. Do NOT show a shark or other animals unless explicitly mentioned.
       - Use specific NOUNS and ACTIONS. Imagine you are searching Pexels/Shutterstock.
    5. **LANGUAGE**: 
       - The `text` (script), `title`, and `hashtags` MUST be in **SPANISH (ESPAÑOL)**.
       - `visual_search_term_en` MUST be in **ENGLISH**.

    OUTPUT FORMAT (Pure JSON):
    {{
      "title": "Video Title (Spanish)",
      "mood": "mystery" | "happy" | "epic" | "curiosity" | "sad",
      "seo_title": "CLICKBAIT Viral Title for YouTube Shorts (Spanish)",
      "seo_description": "3-line SEO optimized description with keywords (Spanish)",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"],
      "tags_string": "comma, separated, list, of, tags, under, 500, chars, for, youtube",
      "hashtags": ["#tag1", "#tag2"],
      "scenes": [
        {{
          "text": "Script text in Spanish...",
          "visual_search_term_en": "literal description of visual in English",
          "visual_overlay_term": "OPTIONAL: Specific noun to show as image/photo (e.g. 'Albert Einstein', 'Eiffel Tower', 'DNA Helix'). Null if general. DO NOT use generic terms like 'Man', 'Woman', 'City'.",
          "color_palette": "color1, color2",
          "subtitle_emphasis": ["emphasis word"]
        }},
        ...
      ]
    }}
    """

    import time
    
    max_retries = 3
    base_delay = 10
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            
            text_response = response.text
            script_data = json.loads(text_response)
            return script_data
            
        except Exception as e:
            error_str = str(e)
            # Retry on rate limits OR network/dns errors
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "getaddrinfo failed" in error_str or "11001" in error_str:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (attempt + 1)
                    print(f"⚠️ Error transitorio ({e}). Reintentando en {wait_time}s... (Intento {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Error: Fallaron los reintentos tras error: {e}")
                    return None
            else:
                print(f"Error generating script: {e}")
                return None

def generate_viral_hooks(base_topic, trending_list):
    """
    Generates 5 viral hook variations adapting a base topic with trending terms.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are a hook adaptation engine for short-form viral videos.

    IMPORTANT:
    - ALL output must be in SPANISH.
    - Do NOT generate full scripts.
    - Do NOT explain the topic.
    - Your ONLY task is to adapt HOOKS.

    INPUT YOU WILL RECEIVE:
    1) A BASE EVERGREEN TOPIC: "{base_topic}"
    2) A LIST OF CURRENT TRENDING TERMS: {trending_list}

    YOUR ROLE:
    - Use trending terms ONLY as contextual examples.
    - NEVER depend on the trend to explain the video.
    - The core meaning must stay evergreen.
    - Trends are optional flavor, not the core subject.

    RULES:
    - Do NOT mention news, dates, or events explicitly.
    - Do NOT explain the trend itself.
    - Do NOT sound like news content.
    - Hooks must sound natural, intriguing, and timeless.

    WHAT TO GENERATE:
    - Generate 5 SHORT HOOK VARIATIONS
    - Each hook must be 1 sentence
    - Max 12 words per hook
    - Use curiosity or contradiction
    - If no trend fits naturally, IGNORE it

    OUTPUT FORMAT (STRICT JSON):
    {{
      "hooks": [
        "texto",
        "texto",
        "texto",
        "texto",
        "texto"
      ]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        return json.loads(response.text).get('hooks', [])
    except Exception as e:
        print(f"Error generating hooks: {e}")
        return []

def generate_creative_topic(style="what_if"):
    """
    Asks the AI to invent a NEW, UNIQUE topic that is not in a standard list.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    
    if style == "what_if":
        prompt = """
        TASK: Invent a unique, mind-blowing 'What If' scenario for a YouTube Short.
        - Must be speculative, scientific, or philosophical.
        - profound or paradoxical.
        - EXAMPLES: "What if shadows were alive?", "What if silence killed you?", "What if dreams were shared reality?"
        - OUTPUT: Just the straight topic string in SPANISH. No quotes.
        - DO NOT output generic ones like "zombies" or "aliens". Be creative.
        """
    elif style == "top_3":
        prompt = """
        TASK: Invent a unique "Top 3" list topic for a video.
        - Format: "Top 3 [Adjective] [Subject]"
        - Examples: "Top 3 lugares prohibidos", "Top 3 animales inmortales", "Top 3 sonidos más fuertes".
        - OUTPUT: Just the topic string in SPANISH.
        """
    else:
        prompt = """
        TASK: Invent a specific, unique curiosity topic for a YouTube Short.
        - Must be obscure but fascinating.
        - OUTPUT: Just the topic string in SPANISH.
        """
        
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip().replace('"', '')
    except Exception as e:
        print(f"Error generating creative topic: {e}")
        return None

if __name__ == "__main__":
    # Test run
    print(generate_script())
 