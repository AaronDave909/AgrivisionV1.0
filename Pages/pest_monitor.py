import customtkinter as ctk
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH
# REMOVED: No longer need PestAnalytics
import cv2
from PIL import Image
from ultralytics import YOLO
import time
import datetime
import os
import json # NEW: Import json

class PestMonitorPage(SC):
    
    def __init__(self):
        super().__init__()
        
        # --- Detection State & Logic ---
        self.detection_start_time = None
        self.last_detected_pest = None
        self.monitoring_duration = 5.0  # 5 seconds
        self.capture_cooldown = 10.0 # 10 sec cooldown after capture
        self.last_capture_time = 0.0
        self.is_running = True # Flag to stop the update loop on exit
        
        # --- Helpers & Model ---
        # MODIFIED: Define paths directly
        self.gallery_path = "Page_files/gallery_files"
        self.json_path = os.path.join(self.gallery_path, "gallery_data.json")
        
        try:
            model_path = "Page_files/yolov11_models/pests.pt"
            self.model = YOLO(model_path)
            print(f"✅ Successfully loaded pest model from {model_path}")
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Could not load pest model: {e}")
            self.model = None

        # --- Standard Page Setup ---
        self.create_left_panel()
        self.create_leaf_image()
        self.create_title(text="Pest Monitor", x=119, y=0)
        self.undo_button(command=self.navigate_to_dashboard) 

        # --- Camera & Display Setup ---
        try:
            self.cap = cv2.VideoCapture(0) 
            if not self.cap.isOpened():
                raise IOError("Cannot open webcam")
            print("✅ Camera initialized.")
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Could not open camera: {e}")
            self.cap = None

        self.cam_x = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        self.cam_y = 0 
        
        self.root.update_idletasks() 
        self.cam_w = self.root.winfo_width() - self.cam_x
        self.cam_h = self.root.winfo_height()

        self.cam_label = ctk.CTkLabel(self.root, text="Initializing Camera...", 
                                      font=("Arial", 20), fg_color="#1F1F1F",
                                      width=self.cam_w, height=self.cam_h)
        
        self.cam_label.place(x=self.cam_x, y=self.cam_y)

        if not self.cap:
            self.cam_label.configure(text="Error: Camera not found.\nCheck connection.")
            return

        self.root.after(100, self._update_frame)

    # --- NEW: JSON Helper Functions ---
    def _load_master_json(self):
        """Loads the master JSON. Returns an empty dict if it doesn't exist or is empty."""
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
            print(f"❌ Error reading master JSON: {e}. Returning empty dict.")
            return {}

    def _save_master_json(self, data):
        """Saves the provided dictionary to the master JSON file."""
        try:
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"❌ Error writing master JSON: {e}")

    # --- Main Update Loop ---
    def _update_frame(self):
        """Continuously grabs frames, runs analysis, and updates the UI."""
        if not self.is_running or not self.cap:
            return

        try:
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️ Warning: Could not read frame from camera.")
                if self.is_running:
                    self.root.after(100, self._update_frame)
                return

            results = self.model(frame)
            annotated_frame = frame 
            
            is_cooldown = time.time() < (self.last_capture_time + self.capture_cooldown)

            # --- Detection Logic ---
            if len(results[0].boxes) > 0 and not is_cooldown:
                top_detection = results[0].boxes[0]
                pest_name_raw = results[0].names[int(top_detection.cls)]
                pest_name = pest_name_raw.replace("_", " ").title()
                
                annotated_frame = results[0].plot()

                if self.detection_start_time is None or self.last_detected_pest != pest_name:
                    self.detection_start_time = time.time()
                    self.last_detected_pest = pest_name
                    print(f"👀 New pest detected: {pest_name}. Starting 5s timer...")
                else:
                    elapsed = time.time() - self.detection_start_time
                    if elapsed >= self.monitoring_duration:
                        print(f"✅ Pest {pest_name} detected for {self.monitoring_duration}s. Capturing...")
                        # MODIFIED: Pass the full results object
                        self._save_pest_capture(annotated_frame, results)
                        
                        self.detection_start_time = None
                        self.last_detected_pest = None
                        self.last_capture_time = time.time()
                        print(f"📸 Capture complete. Starting {self.capture_cooldown}s cooldown.")
            
            elif is_cooldown:
                if len(results[0].boxes) > 0:
                    annotated_frame = results[0].plot()

            else:
                if self.detection_start_time is not None:
                    print("...Pest lost. Resetting timer.")
                self.detection_start_time = None
                self.last_detected_pest = None

            # --- Display the frame ---
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            pil_img_resized = pil_img.resize((self.cam_w, self.cam_h), Image.Resampling.BILINEAR)
            ctk_img = ctk.CTkImage(light_image=pil_img_resized, size=(self.cam_w, self.cam_h))
            
            self.cam_label.configure(image=ctk_img, text="")
            self.cam_label.image = ctk_img

            if self.is_running:
                self.root.after(30, self._update_frame) 

        except Exception as e:
            print(f"❌ Error in update loop: {e}")
            if self.is_running:
                self.root.after(1000, self._update_frame) 

    # --- MODIFIED: Save function now saves to gallery_data.json ---
    def _save_pest_capture(self, annotated_frame, results):
        """Saves the captured frame and records analytics to gallery_data.json."""
        try:
            now = datetime.datetime.now()
            
            # 1. Save the Image
            img_filename = f"pest_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
            img_save_path = os.path.join(self.gallery_path, img_filename)
            
            os.makedirs(self.gallery_path, exist_ok=True)
            cv2.imwrite(img_save_path, annotated_frame)
            print(f"🖼️  Image saved to {img_save_path}")

            # 2. Prepare Analytics Data (similar to analysis_page)
            if len(results[0].boxes) > 0:
                top_detection = results[0].boxes[0]
                pest_name_raw = results[0].names[int(top_detection.cls)]
                accuracy = f"{top_detection.conf.item()*100:.2f}%"
                detection_count = str(len(results[0].boxes))
            else:
                pest_name_raw = "Unknown"
                accuracy = "N/A"
                detection_count = "0"
                
            timestamp_str = now.strftime("%b %d, %Y %I:%M %p")

            # 3. Create data dict using "pest" key
            new_detection_data = {
                "pest": pest_name_raw, # <-- KEY IS "pest"
                "accuracy": accuracy,
                "count": detection_count,
                "timestamp": timestamp_str
            }

            # 4. Load, update, and save the main JSON file
            master_data = self._load_master_json()
            master_data[img_filename] = new_detection_data
            self._save_master_json(master_data)
            
            print(f"✅ Pest detection saved to gallery_data.json: {pest_name_raw} -> {img_filename}")

        except Exception as e:
            print(f"❌ Error during capture save: {e}")

    def cleanup_camera(self):
        """Stops the loop and releases the camera resource."""
        print("Cleaning up camera...")
        self.is_running = False
        if self.cap:
            self.cap.release()
            print("Camera released.")

    def navigate_to_dashboard(self):
        """Cleans up camera resources and then navigates to the main dashboard."""
        self.cleanup_camera() 
        self.root.destroy()
        
        from Pages.main_dashboard import MyDashboard 
        app = MyDashboard()
        app.run()

