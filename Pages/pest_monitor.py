import customtkinter as ctk
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH, BG_COLOR
import json
from language_manager import get_text
import cv2
from PIL import Image
from ultralytics import YOLO
import time
import datetime
import os

class PestMonitorPage(SC):
    
    def __init__(self):
        super().__init__()
        
        # --- Detection State & Logic ---
        self.detection_start_time = None
        self.last_detected_pest = None
        self.monitoring_duration = 5.0  # 5 seconds
        
        # --- Cooldown Timers ---
        self.capture_cooldown = 10.0      # 10 sec for normal pests
        self.last_capture_time = 0.0
        self.droplet_cooldown = 1800.0    # 30 minutes for droplets
        self.last_droplet_capture_time = 0.0
        
        self.is_running = True 
        
        # --- Screen Sleep Logic ---
        self.black_overlay = None
        
        # --- Helpers & Model ---
        self.gallery_path = "Page_files/gallery_files"
        self.json_path = os.path.join(self.gallery_path, "gallery_data.json")
        
        try:
            model_path = "Page_files/yolov11_models/pests.pt"
            self.model = YOLO(model_path)
            print(f"✅ {get_text('log_model_success')}")
        except Exception as e:
            print(f"❌ {get_text('log_model_error')}: {e}")
            self.model = None

        # --- Standard Page Setup ---
        self.create_left_panel()
        self.create_leaf_image()
        self.create_title(text=get_text("lbl_pest_monitor"), x=119, y=0)
        self.create_battery_indicator(x=15, y=100)
        self.undo_button(command=self.navigate_to_dashboard) 

        # --- Sleep Screen Button ---
        self.sleep_btn = self.create_button(
            text=get_text("btn_sleep_screen"),
            x=LEFT_PANEL_WIDTH / 2,
            y=160,
            width=85,
            height=40,
            anchor="center",
            font=["Arial", 11, "bold"],
            command=self.sleep_screen
        )

        # --- Camera Display Setup ---
        self.cap = None 
        self.cam_x = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        self.cam_y = 0 
        
        self.root.update_idletasks() 
        self.cam_w = self.root.winfo_width() - self.cam_x
        self.cam_h = self.root.winfo_height()

        self.cam_label = ctk.CTkLabel(
            self.root, 
            text=get_text("lbl_cam_init"), 
            font=("Arial", 20), 
            fg_color="#1F1F1F",
            width=self.cam_w, 
            height=self.cam_h
        )
        self.cam_label.place(x=self.cam_x, y=self.cam_y)

        # Start Camera and Update Loop
        self.open_camera()

    # --- Screen Sleep / Wake (Software Overlay Only for Computer) ---
    def sleep_screen(self):
        if self.black_overlay is not None:
            return
            
        print(f"💻 {get_text('log_sleep_active')}...")
        self.black_overlay = ctk.CTkToplevel(self.root)
        self.black_overlay.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.black_overlay.overrideredirect(True) 
        self.black_overlay.configure(fg_color="black")
        self.black_overlay.attributes('-topmost', True)
        self.black_overlay.bind("<ButtonPress-1>", self.wake_screen)
        
        # Note: Hardware brightness calls (rpi_backlight) are skipped on PC to prevent errors.

    def wake_screen(self, event=None):
        print(f"💻 {get_text('log_screen_wake')}.")
        if self.black_overlay:
            self.black_overlay.destroy()
            self.black_overlay = None

    # --- OpenCV Camera Setup ---
    def open_camera(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise IOError("Webcam not found")
            
            self.is_running = True
            self.root.after(100, self._update_frame)
        except Exception as e:
            self.cam_label.configure(text=f"Error: {e}", text_color="red")

    # --- JSON Helpers ---
    def _load_master_json(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r') as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}

    def _save_master_json(self, data):
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=4)

    # --- Aspect Ratio Helper ---
    def _crop_to_aspect_ratio(self, frame, target_w, target_h):
        h, w, _ = frame.shape
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
        if not self.is_running or not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.root.after(100, self._update_frame)
            return

        # Prepare frame (No Pi-specific rotation needed for standard webcams)
        frame_ready = self._crop_to_aspect_ratio(frame, self.cam_w, self.cam_h)
        results = self.model(frame_ready, verbose=False)
        annotated_frame = frame_ready.copy()
        
        current_time = time.time()
        target_box = None
        is_droplet_target = False

        # --- Smart Target Selection with Cooldowns ---
        if len(results[0].boxes) > 0:
            for box in results[0].boxes:
                name = results[0].names[int(box.cls)].lower()
                
                if "droplet" in name:
                    if current_time >= (self.last_droplet_capture_time + self.droplet_cooldown):
                        target_box = box
                        is_droplet_target = True
                        break
                else:
                    if current_time >= (self.last_capture_time + self.capture_cooldown):
                        target_box = box
                        is_droplet_target = False
                        break

        # --- Timer Logic ---
        if target_box is not None:
            pest_name = results[0].names[int(target_box.cls)].replace("_", " ").title()
            annotated_frame = results[0].plot()

            if self.detection_start_time is None or self.last_detected_pest != pest_name:
                self.detection_start_time = current_time
                self.last_detected_pest = pest_name
                log_msg = get_text("log_target_lock").replace("{pest}", pest_name)
                print(f"🎯 {log_msg}...")
            else:
                if (current_time - self.detection_start_time) >= self.monitoring_duration:
                    self._save_pest_capture(annotated_frame, results, target_box)
                    if is_droplet_target:
                        self.last_droplet_capture_time = current_time
                    else:
                        self.last_capture_time = current_time
                    self.detection_start_time = None
        else:
            if len(results[0].boxes) > 0:
                annotated_frame = results[0].plot() # Still show boxes even if on cooldown
            self.detection_start_time = None

        # --- UI Update ---
        rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb).resize((self.cam_w, self.cam_h))
        ctk_img = ctk.CTkImage(light_image=img, size=(self.cam_w, self.cam_h))
        self.cam_label.configure(image=ctk_img, text="")
        self.cam_label.image = ctk_img

        self.root.after(30, self._update_frame)

    def _save_pest_capture(self, annotated_frame, results, target_box):
        now = datetime.datetime.now()
        img_name = f"pest_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(self.gallery_path, img_name)
        
        os.makedirs(self.gallery_path, exist_ok=True)
        cv2.imwrite(path, annotated_frame)

        new_data = {
            "pest": results[0].names[int(target_box.cls)],
            "accuracy": f"{target_box.conf.item()*100:.2f}%",
            "count": str(len(results[0].boxes)),
            "timestamp": now.strftime("%b %d, %Y %I:%M %p")
        }

        master = self._load_master_json()
        master[img_name] = new_data
        self._save_master_json(master)
        print(f"✅ {get_text('log_saved_capture')}: {img_name}")

    def cleanup_camera(self):
        self.is_running = False
        if self.cap:
            self.cap.release()

    def navigate_to_dashboard(self):
        self.cleanup_camera() 
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        app = MyDashboard()
        app.run()