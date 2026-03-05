import customtkinter as ctk
from shared_components import SharedComponents as SC
import datetime
import os
from shared_components import (
    custom_font_bold, custom_font_title, custom_font_regular, 
    BUTTON_COLOR, BUTTON_HOVER
)
import matplotlib.dates as mdates
from collections import deque
import matplotlib.ticker as ticker
import pandas as pd
import numpy as np                    # For creating the gradient
import matplotlib.colors as mcolors
from Pages.gallery import gallery_preview
from PIL import Image
import io

#DIALOGUE BOX CONTENT
class HelpSlideshowPopup(ctk.CTkToplevel):
    def __init__(self, master, title_text, image_paths):
        super().__init__(master)

        self.image_paths = image_paths
        self.current_index = 0

        # --- Window Setup ---
        # Removes the default OS window bar for a clean, app-like modal
        self.overrideredirect(True) 
        self.geometry("1300x750") # Adjust overall size to fit your screen
        self.configure(fg_color="#1E2235") # Matches your dark theme
        
        # Center the pop-up on the screen (Optional, but looks premium)
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1300 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"+{x}+{y}")

        # --- Main Container Frame (For rounded borders) ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, border_width=2, border_color="#3A3E55", fg_color="#2A2E3F")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Header Section ---
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(15, 5), padx=20)

        # Title Label
        self.title_label = ctk.CTkLabel(self.header_frame, text=title_text, font=("Arial", 20, "bold"))
        self.title_label.pack(side="left", expand=True)

        # Exit Button (Top Right)
        self.close_btn = ctk.CTkButton(
            self.header_frame, text="✕", width=35, height=35, corner_radius=17, 
            font=("Arial", 16, "bold"), fg_color="#FF6B6B", hover_color="#FF4C4C", 
            command=self.destroy # Closes the pop-up completely
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")

        # --- Image Display Section ---
        self.image_label = ctk.CTkLabel(self.main_frame, text="") # Text is blank, it holds the image
        self.image_label.pack(expand=True, pady=10)

        # --- Footer Section (Controls) ---
        self.footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        self.footer_frame.pack(fill="x", side="bottom", pady=(0, 15), padx=30)

        # Previous Button (◀)
        self.prev_btn = ctk.CTkButton(self.footer_frame, text="◀", width=45, height=45, corner_radius=10, command=self.prev_slide)
        self.prev_btn.pack(side="left")

        # Slide Counter (e.g., "1 / 3")
        self.counter_label = ctk.CTkLabel(self.footer_frame, text="1 / X", font=("Arial", 16, "bold"))
        self.counter_label.pack(side="left", expand=True)

        # Next Button (▶)
        self.next_btn = ctk.CTkButton(self.footer_frame, text="▶", width=45, height=45, corner_radius=10, command=self.next_slide)
        self.next_btn.pack(side="right")

        # Load the very first slide upon opening
        self.update_display()

    # --- Slideshow Logic ---
    def update_display(self):
        # 1. Update the counter text
        total_slides = len(self.image_paths)
        self.counter_label.configure(text=f"{self.current_index + 1} / {total_slides}")

        # 2. Load and set the image
        current_image_path = self.image_paths[self.current_index]
        with open(current_image_path, "rb") as f:
            img_data = Image.open(io.BytesIO(f.read()))
        # Adjust size=(width, height) to fit nicely in your modal
        ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(1010, 600)) 
        self.image_label.configure(image=ctk_img)

        # 3. Disable/Enable buttons if at the start or end of the slideshow
        self.prev_btn.configure(state="normal" if self.current_index > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_index < total_slides - 1 else "disabled")

    def next_slide(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.update_display()

    def prev_slide(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()

#BUTTONS  
class HelpPage(SC):
    def __init__(self):
        super().__init__()
        self.root.update_idletasks()
        self.create_title(text="Help", x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        
        self.scale_x_val = lambda val: self._scale_value(val, 'x')
        self.scale_y_val = lambda val: self._scale_value(val, 'y')

        #Help Page Description
        scaled_badge_font_size = self._scale_value(16, 'y') 
        scaled_badge_font = ("Arial", scaled_badge_font_size, "bold")

        self.create_button(
            text="Help Mode is Active", # Using the Unicode lightbulb icon
            x=250, y=20,  # IMPORTANT: Adjust the 'x' value so it sits perfectly right of your "Help" title
            width=220, height=35,
            anchor="center",
            font=scaled_badge_font,
            corner_radius=20,     # High radius gives it that "pill" shape
            fg_color="#FF6B6B",   # A soft, modern light red/coral color
            hover_color="#FF6B6B", # Matches fg_color so it doesn't flash if a user taps it
            command=None          # It acts purely as a visual indicator
        )

        #Capture Button 
        capture_folder = "_image_assets/capture"
        capture_folder = sorted([
            os.path.join(capture_folder, file) 
            for file in os.listdir(capture_folder) 
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        self.create_record_button(x=107 / 2, y=480 / 2, command=lambda: HelpSlideshowPopup(None, "Capture Button Guide", capture_folder))
        

        #Setting Button
        setting_folder = "_image_assets/settings"
        setting_folder = sorted([
            os.path.join(setting_folder, file) 
            for file in os.listdir(setting_folder) 
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        self.settings_button(command=lambda: HelpSlideshowPopup(None, "Setting Guide", setting_folder)) 

        #Return/Close Button
        scaled_close_font_size = self._scale_value(22, 'y') 
        scaled_close_font = ("Arial", scaled_close_font_size, "bold")

        self.create_button(
            text="✕",  # Using a clean Unicode cross instead of a standard keyboard 'X'
            x=735, y=21,  # Shifted right so it aligns with where the old wide button ended
            width=40, height=40,  # Equal width and height for a perfect square footprint
            anchor="center",
            font=scaled_close_font,
            corner_radius=20,  # Setting this to half the width/height makes it a perfect circle
            command=self.go_back_to_dashboard
        )
                
        #Crop Monitor Button
        monitor_folder = "_image_assets/crops in monitor"
        monitor_folder = sorted([
            os.path.join(monitor_folder, file) 
            for file in os.listdir(monitor_folder) 
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        crops_file = os.path.join("Page_files", "crops_monitored.txt")
        if os.path.exists(crops_file):
            try:
                with open(crops_file, "r") as f:
                    saved_crops = int(f.read().strip())
            except ValueError:
                saved_crops = 0
        else:
            saved_crops = 0
        self.crops_button = self.create_button(
            text="Crops in Monitor\n",
            x=118, y=75,
            width=140, height=140,
            anchor="s", 
            command=lambda: HelpSlideshowPopup(None, "Crop Monitor Guide", monitor_folder), 
            )
        
        #Recent Diseases Button
        recent_images = ["_image_assets/Recent Diseases.png"] 

        btn_text = "Recent Disease Detected"
        self.create_button(
            text=btn_text,
            x=270, y=75,
            width=140, height=140,
            anchor="s",
            # 2. Pass that single-item list directly into your popup
            command=lambda: HelpSlideshowPopup(None, "Recent Disease Detected Guide", recent_images) 
        )

        #Manage Files Button
        futures_photo = self.load_futures_icon()
        self.create_button(
            text="Manage Files\n",
            x=422, y=75,
            width=140, height=140,
            anchor="s",
            command=lambda: HelpSlideshowPopup(None, "Manage Files Guide", weather_folder), #to change
            image=futures_photo,
            compound="top"
        )        

        #Weather Analytics Button
        weather_folder = "_image_assets/weather"
        weather_folder = sorted([
            os.path.join(weather_folder, file) 
            for file in os.listdir(weather_folder) 
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        self.weather_button = self.create_weather_analytics_panel(
                x=121, y=232,
                width=205, height=220,
                anchor="n",
                command=lambda: HelpSlideshowPopup(None, "Weather Analytics Guide", weather_folder)
            )

        #Capture Gallery Button
        gallery_folder = "_image_assets/gallery"
        gallery_folder = sorted([
            os.path.join(gallery_folder, file) 
            for file in os.listdir(gallery_folder) 
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        gallery_photo, file_label = gallery_preview(self.root)

        gallery_scaled_y = self._scale_value(232, 'y')
        gallery_scaled_hover_offset = self._scale_value(5, 'y')

        self.gallery_button = self.create_button(
            text="", 
            x=340, y=232,
            width=222, height=220,
            anchor="n",
            command=lambda: HelpSlideshowPopup(None, "Capture Gallery Guide", gallery_folder), #to change
            handle_hover=False, # Disable default hover
            hover_color=BUTTON_COLOR, # <-- FIX: Use variable
        )
        self.gallery_button.pack_propagate(False) # Prevent shrinking

        gallery_title_label = ctk.CTkLabel(
            self.gallery_button,
            text="Capture Gallery",
            font=tuple(custom_font_bold), # Use same font as weather panel
            text_color="white",
            fg_color="transparent"
        )
        gallery_title_label.pack(pady=(self._scale_value(10, 'y'), 0))

        gallery_image_label = None
        if gallery_photo:
            gallery_image_label = ctk.CTkLabel(
                self.gallery_button,
                text="",
                image=gallery_photo,
                fg_color="transparent"
            )
            gallery_image_label.pack(pady=(0, self._scale_value(5, 'y')), fill="both", expand=True)
       
        gallery_file_frame = None
        gallery_file_label_widget = None
        if file_label not in ("Gallery Empty", "No Images"):
            gallery_file_frame = ctk.CTkFrame(
                self.gallery_button, 
                fg_color=BUTTON_COLOR, # <-- FIX: Use variable 
                corner_radius = 0
            )
            
            gallery_file_frame.pack(side="bottom", pady=(0, self._scale_value(5, 'y'))) 

            gallery_file_label_widget = ctk.CTkLabel(
                gallery_file_frame,
                text=f"{file_label}",
                justify="center",
                font=tuple(custom_font_regular),
                text_color="white",
            )
            gallery_file_label_widget.pack(padx=self._scale_value(5, 'x'), pady=self._scale_value(1, 'y'))
        
        # Disease Record Panel
        disease_panel = self.create_button(
            text="\nDisease Record History",
            x=572, y=75,
            anchor="nw",
            width=217, height=275,
            command=lambda: HelpSlideshowPopup(None, "Disease Record History Guide", weather_folder), 
        )

        #Dock Mode Button
        dock_folder = "_image_assets/dock"
        dock_folder = sorted([
            os.path.join(dock_folder, file) 
            for file in os.listdir(dock_folder) 
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        self.create_button(
                    text="Dock Mode",
                    x=572, y=368,
                    width=217, height=37,
                    anchor="center",
                    font=tuple(custom_font_bold),
                    command=lambda: HelpSlideshowPopup(None, "Dock Mode Button Guide", dock_folder), 
                )
        
        #Risk Check Button
        risk_folder = "_image_assets/risk"
        risk_folder = sorted([
            os.path.join(risk_folder, file) 
            for file in os.listdir(risk_folder) 
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        self.create_button(
            text="Risk Check", 
            x=572, y=414,
            width=217, height=37,
            anchor="center",
            font=tuple(custom_font_bold), 
            command=lambda: HelpSlideshowPopup(None, "Risk Check Guide", risk_folder), #to change
        )
