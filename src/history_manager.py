import json
import os
import difflib

class HistoryManager:
    def __init__(self, history_file="video_history.json"):
        self.history_file = history_file
        self.data = self._load_history()

    def _load_history(self):
        if not os.path.exists(self.history_file):
            return {"titles": [], "used_trends": []}
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"titles": [], "used_trends": [], "used_topics": []}

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️ Error saving history: {e}")

    def _normalize_title(self, title):
        """Standardizes title for comparison: remove punctuation, lower case."""
        if not title: return ""
        # Remove common punctuation: ¿ ? ! ¡ . , :
        chars_to_remove = "¿?!¡.,:"
        norm = title.lower()
        for c in chars_to_remove:
            norm = norm.replace(c, "")
        return norm.strip()

    def _strip_common_prefixes(self, title):
        """Removes common 'What If' prefixes to compare core topic."""
        prefixes = [
            "qué pasaría si", "que pasaria si", 
            "y si", 
            "what if", 
            "si " # aggressive strip of 'si' at start
        ]
        t = self._normalize_title(title)
        for p in prefixes:
            if t.startswith(p):
                t = t[len(p):].strip()
        return t

    def is_title_used(self, title):
        if not title: return False
        
        # 1. Exact/Normalized Match
        check_norm = self._normalize_title(title)
        
        # 2. Fuzzy Match on Core Topic
        check_core = self._strip_common_prefixes(title)
        
        # Check against normalized history
        for t in self.data.get("titles", []):
            # Check 1: Normalization
            hist_norm = self._normalize_title(t)
            if hist_norm == check_norm:
                return True
                
            # Check 2: Fuzzy Core Logic
            hist_core = self._strip_common_prefixes(t)
            
            # Safety: Don't fuzzy match very short words (e.g. "Sol" vs "Sal")
            if len(check_core) < 5 or len(hist_core) < 5:
                continue
                
            similarity = difflib.SequenceMatcher(None, check_core, hist_core).ratio()
            # Threshold 0.75 catch mismatches like "pudiéramos" vs "pudieras"
            if similarity > 0.75: 
                print(f"      ⚠️ Fuzzy Duplicate Detected: '{title}' matches '{t}' (Score: {similarity:.2f})")
                return True
                
        return False

    def add_title(self, title):
        """Adds a title to history if not already present."""
        if title and not self.is_title_used(title):
            self.data.setdefault("titles", []).append(title)
            self._save_history()

    def add_used_topic(self, topic):
        """Tracks the raw input topic (e.g. from constants) to prevent re-selection."""
        if topic:
            # Normalize to avoid "Topic" vs "topic" duplicates
            norm = topic.strip().lower()
            if norm not in [t.lower() for t in self.data.get("used_topics", [])]:
                self.data.setdefault("used_topics", []).append(topic)
                self._save_history()

    def is_topic_used(self, topic):
        """Checks if a raw input topic has been used."""
        if not topic: return False
        norm = topic.strip().lower()
        return norm in [t.lower() for t in self.data.get("used_topics", [])]

    def add_trend(self, trend):
        if trend:
            # Check if likely already used (exact match)
            if trend not in self.data.setdefault("used_trends", []):
                self.data["used_trends"].append(trend)
                self._save_history()

    def filter_trends(self, trends_list):
        """Returns only trends that haven't been used yet."""
        if not trends_list: return []
        used = set(self.data.get("used_trends", []))
        return [t for t in trends_list if t not in used]
