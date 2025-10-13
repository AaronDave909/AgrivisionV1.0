import customtkinter as ctk
from pathlib import Path
import fitz  # PyMuPDF
from viewer import list_items
import re


def extract_pdf_text(file_path):
    """Extract readable text from a PDF."""
    text = ""
    try:
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text("text") + "\n"
    except Exception as e:
        text = f"Error reading PDF: {e}"
    return text.strip() or "[No text found in this PDF]"


def format_pdf_text(raw_text):
    """
    Format the extracted PDF text into a structured, stylized layout.
    - Bold section headers
    - Align key-value pairs
    - Keep clean spacing
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    formatted = ""

    for line in lines:
        # Detect headers like PLANT INFORMATION, DETECTION REPORT
        if re.match(r"^[A-Z ]{4,}$", line):
            formatted += f"\n\n**{line}**\n"
        # Detect key-value pairs
        elif ":" in line:
            key, value = line.split(":", 1)
            formatted += f"{key.strip()}: {value.strip()}\n"
        else:
            formatted += f"{line}\n"

    return formatted.strip()


def open_gallery(main_window, folder_name, title):
    """Main gallery + inline PDF text viewer."""
    main_window.withdraw()

    folder = Path(folder_name)
    folder.mkdir(exist_ok=True)

    # === Window setup ===
    manager = ctk.CTkToplevel()
    manager.title(title)
    manager.geometry("1024x600")
    manager.resizable(False, False)

    def return_to_main():
        manager.destroy()
        main_window.deiconify()

    # === Top bar ===
    top_bar = ctk.CTkFrame(manager, fg_color="transparent")
    top_bar.pack(fill="x", pady=5, padx=5)
    ctk.CTkButton(top_bar, text="← Return", width=100, command=return_to_main).pack(anchor="w", padx=5)

    # === Main split layout ===
    container = ctk.CTkFrame(manager)
    container.pack(fill="both", expand=True, padx=10, pady=10)

    # Gallery (left)
    gallery_frame = ctk.CTkScrollableFrame(container, width=280, height=520)
    gallery_frame.pack(side="left", fill="y", padx=(0, 10), pady=5)

    # Viewer (right)
    viewer_frame = ctk.CTkFrame(container, corner_radius=10)
    viewer_frame.pack(side="right", fill="both", expand=True, pady=5)

    viewer_title = ctk.CTkLabel(viewer_frame, text="Select a PDF to view its report",
                                font=("Arial", 15, "bold"), anchor="w")
    viewer_title.pack(fill="x", padx=10, pady=(10, 5))

    viewer_text_frame = ctk.CTkScrollableFrame(viewer_frame, width=700, height=460)
    viewer_text_frame.pack(fill="both", expand=True, padx=10, pady=5)

    viewer_text_label = ctk.CTkTextbox(viewer_text_frame, wrap="word", font=("Consolas", 13))
    viewer_text_label.pack(fill="both", expand=True, padx=10, pady=10)
    viewer_text_label.configure(state="disabled")

    def update_viewer(text, title_text):
        """Render formatted text with styled headings."""
        viewer_title.configure(text=f"📄 {title_text}")
        viewer_text_label.configure(state="normal")
        viewer_text_label.delete("1.0", "end")
        viewer_text_label.insert("1.0", text)
        viewer_text_label.configure(state="disabled")

    close_btn = ctk.CTkButton(viewer_frame, text="Clear Viewer",
                              command=lambda: update_viewer("", "Select a PDF to view its report"))
    close_btn.pack(pady=(5, 10))

    # === Gallery population ===
    items = list_items(folder_name)
    if not items:
        ctk.CTkLabel(gallery_frame, text=f"The {folder_name} folder is empty").pack(pady=20)
        return

    icons = {"folder": "📁", "pdf": "📄", "other": "📦"}
    columns = 1  # one per line

    def show_pdf_inline(file_path):
        """Extract and show formatted PDF text."""
        raw_text = extract_pdf_text(file_path)
        formatted_text = format_pdf_text(raw_text)
        update_viewer(formatted_text, Path(file_path).name)

    for index, item in enumerate(items):
        item_path = folder / item
        ext = item_path.suffix.lower()
        icon = icons["pdf"] if ext == ".pdf" else icons["other"]

        # Tile
        tile = ctk.CTkFrame(gallery_frame, width=260, height=60, corner_radius=10)
        tile.grid(row=index // columns, column=index % columns, padx=10, pady=5, sticky="nsew")

        def on_enter(e, t=tile): t.configure(fg_color="#2a2d2e")
        def on_leave(e, t=tile): t.configure(fg_color="transparent")
        tile.bind("<Enter>", on_enter)
        tile.bind("<Leave>", on_leave)

        # Icon + label
        ctk.CTkLabel(tile, text=icon, font=("Arial", 28)).pack(side="left", padx=10)
        display_name = item if len(item) <= 25 else item[:22] + "..."
        ctk.CTkLabel(tile, text=display_name, anchor="w").pack(side="left", padx=5)

        if ext == ".pdf":
            tile.bind("<Button-1>", lambda e, path=item_path: show_pdf_inline(path))
            for child in tile.winfo_children():
                child.bind("<Button-1>", lambda e, path=item_path: show_pdf_inline(path))


def main_app():
    """Main entry point."""
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("Main App")
    app.geometry("400x200")

    ctk.CTkButton(app, text="Reports Gallery",
                  command=lambda: open_gallery(app, "_reports_", "Reports Gallery")).pack(expand=True, pady=5)
    ctk.CTkButton(app, text="Diseases Gallery",
                  command=lambda: open_gallery(app, "_diseases_", "Diseases Gallery")).pack(expand=True, pady=5)

    app.mainloop()


if __name__ == "__main__":
    main_app()
