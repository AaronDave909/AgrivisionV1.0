from shared_components import SharedComponents as SC
from Pages.crop_count import show_crop_input_popup
from Pages.gallery import GalleryPage, gallery_preview
from Pages.settings import SettingsPage
from Pages.capture import CapturePage
from Pages.recents import RecentDiseaseList 
from PIL import Image, ImageTk
import customtkinter as ctk
import os
from shared_components import custom_font_bold, custom_font_title, custom_font_regular, ORIGINAL_WIDTH, ORIGINAL_HEIGHT

class MyDashboard(SC):

    def open_gallery(self):
        self.root.destroy()
        gallery = GalleryPage()
        gallery.root.mainloop()

    def open_settings(self):
        self.root.destroy()
        settings = SettingsPage()
        settings.root.mainloop()

    def open_capture(self):
        self.root.destroy()
        capture_page = CapturePage()
        capture_page.root.mainloop()

    def __init__(self):
        super().__init__()
        
        self.root.update_idletasks()
        
        self.create_title()
        self.create_left_panel()
        self.create_leaf_image()
        
        # --- Helper for scaled coordinates ---
        def scale_x(val): return self._scale_value(val, 'x')
        def scale_y(val): return self._scale_value(val, 'y')
        # ---

        # Record Button
        # The coordinates 107/2 and 480/2 are relative to the original 800x480 design
        self.create_record_button(x=107 / 2, y=480 / 2, command=self.open_capture)
        
        # Settings Button
        self.settings_button(command=self.open_settings)

        scale_x_factor = self.scale_x
        scale_y_factor = self.scale_y
        scaled_title_font = tuple(custom_font_title)

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
            anchor="s", # Changed anchor for vertical consistency
            command=lambda: show_crop_input_popup(
                self.root, 
                self.crops_button,
                scale_x_factor,  # Pass the x factor
                scale_y_factor,  # Pass the y factor
                scaled_title_font  # Pass the scaled font
            )
        )

        if saved_crops > 0:
            frame = ctk.CTkFrame(self.crops_button, fg_color="#2A2E3F")
            frame.place(relx=0.15, rely=0.2, anchor="nw")
            num_label = ctk.CTkLabel(
                frame,
                text=str(saved_crops),
                font=scaled_title_font, 
                text_color="white",
                fg_color="#2A2E3F"
            )
            num_label.pack()
            self.crops_button.number_frame = frame
        
        # Recent Disease Button
        self.create_button(
            text="Recent Disease\nDetected",
            x=270, y=75,
            width=140, height=140, # Added width/height for consistency
            anchor="s",
            command=None
        )

        # Manage Files Button with Image
        futures_photo = self.load_futures_icon()

        self.create_button(
            text="Manage Files\n",
            x=422, y=75,
            width=140, height=140, # Added width/height for consistency
            anchor="s",
            command=None,
            image=futures_photo,
            compound="top"
        )
        
        # Analytics Button
        self.create_button(
            text="Analytics",
            x=121, y=232,
            width=205, height=220,
            anchor="n",
            command=None
        )
        
        # Get Gallery Preview data
        gallery_photo, file_label = gallery_preview(self.root)

        # Capture Gallery Button
        self.gallery_button = self.create_button(
            text="Capture Gallery",
            x=340, y=232,
            width=222, height=220,
            anchor="n",
            image=gallery_photo,
            compound="bottom",
            command=self.open_gallery
        )
        
        # Image Filename Label (placed relative to the Gallery Button)
        if file_label not in ("Gallery Empty", "No Images"):
            frame_corner_radius = self._scale_value(8, 'x')
            file_frame = ctk.CTkFrame(self.gallery_button, fg_color="#2A2E3F", corner_radius=frame_corner_radius)
            file_frame.place(relx=0.5, rely=1.0, anchor="s")

            label = ctk.CTkLabel(
                file_frame,
                text=f"{file_label}",
                justify="center",
                font=tuple(custom_font_regular), 
                text_color="white",
            )
            # Use scaled padding
            label.pack(padx=self._scale_value(5, 'x'), pady=self._scale_value(1, 'y')) 

        # Disease Record Panel
        disease_panel = self.create_panel(
            text="\nDisease Record History",
            x=572, y=75,
            anchor="nw",
            width=217, height=275
        )

        # --- Create and add the recent disease list ---

        # Calculate scaled size, subtracting a bit for padding and the title
        list_width = self._scale_value(217, 'x') - self._scale_value(10, 'x') # 10px padding
        list_height = self._scale_value(275, 'y') - self._scale_value(45, 'y') # 45px for title and padding

        # Create an instance of our new widget
        recent_list = RecentDiseaseList(
            master=disease_panel,
            width=list_width,
            height=list_height,
            fg_color="#2A2E3F" # Match panel color
        )

        # Place the list inside the panel
        # We use pack with side="bottom" so it automatically sits *below* the title label
        recent_list.pack(
            side="bottom",
            fill="both",
            expand=True,
            padx=self._scale_value(5, 'x'),
            # Add top padding (e.g., 10px scaled) to push the list down
            pady=(self._scale_value(30, 'y'), self._scale_value(5, 'y')) # <-- This is the NEW line
        )
        
        # Dock Mode Button
        self.create_button(
            text="Dock Mode",
            x=572, y=368,
            width=217, height=37,
            anchor="center",
            font=tuple(custom_font_bold),
            command=None
        )
        
        # Diseases Button
        self.create_button(
            text="Diseases",
            x=572, y=414,
            width=217, height=37,
            anchor="center",
            font=tuple(custom_font_bold), 
            command=None
        )

        # Help Button (rounded)
        scaled_help_font_size = self._scale_value(20, 'y') 
        scaled_help_font = ("Arial", scaled_help_font_size, "bold")
        
        self.create_button(
            text="Help",
            x=674, y=21,
            width=114, height=37,
            anchor="center",
            font=scaled_help_font,
            corner_radius=50,
            command=None
        )

    def run(self):
        self.root.mainloop()