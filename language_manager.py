import json
import os

class LanguageManager:
    def __init__(self, default_lang="en"):
        self.current_lang = default_lang
        self.translations = {}
        
        # This safely finds the 'locales' folder no matter where you run the script from
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.locales_dir = os.path.join(base_dir, "locales")

        lang_file = os.path.join(base_dir, "Page_files", "lang_state.txt")
        if os.path.exists(lang_file):
            try:
                with open(lang_file, "r") as f:
                    saved_lang = f.read().strip()
                    if saved_lang in ["en", "tl"]:
                        self.current_lang = saved_lang
            except:
                pass
        
        self.load_language(self.current_lang)

    def load_language(self, lang_code):
        """Loads the JSON dictionary for the requested language."""
        file_path = os.path.join(self.locales_dir, f"{lang_code}.json")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                self.translations = json.load(file)
            self.current_lang = lang_code
        except FileNotFoundError:
            print(f"Error: Could not find language file at {file_path}")
        except Exception as e:
            print(f"Error loading language {lang_code}: {e}")

    def get_text(self, key):
        """Returns the translated word, or the [key] itself if you forgot to add it to JSON."""
        return self.translations.get(key, f"[{key}]")

    def set_language(self, lang_code):
        """Switches the active dictionary."""
        self.load_language(lang_code)

# Create a single global instance of the manager
i18n = LanguageManager()

# Create a quick helper function so your UI code looks super clean
def get_text(key):
    return i18n.get_text(key)