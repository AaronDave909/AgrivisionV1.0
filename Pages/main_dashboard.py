from shared_components import SharedComponents as SC
from Pages.crop_count import show_crop_input_popup
from Pages.gallery import GalleryPage, gallery_preview
from Pages.settings import SettingsPage
from Pages.capture import CapturePage
from Pages.recents import RecentDiseaseList 
from Pages.recents import recent_disease_preview
from Pages.records import ReportViewerPage 
from Pages.analysis_page import AnalysisPage
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

    def open_report_viewer(self, folder_name, title):
        """Destroys dashboard and opens the report viewer page."""
        self.root.destroy()
        # Pass the folder, title, and what page to return to
        app = ReportViewerPage(folder_name=folder_name, 
                             title=title, 
                             return_page="dashboard")
        app.root.mainloop()

    def open_analysis_view(self, image_path):
        """Destroys the dashboard and opens the analysis page in view-only mode."""
        self.root.destroy()
        # Pass the path to the image and set view_only=True
        app = AnalysisPage(image_path=image_path, view_only=True)
        app.root.mainloop()

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
        disease_name, date_str, time_str, image_path = recent_disease_preview()

        dynamic_text = disease_name # Default text if no data

        # Check if we got valid date, time, and path
        if date_str and time_str and image_path:
            # 2. Format the data for the button using separate date and time
            dynamic_text = f"{disease_name}\n{date_str}\n{time_str}" # <-- FORMAT CHANGE HERE

            # 3. Set the command
            btn_command = lambda path=image_path: self.open_analysis_view(path)

        # 4. Combine dynamic text with the constant footer
        # Adjusted newlines for better spacing with the new 3-line format
        btn_text = f"{dynamic_text}\n\nRecent Disease\nDetected"

        # 5. Create the button with the new text and command
        self.create_button(
            text=btn_text,
            x=270, y=75,
            width=140, height=140,
            anchor="s",
            command=btn_command # Set the command here
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
            pady=(self._scale_value(50, 'y'), self._scale_value(5, 'y')) # <-- This is the NEW line
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
            command=lambda: self.open_report_viewer("_diseases_", "Diseases") 
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