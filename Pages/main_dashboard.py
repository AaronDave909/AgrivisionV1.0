from shared_components import SharedComponents as SC
from Pages.crop_count import show_crop_input_popup
from Pages.gallery import GalleryPage
from PIL import Image, ImageTk
import customtkinter as ctk

class MyDashboard(SC):

    def open_gallery(self):
        """Opens the Gallery Page while keeping the same window position and size."""
        geometry = self.root.geometry()  # Save current window geometry
        self.root.destroy()

        gallery = GalleryPage()
        gallery.root.geometry(geometry)  # Apply same geometry (prevents window 'jumping')
        gallery.root.mainloop()

    def __init__(self):
        super().__init__()
        self.create_title()
        self.create_left_panel()
        self.create_leaf_image()

        # Record Button
        self.create_record_button(x=107 / 2, y=480 / 2, command=None)
        
        # Settings Button
        self.settings_button()

        # Crops Button
        self.crops_button = self.create_button(
            text="Crops in Monitor\n",
            x=118, y=75,
            width=140, height=140,
            anchor="s",
            command=lambda: show_crop_input_popup(self.root, self.crops_button)
        )
        
        # Recent Disease Button
        self.create_button(
            text="Recent Disease\nDetected",
            x=270, y=75,
            anchor="s",
            command=None
        )

        # Manage Files Button with Image
        futures_photo = self.load_futures_icon()

        self.create_button(
            text="Manage Files\n",
            x=422, y=75,
            command=None,
            image=futures_photo,
            compound="top"
        )
        
        # Analytics Button
        self.create_button(
            text="\n  Analytics",
            x=121, y=232,
            width=205, height=232,
            anchor="nw",
            command=None
        )
        
        # Capture Gallery Button
        self.create_button(
            text="\n  Capture Gallery",
            x=340, y=232,
            width=222, height=229,
            anchor="nw",
            command=self.open_gallery
        )
        
        # Disease Record Panel
        self.create_panel(
            text="\nDisease Record History",
            x=572, y=75,
            anchor="nw",
            width=217, height=275
        )
        
        # Dock Mode Button
        self.create_button(
            text="Dock Mode",
            x=572, y=368,
            width=217, height=37,
            anchor="center",
            font=("Arial", 24, "bold"),
            command=None
        )
        
        # Diseases Button
        self.create_button(
            text="Diseases",
            x=572, y=424,
            width=217, height=37,
            anchor="center",
            font=("Arial", 24, "bold"),
            command=None
        )

        # Help Button (rounded)
        self.create_button(
            text="Help",
            x=674, y=21,
            width=114, height=37,
            anchor="center",
            font=("Arial", 20, "bold"),
            corner_radius=50,
            command=None
        )

    def run(self):
        """Runs the main loop for the dashboard."""
        self.root.mainloop()
