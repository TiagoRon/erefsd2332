import os
import json
import random
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def get_trending_topics(count=5, geo='AR'):
    """
    Fetches trending topics using Google Gemini with Search Grounding.
    Returns a list of strings (topics).
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ Error: GOOGLE_API_KEY not found. Using fallback topics.")
        return ["Datos Curiosos", "Misterios del Océano", "Tecnología Futura"]

    client = genai.Client(api_key=api_key)
    
    # Prompt explicitly requests a JSON list of meaningful topics
    prompt = f"""
    List {count + 5} specific, currently trending search topics in {geo} (Argentina/Latin America) right now. 
    Focus on viral news, entertainment, sports, or curiosities.
    Output ONLY a raw JSON list of strings, e.g. ["Topic A", "Topic B"].
    Do NOT use Markdown formatting.
    """
    
    print(f"🤖 Asking Gemini for trends in {geo}...")
    
    try:
        # Use Search Grounding to get real-time info
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        # Parse response (it might contain text around the JSON)
        text = response.text
        # Clean potential markdown
        text = text.replace("```json", "").replace("```", "").strip()
        
        try:
            trends = json.loads(text)
            if isinstance(trends, list) and len(trends) > 0:
                print(f"✅ Found {len(trends)} trends: {trends[:3]}...")
                
                # Deduplication
                from src.history_manager import HistoryManager
                hm = HistoryManager()
                unique_trends = hm.filter_trends(trends)
                
                if len(unique_trends) < count:
                    print(f"⚠️ Warning: Only {len(unique_trends)} new trends found (others were used). Returning all available.")
                    if len(unique_trends) == 0:
                         print("⚠️ All trends were used! Returning original list to avoid empty.")
                         unique_trends = trends # Fallback
                
                random.shuffle(unique_trends)
                return unique_trends[:count]
            else:
                 print(f"⚠️ Unexpected JSON format: {trends}")
        except json.JSONDecodeError:
             print(f"⚠️ Failed to parse JSON from Gemini: {text[:100]}...")

    except Exception as e:
        print(f"❌ Error fetching trends from Gemini: {e}")
        
    except Exception as e:
        print(f"❌ Error fetching trends from Gemini: {e}")
        
    print("⚠️ Using fallback topics due to error.")
    trends = ["Curiosidades del Mundo", "Datos Increíbles", "Ciencia Loca", "Historia Oculta", "Misterios Sin Resolver"]
    
    # Filter Fallback too just in case
    from src.history_manager import HistoryManager
    hm = HistoryManager()
    filtered = hm.filter_trends(trends)
    if not filtered:
        return trends # Fallback if all used
    return filtered[:count]

if __name__ == "__main__":
    t = get_trending_topics(5)
    print("Final Trends:", t)
