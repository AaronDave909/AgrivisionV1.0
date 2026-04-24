import os
import json
from datetime import datetime

from language_manager import get_text

class PestAnalytics:
    """
    A helper class to manage reading from and writing to
    a separate JSON file for pest analytics.
    """
    def __init__(self):
        self.gallery_path = "Page_files/gallery_files"
        self.json_path = os.path.join("Page_files/gallery_files", "gallery_data.json")
        
        # Ensure the directory for the JSON file exists
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)

    def _load_json(self):
        """Loads the master pest JSON. Returns an empty dict if it doesn't exist or is empty."""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r') as f:
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
            else:
                return {}
        except (json.JSONDecodeError, Exception) as e:
            # Localized terminal log
            print(f"❌ {get_text('log_err_pest_json_read')}: {e}")
            return {}

    def _save_json(self, data):
        """Saves the provided dictionary to the master pest JSON file."""
        try:
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            # Localized terminal log
            print(f"❌ {get_text('log_err_pest_json_write')}: {e}")

    def save_detection(self, pest_name, timestamp_obj, image_filename):
        """
        Loads the pest data, adds a new entry, and saves it.
        """
        master_data = self._load_json()
        timestamp_str = timestamp_obj.strftime("%b %d, %Y %I:%M %p")
        
        new_detection_data = {
            "pest_name": pest_name,
            "timestamp": timestamp_str
        }
        
        master_data[image_filename] = new_detection_data
        self._save_json(master_data)

        # Localized console feedback
        # This maps the raw model output to your localized label
        pest_key = f"lbl_pest_{pest_name.lower().replace(' ', '_')}"
        localized_pest = get_text(pest_key)
        
        print(f"✅ {get_text('log_pest_saved')}: {localized_pest} -> {image_filename}")