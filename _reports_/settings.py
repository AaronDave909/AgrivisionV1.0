import os
import platform
import time
import threading
import customtkinter as ctk
import psutil
from shared_components import SharedComponents as SC, custom_font_bold, custom_font_regular # Import scaled fonts

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
        self.create_battery_indicator(x=15, y=100)
        self.undo_button(command=self.go_back_to_dashboard)
        
        # Define a scaled font for smaller text (12pt original)
        # We reuse the scaling factor from SC to ensure consistency
        scaled_12pt_size = self._scale_value(12, 'y')
        self.scaled_12pt_font = ("Arial", scaled_12pt_size)

        # Place version label using scaled coordinates and font
        label = ctk.CTkLabel(
            self.root, 
            text="Agrivision v1.0", 
            font=self.scaled_12pt_font, # Use scaled font
            text_color="white"
        )
        label.place(x=scale_x(123), y=scale_y(430)) # Use scaled position
        
        self.create_memory_usage_bar()
        self.create_brightness_slider() 
        self.load_saved_brightness()

    def create_memory_usage_bar(self):
        disk = psutil.disk_usage('/')
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        percent_used = disk.percent

        # Scale position and use scaled font
        label = ctk.CTkLabel(
            self.root, 
            text="System Storage", 
            font=tuple(custom_font_bold), # Use imported scaled font
            text_color="white"
        )
        label.place(x=self._scale_value(123, 'x'), y=self._scale_value(128, 'y'))

        # Scale width and position of progress bar
        scaled_bar_width = self._scale_value(300, 'x')
        self.storage_bar = ctk.CTkProgressBar(self.root, width=scaled_bar_width, progress_color="white")
        self.storage_bar.place(x=self._scale_value(123, 'x'), y=self._scale_value(185, 'y'))
        self.storage_bar.set(percent_used / 100)

        # Scale position and font of usage text
        usage_text = f"Used: {used_gb:.1f} GB | Free: {free_gb:.1f} GB"
        usage_label = ctk.CTkLabel(
            self.root, 
            text=usage_text, 
            font=self.scaled_12pt_font, # Use scaled 12pt font
            text_color="white"
        )
        usage_label.place(x=self._scale_value(123, 'x'), y=self._scale_value(152, 'y'))

    def create_brightness_slider(self):
        # Scale position and use scaled font
        brightness_label = ctk.CTkLabel(
            self.root, 
            text="Brightness", 
            font=tuple(custom_font_bold), # Use imported scaled font
            text_color="white"
        )
        brightness_label.place(x=self._scale_value(123, 'x'), y=self._scale_value(66, 'y'))

        # Scale width and position of slider
        scaled_slider_width = self._scale_value(300, 'x')
        self.brightness_slider = ctk.CTkSlider(
            self.root,
            width=scaled_slider_width,
            from_=0,
            to=100,
            command=self.set_brightness,
            button_color="white",
            button_hover_color="lightgray",
            progress_color="white"
        )
        self.brightness_slider.place(x=self._scale_value(123, 'x'), y=self._scale_value(105, 'y'))

    def load_saved_brightness(self):
        """Load brightness value from file and apply it."""
        if os.path.exists(BRIGHTNESS_FILE):
            try:
                with open(BRIGHTNESS_FILE, "r") as f:
                    value = float(f.read().strip())
            except:
                value = 50.0  # Fallback
        else:
            value = 50.0  # Default if file doesn't exist

        self.brightness_slider.set(value)
        self.apply_brightness(value)

    # --- (set_brightness, save_brightness, and apply_brightness methods remain unchanged) ---
    def set_brightness(self, value):
        """Triggered when slider is moved."""
        self.save_brightness(value)
        self.apply_brightness(value)

    def save_brightness(self, value):
        """Save brightness to txt file."""
        os.makedirs(os.path.dirname(BRIGHTNESS_FILE), exist_ok=True)
        with open(BRIGHTNESS_FILE, "w") as f:
            f.write(str(value))

    def apply_brightness(self, target_value):
        """Smoothly transition brightness to target value."""

        def fade():
            system = platform.system()

            # Read current brightness (real for Pi, virtual for Mac)
            if system == "Linux" and os.path.exists("/sys/class/backlight/rpi_backlight/brightness"):
                try:
                    with open("/sys/class/backlight/rpi_backlight/brightness", "r") as f:
                        current = int(f.read().strip()) / 2.55  # Convert 0-255 → 0-100
                except:
                    current = target_value
            else:
                # Simulate brightness on unsupported systems (Mac/Windows)
                current = getattr(self, "_virtual_brightness", target_value)

            step = 1 if target_value > current else -1

            for level in range(int(current), int(target_value), step):
                hardware_value = int(level * 2.55)

                if system == "Linux" and os.path.exists("/sys/class/backlight/rpi_backlight/brightness"):
                    try:
                        with open("/sys/class/backlight/rpi_backlight/brightness", "w") as f:
                            f.write(str(hardware_value))
                        time.sleep(0.01)  # Smooth delay
                    except PermissionError:
                        print("Permission denied: run with sudo")
                        break
                else:
                    self._virtual_brightness = level  # Store fake brightness
                    time.sleep(0.01)  # Smooth delay

        threading.Thread(target=fade, daemon=True).start()
