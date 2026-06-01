import customtkinter as ctk
from pathlib import Path
import fitz  # PyMuPDF
import os
import re

# IMPORT ALL COLOR CONSTANTS FROM SHARED COMPONENTS
from shared_components import (
    SharedComponents as SC, LEFT_PANEL_WIDTH,
    BG_COLOR, LEFT_PANEL_COLOR, BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR
)

# --- FIX for UnicodeEncodeError ---
import sys
import io
# Forces stdout to use UTF-8 encoding for Unicode characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# --- End of fix ---

# --- HELPER FUNCTIONS ---
def list_items(folder_path): 
    """Safely lists all items in a given folder."""
    absolute_folder_path = os.path.abspath(str(folder_path))
    print(f"[DEBUG] list_items checking folder: {absolute_folder_path}")
    try:
        items = sorted(os.listdir(folder_path), key=str.lower)
        print(f"[DEBUG] list_items found: {items}")
        return items
    except FileNotFoundError:
        print(f"[DEBUG] Folder not found: {absolute_folder_path}")
        return []
    except Exception as e:
        print(f"Error reading folder {absolute_folder_path}: {e}")
        return []

def extract_pdf_text(file_path):
    """Extracts text from a PDF, trying to maintain layout."""
    text = ""
    try:
        with fitz.open(str(file_path)) as pdf:
            for page in pdf:
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: (b[1], b[0]))
                for b in blocks:
                    line = b[4].rstrip() 
                    text += line + "\n"
    except Exception as e:
        text = f"Error reading PDF: {e}"
    return text.strip() or "[No text found in this PDF]"


def format_pdf_text(raw_text):
    """Applies simple formatting styles to the raw text for display."""
    lines = raw_text.splitlines()
    formatted = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[A-Z ]{4,}$", stripped) and len(stripped) > 3:
            formatted.append(("header", stripped))
        elif ":" in stripped:
            key, value = stripped.split(":", 1)
            formatted.append(("pair", (key.strip(), value.strip())))
        else:
            parts = re.split(r"\s{2,}", stripped)
            if len(parts) == 2:
                formatted.append(("pair", (parts[0].strip(), parts[1].strip())))
            else:
                formatted.append(("normal", stripped))
    return formatted
# --- END HELPER FUNCTIONS ---

class ReportViewerPage(SC):

    def __init__(self, folder_name, title, return_page="dashboard"):
        """
        Initializes the PDF Report Viewer page.
        :param folder_name: The folder name relative to the project root (e.g., "_reports_")
        :param title: The title to display at the top of the page.
        :param return_page: The page to return to (currently only "dashboard").
        """
        super().__init__()

        # --- Define Fonts Here ---
        self.TEXT_FONT = ctk.CTkFont(family="Arial", size=12)
        self.HEADER_FONT = ctk.CTkFont(family="Arial", size=13, weight="bold")
        self.ICON_FONT = ctk.CTkFont(family="Arial", size=20)

        # --- Construct absolute path relative to THIS script file ---
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        self.folder_path = project_root / folder_name
        self.folder_name_display = folder_name

        # DEBUG: Ensure folder exists using the calculated absolute path
        if not self.folder_path.exists():
            print(f"[DEBUG] Attempting to create folder: {self.folder_path.resolve()}")
            try:
                self.folder_path.mkdir(parents=True, exist_ok=True) 
            except Exception as e:
                 print(f"[ERROR] Could not create folder {self.folder_path.resolve()}: {e}")
        else:
             print(f"[DEBUG] Folder already exists: {self.folder_path.resolve()}")

        self.return_page = return_page

        # --- Standard Page Setup ---
        self.create_left_panel()
        self.create_leaf_image()
        self.create_title(text=title, x=119, y=0)
        self.create_battery_indicator(x=15, y=100)
        self.undo_button(command=self.return_to_dashboard)

        # --- Page-Specific UI ---
        start_x = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        start_y = self._scale_value(60, 'y')

        # Using self._get_color(BG_COLOR) for main container
        container = ctk.CTkFrame(self.root, fg_color=self._get_color(BG_COLOR))
        container.place(
            x=start_x,
            y=start_y,
            relwidth=1.0 - (start_x / self.root.winfo_width()),
            relheight=1.0 - (start_y / self.root.winfo_height())
        )

        gallery_w = self._scale_value(250, 'x') 

        self.gallery_frame = ctk.CTkScrollableFrame(container, width=gallery_w, fg_color=self._get_color(BG_COLOR))
        self.gallery_frame.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=5)

        viewer_frame = ctk.CTkFrame(container, corner_radius=10, fg_color=self._get_color(LEFT_PANEL_COLOR))
        viewer_frame.pack(side="right", fill="both", expand=True, pady=5, padx=(0, 5))

        self.viewer_title = ctk.CTkLabel(
            viewer_frame, 
            text="Select a PDF to view its report",
            font=self.HEADER_FONT,
            anchor="w", 
            text_color=self._get_color(TEXT_COLOR)
        )
        self.viewer_title.pack(fill="x", padx=10, pady=(10, 5))

        viewer_text_frame = ctk.CTkScrollableFrame(viewer_frame, fg_color=self._get_color(LEFT_PANEL_COLOR))
        viewer_text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.viewer_text_label = ctk.CTkTextbox(
            viewer_text_frame, 
            wrap="none",
            font=self.TEXT_FONT,
            fg_color=self._get_color(LEFT_PANEL_COLOR), 
            text_color=self._get_color(TEXT_COLOR)
        )
        self.viewer_text_label.pack(fill="both", expand=True, padx=10, pady=10)
        self.viewer_text_label.configure(state="disabled")

        ctk.CTkButton(
            viewer_frame, 
            text="Clear Viewer",
            width=self._scale_value(100, 'x'), 
            height=self._scale_value(30, 'y'),
            command=lambda: self.update_viewer([], "Select a PDF to view its report"),
            font=self.TEXT_FONT,
            text_color=self._get_color(TEXT_COLOR),
            fg_color=self._get_color(BUTTON_COLOR), 
            hover_color=self._get_color(BUTTON_HOVER)
        ).pack(pady=(5, 10))

        # Adjusted tags to pop on both light and dark mode
        self.viewer_text_label.tag_config("header", foreground="#4CAF50") # Nice universal Green
        self.viewer_text_label.tag_config("separator", foreground="gray")

        self.load_gallery_items()

    def load_gallery_items(self):
        """Finds PDFs in the folder and creates list items for them."""
        print(f"[DEBUG] load_gallery_items called for folder path: {self.folder_path}")
        items = list_items(self.folder_path) 
        print(f"[DEBUG] load_gallery_items received items: {items}")

        if not items:
            ctk.CTkLabel(
                self.gallery_frame, 
                text=f"The {self.folder_name_display} folder is empty",
                text_color=self._get_color(TEXT_COLOR), 
                font=self.TEXT_FONT
            ).pack(pady=20)
            return

        # Restored standard unicode emojis
        icons = {"pdf": "📄", "other": "📦"}
        
        tile_w = self._scale_value(240, 'x') 
        tile_h = self._scale_value(50, 'y')

        pdf_found = False

        for item in items:
            item_path = self.folder_path / item
            ext = item_path.suffix.lower()

            print(f"[DEBUG] Processing item path: {item_path}, Extension: {ext}")

            icon = icons.get(ext[1:], icons["other"])

            tile = ctk.CTkFrame(
                self.gallery_frame, 
                width=tile_w, 
                height=tile_h,
                corner_radius=10, 
                fg_color=self._get_color(BUTTON_COLOR)
            )
            tile.pack(fill="x", padx=5, pady=5)
            tile.pack_propagate(False)

            def on_enter(e, t=tile): t.configure(fg_color=self._get_color(BUTTON_HOVER))
            def on_leave(e, t=tile): t.configure(fg_color=self._get_color(BUTTON_COLOR))
            tile.bind("<Enter>", on_enter)
            tile.bind("<Leave>", on_leave)

            ctk.CTkLabel(tile, text=icon, text_color=self._get_color(TEXT_COLOR), font=self.ICON_FONT).pack(side="left", padx=10)

            display_name = item
            ctk.CTkLabel(
                tile, 
                text=display_name, 
                anchor="w", 
                text_color=self._get_color(TEXT_COLOR),
                font=self.TEXT_FONT
            ).pack(side="left", padx=5, fill="x", expand=True)

            if ext == ".pdf":
                pdf_found = True
                tile.bind("<Button-1>", lambda e, path=item_path: self.show_pdf_inline(path))
                for child in tile.winfo_children():
                    child.bind("<Button-1>", lambda e, path=item_path: self.show_pdf_inline(path))
            else:
                 print(f"[DEBUG] Skipping non-PDF item: {item}")

        if not pdf_found and items:
             print("[DEBUG] No PDF files found in the listed items.")


    def show_pdf_inline(self, file_path):
        """Callback to extract, format, and display PDF text in the viewer."""
        print(f"[DEBUG] show_pdf_inline opening: {file_path}")
        raw_text = extract_pdf_text(file_path)
        formatted_text = format_pdf_text(raw_text)
        self.update_viewer(formatted_text, file_path.name)

    def update_viewer(self, formatted_text, title_text):
        """Updates the text and title in the viewer."""
        self.viewer_title.configure(text=f"📄 {title_text}")

        self.viewer_text_label.configure(state="normal") 
        self.viewer_text_label.delete("1.0", "end")

        for style, content in formatted_text:
            if style == "header":
                self.viewer_text_label.insert("end", "\n" + content + "\n", "header")
                # Restored clean Unicode line separator
                self.viewer_text_label.insert("end", "─" * 80 + "\n", "separator") 
            elif style == "pair":
                key, value = content
                # Restored clean Unicode vertical bar
                self.viewer_text_label.insert("end", f"{key:<40} │ {value}\n") 
            else:
                self.viewer_text_label.insert("end", content + "\n")

        self.viewer_text_label.configure(state="disabled") 

    def return_to_dashboard(self):
        """Destroys this page and re-opens the main dashboard."""
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard
        app = MyDashboard()
        app.run()