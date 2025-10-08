import os


def list_items(folder_name="_reports_"):
    """Return a sorted list of items (files/folders) in the target folder."""
    try:
        return sorted(os.listdir(folder_name), key=str.lower)
    except FileNotFoundError:
        print(f"Folder not found: {folder_name}")
        return []
    except Exception as e:
        print(f"Error reading folder: {e}")
        return []
