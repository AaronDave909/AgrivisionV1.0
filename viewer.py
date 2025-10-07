import os
import sys
import subprocess


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


def open_pdf(file_path):
    """Open the selected file or folder using the system's default app."""
    try:
        if sys.platform.startswith("darwin"):  # macOS
            subprocess.call(("open", file_path))
        elif os.name == "nt":  # Windows
            os.startfile(file_path)
        elif os.name == "posix":  # Linux
            subprocess.call(("xdg-open", file_path))
    except Exception as e:
        print(f"Error opening {file_path}: {e}")
