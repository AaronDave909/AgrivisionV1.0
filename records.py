import customtkinter as ctk
from pathlib import Path
import fitz
import os
import re


def list_items(folder_name="_reports_"):
    try:
        return sorted(os.listdir(folder_name), key=str.lower)
    except FileNotFoundError:
        print(f"Folder not found: {folder_name}")
        return []
    except Exception as e:
        print(f"Error reading folder: {e}")
        return []


def extract_pdf_text(file_path):
    text = ""
    try:
        with fitz.open(file_path) as pdf:
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
    lines = raw_text.splitlines()
    formatted = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[A-Z ]{4,}$", stripped):
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


def open_gallery(main_window, folder_name, title):
    main_window.withdraw()
    folder = Path(folder_name)
    folder.mkdir(exist_ok=True)

    manager = ctk.CTkToplevel()
    manager.title(title)
    manager.geometry("800x400")
    manager.resizable(False, False)
    manager.configure(fg_color="#202332")

    def return_to_main():
        manager.destroy()
        main_window.deiconify()

    top_bar = ctk.CTkFrame(manager, fg_color="#202332")
    top_bar.pack(fill="x", pady=5, padx=5)
    ctk.CTkButton(top_bar, text="← Return", width=80, height=28,
                  command=return_to_main, font=("Arial", 12),
                  fg_color="#2b2f45", hover_color="#3a3f57").pack(anchor="w", padx=5)

    container = ctk.CTkFrame(manager, fg_color="#202332")
    container.pack(fill="both", expand=True, padx=10, pady=10)

    gallery_frame = ctk.CTkScrollableFrame(container, width=230, height=320, fg_color="#202332")
    gallery_frame.pack(side="left", fill="y", padx=(0, 10), pady=5)

    viewer_frame = ctk.CTkFrame(container, corner_radius=10, fg_color="#25283f")
    viewer_frame.pack(side="right", fill="both", expand=True, pady=5)

    viewer_title = ctk.CTkLabel(viewer_frame, text="Select a PDF to view its report",
                                font=("Arial", 13, "bold"), anchor="w", text_color="white")
    viewer_title.pack(fill="x", padx=10, pady=(10, 5))

    viewer_text_frame = ctk.CTkScrollableFrame(viewer_frame, width=520, height=270, fg_color="#25283f")
    viewer_text_frame.pack(fill="both", expand=True, padx=10, pady=5)

    viewer_text_label = ctk.CTkTextbox(viewer_text_frame, wrap="none", font=("Arial", 12),
                                       fg_color="#25283f", text_color="white")
    viewer_text_label.pack(fill="both", expand=True, padx=10, pady=10)
    viewer_text_label.configure(state="disabled")

    def update_viewer(formatted_text, title_text):
        viewer_title.configure(text=f"📄 {title_text}")
        viewer_text_label.configure(state="normal")
        viewer_text_label.delete("1.0", "end")

        for style, content in formatted_text:
            if style == "header":
                viewer_text_label.insert("end", "\n" + content + "\n", "header")
                viewer_text_label.insert("end", "─" * 60 + "\n", "separator")
            elif style == "pair":
                key, value = content
                viewer_text_label.insert("end", f"{key:<28} │ {value}\n")
            else:
                viewer_text_label.insert("end", content + "\n")

        # ✅ Only colors allowed — no font changes
        viewer_text_label.tag_config("header", foreground="#00FF99")
        viewer_text_label.tag_config("separator", foreground="#555555")
        viewer_text_label.configure(state="disabled")

    ctk.CTkButton(viewer_frame, text="Clear Viewer", width=100, height=30,
                  command=lambda: update_viewer([], "Select a PDF to view its report"),
                  font=("Arial", 12), fg_color="#2b2f45", hover_color="#3a3f57").pack(pady=(5, 10))

    items = list_items(folder_name)
    if not items:
        ctk.CTkLabel(gallery_frame, text=f"The {folder_name} folder is empty",
                     text_color="white", font=("Arial", 12)).pack(pady=20)
        return

    icons = {"pdf": "📄", "other": "📦"}
    columns = 1

    def show_pdf_inline(file_path):
        raw_text = extract_pdf_text(file_path)
        formatted_text = format_pdf_text(raw_text)
        update_viewer(formatted_text, Path(file_path).name)

    for index, item in enumerate(items):
        item_path = folder / item
        ext = item_path.suffix.lower()
        icon = icons["pdf"] if ext == ".pdf" else icons["other"]

        tile = ctk.CTkFrame(gallery_frame, width=210, height=50, corner_radius=10, fg_color="#2b2f45")
        tile.grid(row=index // columns, column=index % columns, padx=10, pady=5, sticky="nsew")

        def on_enter(e, t=tile): t.configure(fg_color="#3a3f57")
        def on_leave(e, t=tile): t.configure(fg_color="#2b2f45")
        tile.bind("<Enter>", on_enter)
        tile.bind("<Leave>", on_leave)

        ctk.CTkLabel(tile, text=icon, font=("Arial", 20)).pack(side="left", padx=10)
        display_name = item if len(item) <= 22 else item[:19] + "..."
        ctk.CTkLabel(tile, text=display_name, anchor="w", font=("Arial", 12)).pack(side="left", padx=5)

        if ext == ".pdf":
            tile.bind("<Button-1>", lambda e, path=item_path: show_pdf_inline(path))
            for child in tile.winfo_children():
                child.bind("<Button-1>", lambda e, path=item_path: show_pdf_inline(path))


def main_app():
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("Main App")
    app.geometry("400x200")
    app.configure(fg_color="#202332")

    ctk.CTkButton(app, text="Reports Gallery",
                  command=lambda: open_gallery(app, "_reports_", "Reports Gallery"),
                  font=("Arial", 13), fg_color="#2b2f45", hover_color="#3a3f57").pack(expand=True, pady=5)
    ctk.CTkButton(app, text="Diseases Gallery",
                  command=lambda: open_gallery(app, "_diseases_", "Diseases Gallery"),
                  font=("Arial", 13), fg_color="#2b2f45", hover_color="#3a3f57").pack(expand=True, pady=5)

    app.mainloop()


if __name__ == "__main__":
    main_app()
