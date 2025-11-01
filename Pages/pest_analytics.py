import os
import json
from datetime import datetime

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
            print(f"❌ Error reading pest JSON: {e}. Returning empty dict.")
            return {}

    def _save_json(self, data):
        """Saves the provided dictionary to the master pest JSON file."""
        try:
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"❌ Error writing pest JSON: {e}")

    def save_detection(self, pest_name, timestamp_obj, image_filename):
        """
        Loads the pest data, adds a new entry, and saves it.
        The image_filename is used as the primary key, just like in gallery_data.json.
        """
        master_data = self._load_json()
        
        # Use the same timestamp format as your other files
        timestamp_str = timestamp_obj.strftime("%b %d, %Y %I:%M %p")
        
        # Create the new data entry
        new_detection_data = {
            "pest_name": pest_name,
            "timestamp": timestamp_str
        }
        
        # Add the new entry using the image filename as the key
        master_data[image_filename] = new_detection_data
        
        # Save the updated dictionary
        self._save_json(master_data)
        print(f"✅ Pest detection saved: {pest_name} -> {image_filename}")
