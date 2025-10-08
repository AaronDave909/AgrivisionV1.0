import customtkinter as ctk
from PIL import Image, ImageTk
from shared_components import SharedComponents as SC

class GalleryPage(SC):
    def __init__(self):
        super().__init__()
        self.create_title(text="Capture Gallery", x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        self.undo_button()

        # Placeholder for gallery images
        self.gallery_frame = ctk.CTkFrame(self.root, width=600, height=400, fg_color="#2A2E3F")
        self.gallery_frame.place(x=150, y=80)

