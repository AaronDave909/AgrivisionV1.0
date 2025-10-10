import os
import platform
import time
import threading
import customtkinter as ctk
import psutil
from shared_components import SharedComponents as SC

BRIGHTNESS_FILE = "Page_files/brightness_state.txt"  # Updated path

class SettingsPage(SC):
    def __init__(self):
        super().__init__()
        self.create_title(text="Settings", x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        self.undo_button()
        self.create_memory_usage_bar()
        self.create_brightness_slider()  # Added below storage bar

        label = ctk.CTkLabel(self.root, text="Agrivision v1.0", font=("Arial", 12))
        label.place(x=123, y=449)
        self.load_saved_brightness()

    def create_memory_usage_bar(self):
        disk = psutil.disk_usage('/')
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        percent_used = disk.percent

        label = ctk.CTkLabel(self.root, text="System Storage", font=("Arial", 14, "bold"))
        label.place(x=123, y=128)

        self.storage_bar = ctk.CTkProgressBar(self.root, width=300, progress_color="white")
        self.storage_bar.place(x=123, y=185)
        self.storage_bar.set(percent_used / 100)

        usage_text = f"Used: {used_gb:.1f} GB | Free: {free_gb:.1f} GB"
        usage_label = ctk.CTkLabel(self.root, text=usage_text, font=("Arial", 12))
        usage_label.place(x=123, y=152)

    def create_brightness_slider(self):
        brightness_label = ctk.CTkLabel(self.root, text="Brightness", font=("Arial", 14, "bold"))
        brightness_label.place(x=123, y=66)

        self.brightness_slider = ctk.CTkSlider(
            self.root,
            width=300,
            from_=0,
            to=100,
            command=self.set_brightness,
            button_color="white",
            button_hover_color="lightgray",
            progress_color="white"
        )
        self.brightness_slider.place(x=123, y=105)

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