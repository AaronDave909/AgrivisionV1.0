import os
import platform
import time
import threading
import customtkinter as ctk
import psutil
from language_manager import get_text, i18n
import json # Used to save the language safely

# ---> IMPORT TEXT_COLOR HERE <---
from shared_components import SharedComponents as SC, custom_font_bold, custom_font_regular, TEXT_COLOR 

BRIGHTNESS_FILE = "Page_files/brightness_state.txt"
THEME_FILE = "Page_files/theme_state.txt" # --- NEW: File to store theme state ---
LANG_FILE = "Page_files/lang_state.txt"

class SettingsPage(SC):
    
    def __init__(self):
        super().__init__()
        
        # Define helper functions for cleaner scaling calls
        def scale_x(val): return self._scale_value(val, 'x')
        def scale_y(val): return self._scale_value(val, 'y')
        
        self.create_title(text="Settings", x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        self.undo_button(command=self.go_back_to_dashboard)
        
        scaled_12pt_size = self._scale_value(12, 'y')
        self.scaled_12pt_font = ("Arial", scaled_12pt_size)

        # Version Label
        label = ctk.CTkLabel(
            self.root, 
            text="Agrivision v1.0", 
            font=self.scaled_12pt_font, 
            text_color=TEXT_COLOR 
        )
        label.place(x=scale_x(123), y=scale_y(430)) 
        
        self.create_memory_usage_bar()
        self.create_brightness_slider() 
        self.load_saved_brightness()
        
        self.create_appearance_toggle()
        self.create_language_toggle() # <--- NEW: Call the function

    def create_appearance_toggle(self):
        """Creates the Light/Dark mode toggle switch."""
        # 1. Section Title
        appearance_label = ctk.CTkLabel(
            self.root, 
            text=get_text("lbl_app_appearance"), 
            font=tuple(custom_font_bold), 
            text_color=TEXT_COLOR 
        )
        appearance_label.place(x=self._scale_value(123, 'x'), y=self._scale_value(230, 'y'))

        # 2. The Switch Widget
        self.mode_switch = ctk.CTkSwitch(
            self.root,
            text="Dark Mode" if ctk.get_appearance_mode() == "Dark" else "Light Mode",
            font=self.scaled_12pt_font,
            text_color=TEXT_COLOR,
            progress_color="#FF6B6B", # Turns soft red when active!
            command=self.toggle_appearance
        )
        self.mode_switch.place(x=self._scale_value(123, 'x'), y=self._scale_value(265, 'y'))

        # 3. Set initial switch position based on current mode
        if ctk.get_appearance_mode() == "Dark":
            self.mode_switch.select()
        else:
            self.mode_switch.deselect()

    def toggle_appearance(self):
        """Flipped when the user clicks the switch."""
        
        # 1. Change the internal CTk mode and SAVE it
        if self.mode_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.mode_switch.configure(text="Dark Mode")
            self.save_theme("Dark") # --- NEW: Save choice ---
        else:
            ctk.set_appearance_mode("Light")
            self.mode_switch.configure(text="Light Mode")
            self.save_theme("Light") # --- NEW: Save choice ---
            
        # 2. Force the UI to refresh by reloading the dashboard
        print(f"Theme switched to {ctk.get_appearance_mode()}. Reloading UI...")
        
        # Give the switch a tiny moment to finish its animation
        self.root.after(150, self.force_ui_reload)

    def create_language_toggle(self):
        """Creates the side-by-side Tagalog and English toggle buttons."""
        
        # 1. Section Title
        lang_label = ctk.CTkLabel(
            self.root, 
            text=get_text("lbl_lang"), # A nice bilingual title!
            font=tuple(custom_font_bold), 
            text_color=TEXT_COLOR 
        )
        lang_label.place(x=self._scale_value(123, 'x'), y=self._scale_value(320, 'y')) # Placed just below Appearance

        # 2. Define Colors (Matches your Image)
        # Using magic tuples so they adapt slightly if you switch dark/light mode
        ACTIVE_COLOR = ("#2CC9F5", "#1CA3C6") 
        INACTIVE_COLOR = ("gray60", "gray40") 
        TEXT_COLOR_BTN = ("white", "white")

        # 3. Create the Buttons side-by-side
        # Place English on the LEFT (Default)
        self.btn_english = ctk.CTkButton(
            self.root,
            text="English",
            font=("Arial", self._scale_value(18, 'y'), "bold"),
            text_color=TEXT_COLOR_BTN,
            width=self._scale_value(140, 'x'),
            height=self._scale_value(40, 'y'),
            corner_radius=8,
            fg_color=ACTIVE_COLOR if i18n.current_lang == "en" else INACTIVE_COLOR,
            command=lambda: self.change_language("en")
        )
        self.btn_english.place(x=self._scale_value(123, 'x'), y=self._scale_value(355, 'y'))

        # Place Tagalog on the RIGHT
        self.btn_tagalog = ctk.CTkButton(
            self.root,
            text="Tagalog",
            font=("Arial", self._scale_value(18, 'y'), "bold"),
            text_color=TEXT_COLOR_BTN,
            width=self._scale_value(140, 'x'),
            height=self._scale_value(40, 'y'),
            corner_radius=8,
            fg_color=ACTIVE_COLOR if i18n.current_lang == "tl" else INACTIVE_COLOR,
            command=lambda: self.change_language("tl")
        )
        # (123 + 140 width + 10 padding = 273)
        self.btn_tagalog.place(x=self._scale_value(273, 'x'), y=self._scale_value(355, 'y'))

    def change_language(self, lang_code):
        """Swaps dictionaries, updates colors, and saves the choice."""
        # 1. Tell the engine to swap
        i18n.set_language(lang_code)

        # 2. Update Button Colors (The "Seesaw")
        ACTIVE_COLOR = ("#2CC9F5", "#1CA3C6") 
        INACTIVE_COLOR = ("gray60", "gray40") 

        if lang_code == "tl":
            self.btn_tagalog.configure(fg_color=ACTIVE_COLOR)
            self.btn_english.configure(fg_color=INACTIVE_COLOR)
        else:
            self.btn_tagalog.configure(fg_color=INACTIVE_COLOR)
            self.btn_english.configure(fg_color=ACTIVE_COLOR)
        
        # 3. Save the choice to file
        os.makedirs(os.path.dirname(LANG_FILE), exist_ok=True)
        try:
            with open(LANG_FILE, "w") as f:
                f.write(lang_code)
        except Exception as e:
            print(f"Error saving language: {e}")
            
        print(f"Language switched to {lang_code}.")

    # --- NEW: Save theme function ---
    def save_theme(self, mode):
        """Writes the selected theme to a text file so it survives reboots."""
        os.makedirs(os.path.dirname(THEME_FILE), exist_ok=True)
        try:
            with open(THEME_FILE, "w") as f:
                f.write(mode)
        except Exception as e:
            print(f"Error saving theme: {e}")
    # --------------------------------

    def force_ui_reload(self):
        """Destroys the current window and reloads the Dashboard to apply new colors."""
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.root.mainloop()

    def create_memory_usage_bar(self):
        disk = psutil.disk_usage('/')
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        percent_used = disk.percent

        label = ctk.CTkLabel(
            self.root, 
            text=get_text("lbl_system_storage"), 
            font=tuple(custom_font_bold), 
            text_color=TEXT_COLOR 
        )
        label.place(x=self._scale_value(123, 'x'), y=self._scale_value(128, 'y'))

        scaled_bar_width = self._scale_value(300, 'x')
        self.storage_bar = ctk.CTkProgressBar(self.root, width=scaled_bar_width, progress_color="#A9DFFF")
        self.storage_bar.place(x=self._scale_value(123, 'x'), y=self._scale_value(185, 'y'))
        self.storage_bar.set(percent_used / 100)

        usage_text = f"{i18n.get_text('lbl_used')}: {used_gb:.1f} GB | {i18n.get_text('lbl_free')}: {free_gb:.1f} GB"
        
        usage_label = ctk.CTkLabel(
            self.root, 
            text=usage_text, 
            font=self.scaled_12pt_font, 
            text_color=TEXT_COLOR 
        )
        usage_label.place(x=self._scale_value(123, 'x'), y=self._scale_value(152, 'y'))

    def create_brightness_slider(self):
        brightness_label = ctk.CTkLabel(
            self.root, 
            text="Brightness", 
            font=tuple(custom_font_bold), 
            text_color=TEXT_COLOR 
        )
        brightness_label.place(x=self._scale_value(123, 'x'), y=self._scale_value(66, 'y'))

        scaled_slider_width = self._scale_value(300, 'x')
        self.brightness_slider = ctk.CTkSlider(
            self.root,
            width=scaled_slider_width,
            from_=0,
            to=100,
            command=self.set_brightness,
            button_color="#A9DFFF", 
            button_hover_color="#89BFEF",
            progress_color="#A9DFFF"
        )
        self.brightness_slider.place(x=self._scale_value(123, 'x'), y=self._scale_value(105, 'y'))

    def load_saved_brightness(self):
        if os.path.exists(BRIGHTNESS_FILE):
            try:
                with open(BRIGHTNESS_FILE, "r") as f:
                    value = float(f.read().strip())
            except:
                value = 50.0  
        else:
            value = 50.0  

        self.brightness_slider.set(value)
        self.apply_brightness(value)

    def set_brightness(self, value):
        self.save_brightness(value)
        self.apply_brightness(value)

    def save_brightness(self, value):
        os.makedirs(os.path.dirname(BRIGHTNESS_FILE), exist_ok=True)
        with open(BRIGHTNESS_FILE, "w") as f:
            f.write(str(value))

    def apply_brightness(self, target_value):
        def fade():
            system = platform.system()
            if system == "Linux" and os.path.exists("/sys/class/backlight/rpi_backlight/brightness"):
                try:
                    with open("/sys/class/backlight/rpi_backlight/brightness", "r") as f:
                        current = int(f.read().strip()) / 2.55  
                except:
                    current = target_value
            else:
                current = getattr(self, "_virtual_brightness", target_value)

            step = 1 if target_value > current else -1

            for level in range(int(current), int(target_value), step):
                hardware_value = int(level * 2.55)

                if system == "Linux" and os.path.exists("/sys/class/backlight/rpi_backlight/brightness"):
                    try:
                        with open("/sys/class/backlight/rpi_backlight/brightness", "w") as f:
                            f.write(str(hardware_value))
                        time.sleep(0.01)  
                    except PermissionError:
                        print("Permission denied: run with sudo")
                        break
                else:
                    self._virtual_brightness = level  
                    time.sleep(0.01)  

        threading.Thread(target=fade, daemon=True).start()