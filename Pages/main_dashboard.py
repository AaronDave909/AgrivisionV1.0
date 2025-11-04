from shared_components import SharedComponents as SC
from Pages.crop_count import show_crop_input_popup
from Pages.gallery import GalleryPage, gallery_preview
from Pages.settings import SettingsPage
from Pages.capture import CapturePage
from Pages.recents import RecentDiseaseList 
from Pages.recents import recent_disease_preview
from Pages.records import ReportViewerPage 
from Pages.analysis_page import AnalysisPage
from Pages.pest_monitor import PestMonitorPage
from Pages.weather_page import WeatherPage
from Pages.weather_page import get_latest_weather_averages 
import customtkinter as ctk
import os
from shared_components import (
    custom_font_bold, custom_font_title, custom_font_regular, 
    BUTTON_COLOR, BUTTON_HOVER
)

class MyDashboard(SC):

    # --- MODIFIED: Added is_running flag ---
    def open_gallery(self):
        self.is_running = False # Stop update loop
        self.root.destroy()
        gallery = GalleryPage()
        gallery.root.mainloop()

    # --- MODIFIED: Added is_running flag ---
    def open_settings(self):
        self.is_running = False # Stop update loop
        self.root.destroy()
        settings = SettingsPage()
        settings.root.mainloop()

    # --- MODIFIED: Added is_running flag ---
    def open_capture(self):
        self.is_running = False # Stop update loop
        self.root.destroy()
        capture_page = CapturePage()
        capture_page.root.mainloop()
    
    # --- MODIFIED: Added is_running flag ---
    def open_pest_monitor(self):
        self.is_running = False # Stop update loop
        self.root.destroy()
        monitor_page = PestMonitorPage()
        monitor_page.root.mainloop()

    # --- MODIFIED: Added is_running flag ---
    def open_report_viewer(self, folder_name, title):
        """Destroys dashboard and opens the report viewer page."""
        self.is_running = False # Stop update loop
        self.root.destroy()
        app = ReportViewerPage(folder_name=folder_name, 
                             title=title, 
                             return_page="dashboard")
        app.root.mainloop()

    # --- MODIFIED: Added is_running flag ---
    def open_analysis_view(self, image_path):
        """Destroys the dashboard and opens the analysis page in view-only mode."""
        self.is_running = False # Stop update loop
        self.root.destroy()
        app = AnalysisPage(image_path=image_path, view_only=True)
        app.root.mainloop()
    
    # --- MODIFIED: Added is_running flag ---
    def open_weather_page(self):
        """Destroys the dashboard and opens the WeatherPage."""
        self.is_running = False # Stop update loop
        self.root.destroy()
        app = WeatherPage()
        app.root.mainloop()

    # --- ADDED: New function to update weather labels ---
    def update_weather_data(self):
        """
        Fetches the latest weather data and updates the dashboard labels.
        This function will reschedule itself.
        """
        if not self.is_running:
            return # Stop the loop if we've navigated away

        # 1. Get the data using the imported function
        avg_temp, avg_hum, avg_pres = get_latest_weather_averages()

        # 2. Update the labels (checking if data is valid)
        # These labels (self.temp_label) were created in create_weather_analytics_panel
        if avg_temp is not None:
            self.temp_label.configure(text=f"{avg_temp:.1f} Â°C")
        else:
            self.temp_label.configure(text="-- Â°C")

        if avg_hum is not None:
            self.hum_label.configure(text=f"{avg_hum:.1f} %")
        else:
            self.hum_label.configure(text="-- %")

        if avg_pres is not None:
            self.pres_label.configure(text=f"{avg_pres:.1f} hPa")
        else:
            self.pres_label.configure(text="-- hPa")

        # 3. Reschedule this function to run again
        # Runs every 10 seconds (10000 milliseconds)
        self.root.after(10000, self.update_weather_data)

    def __init__(self):
        super().__init__()
        
        # --- ADDED: Flag to control the update loop ---
        self.is_running = True 
        
        self.root.update_idletasks()
        
        self.create_title()
        self.create_left_panel()
        self.create_leaf_image()
        
        def scale_x(val): return self._scale_value(val, 'x')
        def scale_y(val): return self._scale_value(val, 'y')

        self.create_record_button(x=107 / 2, y=480 / 2, command=self.open_capture)
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
            anchor="s", 
            command=lambda: show_crop_input_popup(
                self.root, 
                self.crops_button,
                scale_x_factor,
                scale_y_factor,
                scaled_title_font
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
        dynamic_text = disease_name
        btn_command = None 

        if date_str and time_str and image_path:
            dynamic_text = f"{disease_name}\n{date_str}\n{time_str}"
            btn_command = lambda path=image_path: self.open_analysis_view(path)

        btn_text = f"{dynamic_text}\n\nRecent Disease\nDetected"
        self.create_button(
            text=btn_text,
            x=270, y=75,
            width=140, height=140,
            anchor="s",
            command=btn_command
        )

        # Manage Files Button with Image
        futures_photo = self.load_futures_icon()
        self.create_button(
            text="Manage Files\n",
            x=422, y=75,
            width=140, height=140,
            anchor="s",
            command=None,
            image=futures_photo,
            compound="top"
        )
        
        # Analytics Button
        self.weather_button = self.create_weather_analytics_panel(
            x=121, y=232,
            width=205, height=220,
            anchor="n",
            command=self.open_weather_page
        )
        
        # Get Gallery Preview data
        gallery_photo, file_label = gallery_preview(self.root)

        # === UPDATED: Capture Gallery Button ===
        # Rebuilt as a composite widget to match the Weather Analytics panel layout
        # 1. Get scaled values for hover logic
        gallery_scaled_y = self._scale_value(232, 'y')
        gallery_scaled_hover_offset = self._scale_value(5, 'y')

        # 2. Create the base button (acts as a frame)
        self.gallery_button = self.create_button(
            text="", # Title will be added manually
            x=340, y=232,
            width=222, height=220,
            anchor="n",
            command=self.open_gallery,
            handle_hover=False, # Disable default hover
            hover_color=BUTTON_COLOR, # <-- FIX: Use variable
        )
        self.gallery_button.pack_propagate(False) # Prevent shrinking

        # 3. Create the Title Label
        gallery_title_label = ctk.CTkLabel(
            self.gallery_button,
            text="Capture Gallery",
            font=tuple(custom_font_bold), # Use same font as weather panel
            text_color="white",
            fg_color="transparent"
        )
        # Use the same padding as the weather panel's title to align them
        gallery_title_label.pack(pady=(self._scale_value(10, 'y'), 0))

        # 4. Create the Image Label (if an image exists)
        gallery_image_label = None
        if gallery_photo:
            gallery_image_label = ctk.CTkLabel(
                self.gallery_button,
                text="",
                image=gallery_photo,
                fg_color="transparent"
            )
            # Pack it below the title, expanding to fill space
            gallery_image_label.pack(pady=(0, self._scale_value(5, 'y')), fill="both", expand=True)
        # 5. Create the file_label frame (if file exists)
        gallery_file_frame = None
        gallery_file_label_widget = None
        if file_label not in ("Gallery Empty", "No Images"):
            gallery_file_frame = ctk.CTkFrame(
                self.gallery_button, 
                fg_color=BUTTON_COLOR, # <-- FIX: Use variable 
                corner_radius = 0
            )
            
            # --- FIX: Use .pack() instead of .place() ---
            gallery_file_frame.pack(side="bottom", pady=(0, self._scale_value(5, 'y'))) 

            gallery_file_label_widget = ctk.CTkLabel(
                gallery_file_frame,
                text=f"{file_label}",
                justify="center",
                font=tuple(custom_font_regular),
                text_color="white",
            )
            gallery_file_label_widget.pack(padx=self._scale_value(5, 'x'), pady=self._scale_value(1, 'y'))

        # 6. Define composite hover logic for the gallery button
        def on_gallery_enter(event):
            self.gallery_button.place_configure(y=gallery_scaled_y - gallery_scaled_hover_offset)
            self.gallery_button.configure(fg_color=BUTTON_HOVER)
            gallery_title_label.configure(fg_color=BUTTON_HOVER)
            if gallery_image_label:
                gallery_image_label.configure(fg_color=BUTTON_HOVER) # <-- FIX: Use variable
            if gallery_file_frame:
                gallery_file_frame.configure(fg_color=BUTTON_HOVER) # <-- FIX: Use variable

        def on_gallery_leave(event):
            self.gallery_button.place_configure(y=gallery_scaled_y)
            self.gallery_button.configure(fg_color=BUTTON_COLOR)
            gallery_title_label.configure(fg_color="transparent")
            if gallery_image_label:
                gallery_image_label.configure(fg_color="transparent")
            if gallery_file_frame:
                # Revert frame to normal color
                gallery_file_frame.configure(fg_color=BUTTON_COLOR) # <-- FIX: Use variable

        # 7. Bind all child widgets to pass clicks/hovers to the parent button
        gallery_widgets_to_bind = [self.gallery_button, gallery_title_label]
        
        if gallery_image_label:
            gallery_widgets_to_bind.append(gallery_image_label)
        if gallery_file_frame:
            gallery_widgets_to_bind.append(gallery_file_frame)
        if gallery_file_label_widget:
            gallery_widgets_to_bind.append(gallery_file_label_widget)

        for widget in gallery_widgets_to_bind:
             if widget is None: continue # Skip if a widget wasn't created
             widget.bind("<Button-1>", lambda e, cmd=self.open_gallery: cmd() if cmd else None)
             widget.bind("<Enter>", on_gallery_enter)
             widget.bind("<Leave>", on_gallery_leave)

        # --- End of Updated Section ---

        # Disease Record Panel
        disease_panel = self.create_panel(
            text="\nDisease Record History",
            x=572, y=75,
            anchor="nw",
            width=217, height=275
        )

        list_width = self._scale_value(217, 'x') - self._scale_value(10, 'x')
        list_height = self._scale_value(275, 'y') - self._scale_value(45, 'y') 
        recent_list = RecentDiseaseList(
            master=disease_panel,
            width=list_width,
            height=list_height,
            fg_color="#2A2E3F"
        )
        recent_list.pack(
            side="bottom",
            fill="both",
            expand=True,
            padx=self._scale_value(5, 'x'),
            pady=(self._scale_value(50, 'y'), self._scale_value(5, 'y'))
        )
        
        # Dock Mode Button
        self.create_button(
            text="Dock Mode",
            x=572, y=368,
            width=217, height=37,
            anchor="center",
            font=tuple(custom_font_bold),
            command=self.open_pest_monitor
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

        # --- ADDED: Start the update loop ---
        # Start the loop 1 second after the dashboard loads
        self.root.after(1000, self.update_weather_data) 

    def run(self):
        self.root.mainloop()