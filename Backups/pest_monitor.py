import customtkinter as ctk
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH, BG_COLOR
import cv2
from PIL import Image
from ultralytics import YOLO
import time
import datetime
import os
import json
# NEW: Import Picamera2
from picamera2 import Picamera2

class PestMonitorPage(SC):
    
    def __init__(self):
        super().__init__()
        
        # --- Detection State & Logic ---
        self.detection_start_time = None
        self.last_detected_pest = None
        self.monitoring_duration = 5.0  # 5 seconds
        
        # --- Cooldown Timers ---
        self.capture_cooldown = 10.0 # 10 sec cooldown for normal pests
        self.last_capture_time = 0.0
        
        self.droplet_cooldown = 1800.0 # 30 minutes (30 * 60 seconds) for droplets
        self.last_droplet_capture_time = 0.0
        
        self.is_running = True # Flag to stop the update loop on exit
        
        # --- Screen Sleep Logic ---
        self.black_overlay = None
        self.saved_brightness = "255" # Default hardware brightness
        
        # --- Helpers & Model ---
        self.gallery_path = "Page_files/gallery_files"
        self.json_path = os.path.join(self.gallery_path, "gallery_data.json")
        
        try:
            model_path = "Page_files/yolov11_models/pests.pt"
            self.model = YOLO(model_path)
            print(f"Successfully loaded pest model from {model_path}")
        except Exception as e:
            print(f"CRITICAL ERROR: Could not load pest model: {e}")
            self.model = None

        # --- Standard Page Setup ---
        self.create_left_panel()
        self.create_leaf_image()
        self.create_title(text="Pest Monitor", x=119, y=0)
        self.create_battery_indicator(x=15, y=100)
        self.undo_button(command=self.navigate_to_dashboard) 

        # --- NEW: Sleep Screen Button ---
        self.sleep_btn = self.create_button(
            text="Sleep\nScreen",
            x=LEFT_PANEL_WIDTH / 2,
            y=160,
            width=85,
            height=40,
            anchor="center",
            font=["Arial", 11, "bold"],
            command=self.sleep_screen
        )

        # --- Camera & Display Setup ---
        self.picam2 = None # Will be initialized in setup_picamera
        
        # Calculate dimensions for the camera feed
        self.cam_x = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        self.cam_y = 0 
        
        self.root.update_idletasks() 
        self.cam_w = self.root.winfo_width() - self.cam_x
        self.cam_h = self.root.winfo_height()

        self.cam_label = ctk.CTkLabel(
            self.root, 
            text="Initializing Camera...", 
            font=("Arial", 20), 
            fg_color=self._get_color(BG_COLOR),
            width=self.cam_w, 
            height=self.cam_h
        )
        self.cam_label.place(x=self.cam_x, y=self.cam_y)

        # Start camera setup and then the loop
        self.setup_picamera()

    # --- Screen Sleep / Wake Functions ---
    def sleep_screen(self):
        """Activates a full-screen black overlay and attempts to turn off the hardware display."""
        if self.black_overlay is not None:
            return
            
        print("Screen entering Sleep Mode (AI continues monitoring)...")
            
        self.black_overlay = ctk.CTkToplevel(self.root)
        self.black_overlay.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.black_overlay.overrideredirect(True) 
        self.black_overlay.configure(fg_color="black")
        self.black_overlay.attributes('-topmost', True)
        
        self.black_overlay.bind("<ButtonPress-1>", self.wake_screen)
        
        try:
            brightness_path = "/sys/class/backlight/rpi_backlight/brightness"
            if os.path.exists(brightness_path):
                with open(brightness_path, "r") as f:
                    self.saved_brightness = f.read().strip()
                with open(brightness_path, "w") as f:
                    f.write("0")
            else:
                os.system("vcgencmd display_power 0")
        except Exception as e:
            print(f"Hardware sleep error (Software overlay still active): {e}")

    def wake_screen(self, event=None):
        """Removes the black overlay and turns the hardware display back on."""
        print("Screen Woken Up.")
        
        try:
            brightness_path = "/sys/class/backlight/rpi_backlight/brightness"
            if os.path.exists(brightness_path):
                with open(brightness_path, "w") as f:
                    f.write(self.saved_brightness)
            else:
                os.system("vcgencmd display_power 1")
        except Exception as e:
            print(f"Hardware wake error: {e}")
            
        if self.black_overlay:
            self.black_overlay.destroy()
            self.black_overlay = None

    # --- Picamera2 Setup ---
    def setup_picamera(self):
        """Initializes and starts the Picamera2 feed."""
        if self.model is None:
             self.cam_label.configure(text="Error: Pest Model not found.\nCannot start monitor.", text_color="red")
             return
            
        try:
            self.picam2 = Picamera2()
            
            config = self.picam2.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"})
            self.picam2.configure(config)
            
            self.picam2.set_controls({"AfMode": 2, "AfTrigger": 0})
            
            self.picam2.start()
            self.is_running = True
            print("Picamera2 initialized and started.")
            
            self.root.after(100, self._update_frame)
            
        except Exception as e:
            print(f"CRITICAL ERROR: Could not open Picamera2: {e}")
            self.cam_label.configure(text=f"Error: Camera not found.\nCheck connection.\n{e}", text_color="red")
            self.picam2 = None
            return

    # --- JSON Helper Functions ---
    def _load_master_json(self):
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r') as f:
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
            else:
                return {}
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error reading master JSON: {e}. Returning empty dict.")
            return {}

    def _save_master_json(self, data):
        try:
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error writing master JSON: {e}")

    # --- Dynamic Aspect Ratio Crop ---
    def _crop_to_aspect_ratio(self, frame, target_w, target_h):
        h, w, _ = frame.shape
        if target_h == 0: return frame 
        
        target_aspect = target_w / target_h
        frame_aspect = w / h

        if frame_aspect > target_aspect:
            new_w = int(h * target_aspect)
            start_x = (w - new_w) // 2
            return frame[:, start_x:start_x + new_w]
        else:
            new_h = int(w / target_aspect)
            start_y = (h - new_h) // 2
            return frame[start_y:start_y + new_h, :]

    # --- Main Update Loop ---
    def _update_frame(self):
        if not self.is_running or not self.picam2:
            return

        try:
            raw_frame_bgr = self.picam2.capture_array()
            rotated_bgr = cv2.rotate(raw_frame_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame_bgr = self._crop_to_aspect_ratio(rotated_bgr, self.cam_w, self.cam_h)
            
            results = self.model(frame_bgr, verbose=False)
            annotated_frame = frame_bgr.copy() 
            
            current_time = time.time()
            target_box = None
            is_droplet_target = False

            # --- Smart Target Selection ---
            if len(results[0].boxes) > 0:
                for box in results[0].boxes:
                    cls_id = int(box.cls)
                    name = results[0].names[cls_id].lower()
                    
                    if "droplet" in name:
                        # Only target droplet if its specific 30-min cooldown is over
                        if current_time >= (self.last_droplet_capture_time + self.droplet_cooldown):
                            target_box = box
                            is_droplet_target = True
                            break
                    else:
                        # Normal pest check against standard 10-sec cooldown
                        if current_time >= (self.last_capture_time + self.capture_cooldown):
                            target_box = box
                            is_droplet_target = False
                            break

            # --- Timer & Capture Logic ---
            if target_box is not None:
                pest_name_raw = results[0].names[int(target_box.cls)]
                pest_name = pest_name_raw.replace("_", " ").title()
                
                annotated_frame = results[0].plot()

                if self.detection_start_time is None or self.last_detected_pest != pest_name:
                    self.detection_start_time = current_time
                    self.last_detected_pest = pest_name
                    print(f"New target detected: {pest_name}. Starting 5s timer...")
                else:
                    elapsed = current_time - self.detection_start_time
                    if elapsed >= self.monitoring_duration:
                        print(f"Target {pest_name} detected for {self.monitoring_duration}s. Capturing...")
                        self._save_pest_capture(annotated_frame, results, target_box)
                        
                        self.detection_start_time = None
                        self.last_detected_pest = None
                        
                        # Update the appropriate cooldown timer
                        if is_droplet_target:
                            self.last_droplet_capture_time = current_time
                            print(f"Droplet captured. Entering 30-minute cooldown.")
                        else:
                            self.last_capture_time = current_time
                            print(f"Pest captured. Entering {self.capture_cooldown}s cooldown.")
            
            else:
                # If we have detections but they are all on cooldown, just draw the boxes
                if len(results[0].boxes) > 0:
                    annotated_frame = results[0].plot()

                if self.detection_start_time is not None:
                    print("...Target lost or on cooldown. Resetting timer.")
                self.detection_start_time = None
                self.last_detected_pest = None

            # --- Display the frame ---
            display_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            
            pil_img = Image.fromarray(display_rgb)
            pil_img_resized = pil_img.resize((self.cam_w, self.cam_h), Image.Resampling.BILINEAR)
            ctk_img = ctk.CTkImage(light_image=pil_img_resized, dark_image=pil_img_resized, size=(self.cam_w, self.cam_h))
            
            self.cam_label.configure(image=ctk_img, text="")
            self.cam_label.image = ctk_img

            if self.is_running:
                self.root.after(30, self._update_frame) 

        except Exception as e:
            print(f"Error in update loop: {e}")
            if self.is_running:
                self.root.after(1000, self._update_frame) 

    # --- Save Capture ---
    def _save_pest_capture(self, annotated_frame, results, target_box):
        """Saves the captured frame and records analytics to gallery_data.json."""
        try:
            now = datetime.datetime.now()
            
            img_filename = f"pest_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
            img_save_path = os.path.join(self.gallery_path, img_filename)
            
            os.makedirs(self.gallery_path, exist_ok=True)
            cv2.imwrite(img_save_path, annotated_frame)
            print(f"Image saved to {img_save_path}")

            if target_box is not None:
                pest_name_raw = results[0].names[int(target_box.cls)]
                accuracy = f"{target_box.conf.item()*100:.2f}%"
                detection_count = str(len(results[0].boxes))
            else:
                pest_name_raw = "Unknown"
                accuracy = "N/A"
                detection_count = "0"
                
            timestamp_str = now.strftime("%b %d, %Y %I:%M %p")

            new_detection_data = {
                "pest": pest_name_raw, 
                "accuracy": accuracy,
                "count": detection_count,
                "timestamp": timestamp_str
            }

            master_data = self._load_master_json()
            master_data[img_filename] = new_detection_data
            self._save_master_json(master_data)
            
            print(f"Detection saved to gallery_data.json: {pest_name_raw} -> {img_filename}")

        except Exception as e:
            print(f"Error during capture save: {e}")

    # --- Cleanup for Picamera2 ---
    def cleanup_camera(self):
        """Stops the loop and releases the camera resource."""
        print("Cleaning up camera...")
        self.is_running = False
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
                print("Picamera2 released.")
            except Exception as e:
                print(f"Error closing picam2: {e}")

    # --- Navigation ---
    def navigate_to_dashboard(self):
        """Cleans up camera resources and then navigates to the main dashboard."""
        self.cleanup_camera() 
        self.root.destroy()
        
        from Pages.main_dashboard import MyDashboard 
        app = MyDashboard()
        app.run()
