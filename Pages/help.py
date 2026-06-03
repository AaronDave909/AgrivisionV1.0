import customtkinter as ctk
from shared_components import BG_COLOR, TEXT_COLOR, SharedComponents as SC
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
import numpy as np                    
import matplotlib.colors as mcolors
from Pages.gallery import gallery_preview
from PIL import Image
import io
from language_manager import get_text, get_folder, get_image
from Pages.recents import recent_disease_preview

# --- DIALOGUE BOX CONTENT ---
class HelpSlideshowPopup(ctk.CTkToplevel):
    def __init__(self, master, title_text, folder_or_list):
        super().__init__(master)

        self.current_index = 0

        # Smart Check: Handle fixed Image Lists vs Folder Paths
        if isinstance(folder_or_list, list):
            self.image_paths = folder_or_list
        else:
            try:
                self.image_paths = sorted([
                    os.path.join(folder_or_list, file) 
                    for file in os.listdir(folder_or_list) 
                    if file.lower().endswith(('.png', '.jpg', '.jpeg'))
                ])
            except Exception as e:
                print(f"DEBUG: Error loading images from {folder_or_list}: {e}")
                self.image_paths = []

        # --- Window Setup ---
        self.overrideredirect(True) 
        self.geometry("728x420") 
        self.configure(fg_color=BG_COLOR) 
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (728 // 2)
        y = (self.winfo_screenheight() // 2) - (420 // 2)
        self.geometry(f"+{x}+{y}")

        # --- Main UI Setup ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, border_width=2, border_color=BUTTON_HOVER, fg_color=BUTTON_COLOR)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(15, 5), padx=20)

        self.title_label = ctk.CTkLabel(self.header_frame, text=title_text, text_color=TEXT_COLOR, font=("Arial", 20, "bold"))
        self.title_label.pack(side="left", expand=True)

        self.close_btn = ctk.CTkButton(
            self.header_frame, text="✕", text_color=TEXT_COLOR, width=35, height=35, corner_radius=17, 
            font=("Arial", 16, "bold"), fg_color="#FF6B6B", hover_color="#FF4C4C", 
            command=self.destroy 
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")

        self.image_label = ctk.CTkLabel(self.main_frame, text="") 
        self.image_label.pack(expand=True, pady=10)

        self.footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        self.footer_frame.pack(fill="x", side="bottom", pady=(0, 15), padx=30)

        self.prev_btn = ctk.CTkButton(self.footer_frame, text="◀", text_color=TEXT_COLOR, width=45, height=45, corner_radius=10, command=self.prev_slide)
        self.prev_btn.pack(side="left")

        self.counter_label = ctk.CTkLabel(self.footer_frame, text="1 / X", text_color=TEXT_COLOR, font=("Arial", 16, "bold"))
        self.counter_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(self.footer_frame, text="▶", text_color=TEXT_COLOR, width=45, height=45, corner_radius=10, command=self.next_slide)
        self.next_btn.pack(side="right")

        self.update_display()

    def update_display(self):
        total_slides = len(self.image_paths)
        if total_slides == 0:
            self.counter_label.configure(text="0 / 0")
            self.image_label.configure(text="No images found", image="")
            return

        self.counter_label.configure(text=f"{self.current_index + 1} / {total_slides}")
        current_image_path = self.image_paths[self.current_index]
        
        with open(current_image_path, "rb") as f:
            img_data = Image.open(io.BytesIO(f.read()))
        
        ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(512, 288)) 
        self.image_label.configure(image=ctk_img)

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


# --- HELP PAGE ---
class HelpPage(SC):
    def __init__(self, current_language="English"):
        super().__init__()
        # 1. CRITICAL: Store the language passed from the Dashboard!
        self.current_language = current_language 
        
        self.root.update_idletasks()
        self.create_title(text=get_text("title_help"), x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        
        self.scale_x_val = lambda val: self._scale_value(val, 'x')
        self.scale_y_val = lambda val: self._scale_value(val, 'y')

        # 2. Help Indicator Badge
        scaled_badge_font = ("Arial", self._scale_value(16, 'y'), "bold")
        self.create_button(
            text=get_text("notice_help"), 
            x=250, y=20, width=220, height=35, anchor="center",
            font=scaled_badge_font, corner_radius=20, fg_color="#FF6B6B", 
            hover_color="#FF6B6B", command=None          
        )

        # 3. BUTTONS (CLEANED: We no longer scan folders here)
        # Capture Button
        self.create_record_button(
            x=107 / 2, y=480 / 2, 
            command=lambda: HelpSlideshowPopup(None, get_text("title_capture_guide"), get_folder("_image_assets/capture"))
        )

        # Settings Button
        self.settings_button(
            command=lambda: HelpSlideshowPopup(None, get_text("title_setting_guide"), get_folder("_image_assets/settings"))
        ) 

        # Return Button
        self.create_button(
            text="✕", x=735, y=21, width=40, height=40, anchor="center",
            font=("Arial", self._scale_value(22, 'y'), "bold"), 
            corner_radius=20, command=self.go_back_to_dashboard
        )
                
        # Crop Monitor Button
        icon_for_dark = Image.open("_image_assets/crop_inside.png")
        icon_for_light = Image.open("_image_assets/crop_inside_light.png").resize(icon_for_dark.size)
        monitor_photo = ctk.CTkImage(light_image=icon_for_light, dark_image=icon_for_dark, size=(150, 100))

        self.crops_button = self.create_button(
            text=f"{get_text('lbl_crops_monitor')}\n", x=118, y=75, width=140, height=140, anchor="s", 
            command=lambda: HelpSlideshowPopup(None, get_text("title_monitor_guide"), get_folder("_image_assets/crops in monitor")), 
            image=monitor_photo
        )

        # Recent Disease Button (Fixed List)
        disease_name, date_str, time_str, image_path = recent_disease_preview()

        # --- THE UPDATED SANITIZER ---
        # We check for keywords in the raw disease_name to assign a consistent KEY
        raw_lower = disease_name.lower()
        
        if "nitrogen" in raw_lower or "n deficiency" in raw_lower:
            disease_key = "status_n_def"
        elif "phosphorus" in raw_lower or "p deficiency" in raw_lower:
            disease_key = "status_p_def"
        elif "potassium" in raw_lower or "k deficiency" in raw_lower:
            disease_key = "status_k_def"
        elif "no disease" in raw_lower:
            disease_key = "status_no_disease"
        else:
            # For specific diseases like Powdery Mildew, we use the standard sanitizer
            clean_name = "_".join(raw_lower.split())
            disease_key = f"status_{clean_name}"
        
        # Now get the translation (will return Tagalog if active, English if not)
        translated_disease = get_text(disease_key)
        # ---------------------------------

        dynamic_text = translated_disease
        btn_command = None 

        if date_str and time_str and image_path:
            # Use the translated disease
            dynamic_text = f"{translated_disease}\n{date_str}\n{time_str}"
            btn_command = lambda path=image_path: self.open_analysis_view(path)

        # Inject the translated label at the bottom (Huling Sakit na Natukoy)
        btn_text = f"{dynamic_text}\n\n{get_text('lbl_recent_disease')}\n"
        self.create_button(
            text=btn_text,
            x=270, y=75,
            width=140, height=140,
            anchor="s",
            command=btn_command
        )
        
        self.create_button(
            text=btn_text, x=270, y=75, width=140, height=140, anchor="s",
            command=lambda: HelpSlideshowPopup(None, get_text("title_recent_disease_guide"), [get_image("_image_assets/recent.png")]),
        )

        # Generate Report Button
        self.create_button(
            text = f"{get_text('btn_generate_report')}\n", x=422, y=75, width=140, height=140, anchor="s",
            command=lambda: HelpSlideshowPopup(None, get_text("title_report_guide"), get_folder("_image_assets/report")), 
            image=self.load_futures_icon(), compound="top"
        )        

        # Weather Analytics Button
        icon_weather_dark = Image.open("_image_assets/weather_inside.png") 
        icon_weather_light = Image.open("_image_assets/weather_inside_light.png").resize(icon_weather_dark.size)
        weather_photo = ctk.CTkImage(light_image=icon_weather_light, dark_image=icon_weather_dark, size=(200, 200))
        
        self.weather_button = self.create_button(
            text=f"\n{get_text('lbl_analytics')}", x=121, y=232, width=205, height=220, anchor="n",
            command=lambda: HelpSlideshowPopup(None, get_text("title_analytics_guide"), get_folder("_image_assets/analytics")),
            image=weather_photo, compound="bottom"
        )

        # Capture Gallery Button
        icon_gallery_dark = Image.open("_image_assets/gallery_inside.png") 
        icon_gallery_light = Image.open("_image_assets/gallery_inside_light.png").resize(icon_gallery_dark.size)
        gallery_photo = ctk.CTkImage(light_image=icon_gallery_light, dark_image=icon_gallery_dark, size=(200, 200))
        
        self.gallery_button = self.create_button(
            text=f"\n{get_text('lbl_capture_gallery')}", x=340, y=232, width=222, height=220, anchor="n",
            command=lambda: HelpSlideshowPopup(None, get_text("title_gallery_guide"), get_folder("_image_assets/gallery")),
            image=gallery_photo, compound="bottom"
        )
        
        # Disease Record History (Fixed List)
        icon_hist_dark = Image.open("_image_assets/history_image.png")
        icon_hist_light = Image.open("_image_assets/history_image_light.png").resize(icon_hist_dark.size)
        history_photo = ctk.CTkImage(light_image=icon_hist_light, dark_image=icon_hist_dark, size=(210, 260))

        self.create_button(
            text = f"\n{get_text('lbl_disease_history')}", x=572, y=75, anchor="n", width=217, height=275,
            command=lambda: HelpSlideshowPopup(None, get_text("title_history_guide"), [get_image("_image_assets/history.png")]), 
            image=history_photo, compound="bottom"
        )

        # Bottom Row Buttons
        self.create_button(
            text="Dock Mode", x=572, y=368, width=217, height=37, anchor="center", font=tuple(custom_font_bold),
            command=lambda: HelpSlideshowPopup(None, get_text("title_dock_guide"), get_folder("_image_assets/dock")), 
        )
        
        self.create_button(
            text=get_text("btn_risk_check"), x=572, y=414, width=217, height=37, anchor="center", font=tuple(custom_font_bold), 
            command=lambda: HelpSlideshowPopup(None, get_text("title_risk_guide"), get_folder("_image_assets/risk")),
        )