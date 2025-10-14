from shared_components import SharedComponents as SC
from Pages.crop_count import show_crop_input_popup
from Pages.gallery import GalleryPage, gallery_preview
from Pages.settings import SettingsPage
from PIL import Image, ImageTk
import customtkinter as ctk
import os

# Import scaled font and original size for reference
from shared_components import custom_font_bold, custom_font_title, ORIGINAL_WIDTH, ORIGINAL_HEIGHT

class MyDashboard(SC):

    def open_gallery(self):
        self.root.destroy()
        gallery = GalleryPage()
        gallery.root.mainloop()

    def open_settings(self):
        self.root.destroy()
        settings = SettingsPage()
        settings.root.mainloop()

    def __init__(self):
        super().__init__()
        self.create_title()
        self.create_left_panel()
        self.create_leaf_image()
        
        # --- Helper for scaled coordinates ---
        # Note: You can use self._scale_value directly, but these helpers keep the lines clean.
        def scale_x(val): return self._scale_value(val, 'x')
        def scale_y(val): return self._scale_value(val, 'y')
        # ---

        # Record Button
        # The coordinates 107/2 and 480/2 are relative to the original 800x480 design
        self.create_record_button(x=107 / 2, y=480 / 2, command=None)
        
        # Settings Button
        self.settings_button(command=self.open_settings)

        scale_x_factor = self.scale_x
        scale_y_factor = self.scale_y
        scaled_title_font = tuple(SC.custom_font_title)

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
            # --- UPDATED COMMAND CALL ---
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

        # === FIX 2: Scale the frame position and corner radius ===
        frame_corner_radius = self._scale_value(8, 'x')
        frame = ctk.CTkFrame(self.root, fg_color="#2A2E3F", corner_radius=frame_corner_radius)
        frame.place(x=scale_x(443), y=scale_y(430))

        # === FIX 3: Scale the label's font ===
        label = ctk.CTkLabel(
            frame,
            text=f"{file_label}",
            justify="center",
            # Use the SCALED global font (converted to tuple)
            font=tuple(SC.custom_font_regular), # Assuming SC uses custom_font_regular
            text_color="white",
        )
        label.pack(anchor="center")

        # Disease Record Panel
        self.create_panel(
            text="\nDisease Record History",
            x=572, y=75,
            anchor="nw",
            width=217, height=275
        )
        
        # Dock Mode Button
        # === FIX 4: Use scaled custom_font_bold for consistency ===
        self.create_button(
            text="Dock Mode",
            x=572, y=368,
            width=217, height=37,
            anchor="center",
            font=tuple(custom_font_bold), # Use scaled font
            command=None
        )
        
        # Diseases Button
        # === FIX 5: Use scaled custom_font_bold for consistency ===
        self.create_button(
            text="Diseases",
            x=572, y=424,
            width=217, height=37,
            anchor="center",
            font=tuple(custom_font_bold), # Use scaled font
            command=None
        )

        # Help Button (rounded)
        # === FIX 6: Use scaled font (or manually scale the size if necessary) ===
        # Here we manually scale the font size, using the general scale factor for robustness.
        # It's better to use a dedicated scaled variable from SC if available. 
        # Since we only have custom_font_bold, we'll manually scale the 20pt size.
        scaled_help_font_size = self._scale_value(20, 'y') 
        scaled_help_font = ("Arial", scaled_help_font_size, "bold")
        
        self.create_button(
            text="Help",
            x=674, y=21,
            width=114, height=37,
            anchor="center",
            font=scaled_help_font, # Use the manually scaled font tuple
            corner_radius=50,
            command=None
        )

    def run(self):
        """Runs the main loop for the dashboard."""
        self.root.mainloop()