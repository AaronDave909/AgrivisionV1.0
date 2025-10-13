from shared_components import SharedComponents as SC
from Pages.crop_count import show_crop_input_popup
from Pages.gallery import GalleryPage, gallery_preview
from Pages.settings import SettingsPage  # Import here to avoid circular import
from PIL import Image, ImageTk
import customtkinter as ctk
import os

class MyDashboard(SC):

    def open_gallery(self):
        geometry = self.root.geometry()  # Save current window geometry
        self.root.destroy()

        gallery = GalleryPage()
        gallery.root.geometry(geometry)  # Apply same geometry (prevents window 'jumping')
        gallery.root.mainloop()

    def open_settings(self):
        geometry = self.root.geometry()
        self.root.destroy()
        settings = SettingsPage()
        settings.root.geometry(geometry)
        settings.root.mainloop()

    def __init__(self):
        super().__init__()
        self.create_title()
        self.create_left_panel()
        self.create_leaf_image()

        # Record Button
        self.create_record_button(x=107 / 2, y=480 / 2, command=None)
        
        # Settings Button
        self.settings_button(command=self.open_settings)

        # === Read saved crop count from file ===
        crops_file = os.path.join("Page_files", "crops_monitored.txt")
        if os.path.exists(crops_file):
            try:
                with open(crops_file, "r") as f:
                    saved_crops = int(f.read().strip())
            except ValueError:
                saved_crops = 0
        else:
            saved_crops = 0

        # Crops Button
        self.crops_button = self.create_button(
            text="Crops in Monitor\n",
            x=118, y=75,
            width=140, height=140,
            anchor="s",
            command=lambda: show_crop_input_popup(self.root, self.crops_button)
        )

        if saved_crops > 0:
            frame = ctk.CTkFrame(self.crops_button, fg_color="#2A2E3F")
            frame.place(relx=0.15, rely=0.2, anchor="nw")
            num_label = ctk.CTkLabel(
                frame,
                text=str(saved_crops),
                font=("Arial", 32, "bold"),
                text_color="white",
                fg_color="#2A2E3F"
            )
            num_label.pack()
            self.crops_button.number_frame = frame
        
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
            anchor="s",
            command=None,
            image=futures_photo,
            compound="top"
        )
        
        # Analytics Button
        self.create_button(
            text="Analytics",
            x=121, y=232,
            width=205, height=232,
            anchor="n",
            command=None
        )
        

        gallery_photo, file_label = gallery_preview(self.root)

        # Capture Gallery Button
        self.create_button(
            text="Capture Gallery",
            x=340, y=232,
            width=222, height=232,
            anchor="n",
            image=gallery_photo,
            compound="bottom",
            command=self.open_gallery
        )

        frame = ctk.CTkFrame(self.root, fg_color="#2A2E3F", corner_radius=8)
        frame.place(x=443, y=430)  # position only, no width/height fixed

        # === Label for filename (auto-sizes to text) ===
        label = ctk.CTkLabel(
            frame,
            text=f"{file_label}",
            justify="center",
            text_color="white",
        )
        label.pack(anchor="center")  # left-align and let it auto-size

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
