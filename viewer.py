import os
from PyPDF2 import PdfReader
import subprocess
import platform


FOLDER_PATH = "_record_"


def get_pdf_list():
    """Return a list of dictionaries with PDF metadata."""
    if not os.path.exists(FOLDER_PATH):
        raise FileNotFoundError(f"Folder '{FOLDER_PATH}' not found.")

    pdf_files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith(".pdf")]

    result = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(FOLDER_PATH, pdf_file)
        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
            info = reader.metadata
            title = info.title if info and info.title else pdf_file
        except Exception:
            title = pdf_file
            num_pages = "Unknown"

        result.append({
            "title": title,
            "pages": num_pages,
            "path": pdf_path
        })

    return result


def open_pdf(path: str):
    """Open a PDF file using the default system viewer."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":  # macOS
            subprocess.call(["open", path])
        else:  # Linux / others
            subprocess.call(["xdg-open", path])
    except Exception as e:
        raise RuntimeError(f"Could not open PDF: {e}")
