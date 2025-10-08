import customtkinter as ctk
from PIL import Image
from shared_components import SharedComponents as SC
import os
import random

def gallery_preview(root):
    """Returns a CTkImage and text to display as part of a button preview."""
    gallery_folder = "gallery_files"
    random_image = None
    gallery_photo = None
    file_label = ""

    if os.path.exists(gallery_folder):
        jpg_files = [f for f in os.listdir(gallery_folder) if f.lower().endswith(".jpg")]
        if jpg_files:
            random_image = random.choice(jpg_files)
            img_path = os.path.join(gallery_folder, random_image)

            # Load & resize the image
            img = Image.open(img_path)
            img = img.resize((168, 168))
            gallery_photo = ctk.CTkImage(light_image=img, dark_image=img, size=(168, 168))

            # Extract filename (without extension)
            file_label = os.path.splitext(random_image)[0]
        else:
            print("No JPG images found in gallery_files.")
    else:
        print(f"Folder '{gallery_folder}' not found.")

    return gallery_photo, file_label


class GalleryPage(SC):
    def __init__(self):
        super().__init__()
        self.create_title(text="Capture Gallery", x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        self.undo_button()

        # Scrollable gallery setup
        self.create_scrollable_gallery()

    def create_scrollable_gallery(self):
        # === Canvas for scrollable content ===
        self.canvas = ctk.CTkCanvas(
            self.root,
            bg="#202332",
            highlightthickness=0
        )
        self.canvas.place(x=120, y=60, relwidth=0.84, relheight=0.85)

        # === Scrollbar at the right edge ===
        self.scrollbar = ctk.CTkScrollbar(
            self.root,
            orientation="vertical",
            command=self.canvas.yview,
            # --- Customize appearance here ---
            width=40,  # scrollbar thickness
            fg_color="#222533",   # background track color
            button_color="#4C516D",  # scroll thumb color
            button_hover_color="#6A7090",  # hover thumb color
        )
        self.scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")  # pinned right

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # === Frame inside the canvas (holds the images) ===
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color="#202332")

        # Update scrollregion when the content size changes
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Load the gallery images
        self.load_gallery_images()

    def load_gallery_images(self, folder_path="gallery_files"):
        panel_width = 197.33
        panel_height = 190.45
        image_width = 141
        image_height = 146
        spacing = 13
        max_per_row = 3

        if not os.path.exists(folder_path):
            print(f"Folder '{folder_path}' not found.")
            return

        jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
        if not jpg_files:
            print("No JPG images found.")
            return

        for index, filename in enumerate(jpg_files):
            file_path = os.path.join(folder_path, filename)

            # Load and resize image
            img = Image.open(file_path)
            img = img.resize((int(image_width), int(image_height)))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(image_width, image_height))

            col = index % max_per_row
            row = index // max_per_row

            # Create frame for each image
            frame = ctk.CTkFrame(self.scrollable_frame, width=panel_width, height=panel_height, fg_color="#2A2E3F", corner_radius=10)
            frame.grid(row=row, column=col, padx=10, pady=10)

            # Image button
            img_button = ctk.CTkButton(
                frame,
                image=ctk_img,
                text="",
                width=image_width,
                height=image_height,
                fg_color="transparent",
                hover_color="#3B3F51",
                command=lambda path=file_path: print(f"Clicked: {path}")
            )
            img_button.image = ctk_img
            img_button.place(relx=0.5, rely=0.45, anchor="center")

            # Filename label
            name = os.path.splitext(filename)[0]
            name_label = ctk.CTkLabel(frame, text=name, text_color="white", font=("Arial", 14))
            name_label.place(relx=0.5, rely=0.9, anchor="center")
