import os
import platform
import time
import threading
import customtkinter as ctk
import psutil

# ---> IMPORT TEXT_COLOR HERE <---
from shared_components import SharedComponents as SC, custom_font_bold, custom_font_regular, TEXT_COLOR 

BRIGHTNESS_FILE = "Page_files/brightness_state.txt"

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
            text_color=TEXT_COLOR # ---> REPLACED "white" <---
        )
        label.place(x=scale_x(123), y=scale_y(430)) 
        
        self.create_memory_usage_bar()
        self.create_brightness_slider() 
        self.load_saved_brightness()
        
        # ---> CALL THE NEW TOGGLE FUNCTION <---
        self.create_appearance_toggle()

    def create_appearance_toggle(self):
        """Creates the Light/Dark mode toggle switch."""
        # 1. Section Title
        appearance_label = ctk.CTkLabel(
            self.root, 
            text="App Appearance", 
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
        if self.mode_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.mode_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("Light")
            self.mode_switch.configure(text="Light Mode")

    def create_memory_usage_bar(self):
        disk = psutil.disk_usage('/')
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        percent_used = disk.percent

        label = ctk.CTkLabel(
            self.root, 
            text="System Storage", 
            font=tuple(custom_font_bold), 
            text_color=TEXT_COLOR # ---> REPLACED "white" <---
        )
        label.place(x=self._scale_value(123, 'x'), y=self._scale_value(128, 'y'))

        scaled_bar_width = self._scale_value(300, 'x')
        self.storage_bar = ctk.CTkProgressBar(self.root, width=scaled_bar_width, progress_color="#A9DFFF")
        self.storage_bar.place(x=self._scale_value(123, 'x'), y=self._scale_value(185, 'y'))
        self.storage_bar.set(percent_used / 100)

        usage_text = f"Used: {used_gb:.1f} GB | Free: {free_gb:.1f} GB"
        usage_label = ctk.CTkLabel(
            self.root, 
            text=usage_text, 
            font=self.scaled_12pt_font, 
            text_color=TEXT_COLOR # ---> REPLACED "white" <---
        )
        usage_label.place(x=self._scale_value(123, 'x'), y=self._scale_value(152, 'y'))

    def create_brightness_slider(self):
        brightness_label = ctk.CTkLabel(
            self.root, 
            text="Brightness", 
            font=tuple(custom_font_bold), 
            text_color=TEXT_COLOR # ---> REPLACED "white" <---
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