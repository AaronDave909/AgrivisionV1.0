import customtkinter as ctk
from PIL import Image
import datetime
import cv2
import os
from picamera2 import Picamera2 # Back to Pi-specific library
from language_manager import get_text
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH 

class CapturePage(SC):
    ORIGINAL_LEFT_PANEL_WIDTH = LEFT_PANEL_WIDTH

    def __init__(self):
        super().__init__()

        # Camera dimensions
        self.fixed_w = 480 
        self.fixed_h = 480
        
        # Camera & State variables
        self.picam2 = None # Updated for Pi
        self.running = False
        self.current_frame = None 
        self.capture_mode = "Disease" 
        
        # Filesystem
        self.save_path = "Page_files/captured_images"
        os.makedirs(self.save_path, exist_ok=True)

        # UI Setup
        self.create_left_panel()
        self.create_leaf_image()
        self.create_battery_indicator(x=15, y=100)

        # Setup Camera and Mode Buttons
        self.setup_layout()

        # Global Buttons
        self.undo_button(command=self.navigate_to_dashboard) 
        self.record_button = self.create_record_button(
            x=53.5, y=480 / 2, command=self.capture_image
        )
        self.record_button.configure(state="disabled")

        # Initialize Camera
        self.root.after(100, self.open_camera)

    def setup_layout(self):
        """Creates the camera display and the mode selection buttons."""
        self.root.update_idletasks()
        scaled_panel_w = self._scale_value(self.ORIGINAL_LEFT_PANEL_WIDTH, 'x')

        self.camera_w = self._scale_value(self.fixed_w, 'x')
        self.camera_h = self._scale_value(self.fixed_h, 'y')
        self.camera_x = scaled_panel_w
        self.camera_y = 0

        self.camera_label = ctk.CTkLabel(
            self.root, text="", width=self.camera_w, height=self.camera_h, fg_color="#1F1F1F"
        )
        self.camera_label.place(x=self.camera_x, y=self.camera_y)

        button_area_x = self.camera_x + self.camera_w + self._scale_value(20, 'x')
        button_width = self._scale_value(160, 'x')
        button_height = self._scale_value(60, 'y')

        self.disease_btn = ctk.CTkButton(
            self.root,
            text=get_text("btn_disease"),
            width=button_width,
            height=button_height,
            hover=False,
            font=("Arial", self._scale_value(18, 'y'), "bold"),
            command=lambda: self.set_mode("Disease")
        )
        self.disease_btn.place(x=button_area_x, y=self._scale_value(150, 'y'))

        self.nutrient_btn = ctk.CTkButton(
            self.root,
            text=get_text("btn_nutrient"),
            width=button_width,
            height=button_height,
            hover=False,
            font=("Arial", self._scale_value(18, 'y'), "bold"),
            command=lambda: self.set_mode("Nutrient")
        )
        self.nutrient_btn.place(x=button_area_x, y=self._scale_value(230, 'y'))

        self.update_button_styles()

    def set_mode(self, mode):
        self.capture_mode = mode
        mode_label = get_text("btn_disease") if mode == "Disease" else get_text("btn_nutrient")
        print(f"--- {get_text('log_mode_set')}: {mode_label}")
        self.update_button_styles()

    def update_button_styles(self):
        if self.capture_mode == "Disease":
            self.disease_btn.configure(fg_color="#383C4E")
            self.nutrient_btn.configure(fg_color="#2A2E3F")
        else:
            self.nutrient_btn.configure(fg_color="#383C4E")
            self.disease_btn.configure(fg_color="#2A2E3F")

    # =============================
    # CAMERA LOGIC (Raspberry Pi)
    # =============================
    def open_camera(self):
        try:
            self.picam2 = Picamera2()
            # Capture in RGB888 for easier UI integration
            config = self.picam2.create_video_configuration(
                main={"size": (1280, 720), "format": "BGR888"}
            )
            self.picam2.configure(config)
            self.picam2.start()

            self.running = True
            self.record_button.configure(state="normal")
            self.update_frame()
        except Exception as e:
            error_msg = f"{get_text('err_camera_not_found')}: {e}"
            self.camera_label.configure(text=error_msg, text_color="red")

    def _crop_center_square(self, frame):
        h, w, _ = frame.shape
        min_dim = min(h, w)
        start_x = (w - min_dim) // 2
        start_y = (h - min_dim) // 2
        return frame[start_y:start_y + min_dim, start_x:start_x + min_dim]

    def update_frame(self):
        if self.running and self.picam2:
            try:
                # Capture frame from Pi
                raw_frame = self.picam2.capture_array()
                
                # Apply rotation for vertical orientation (Pi standard)
                rotated = cv2.rotate(raw_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                square = self._crop_center_square(rotated)

                self.current_frame = square.copy()

                # Convert to PIL for Tkinter (Note: Frame is already RGB from Picamera2 config)
                img = Image.fromarray(self.current_frame)
                img = img.resize((self.camera_w, self.camera_h))

                ctk_img = ctk.CTkImage(light_image=img, size=(self.camera_w, self.camera_h))
                self.camera_label.configure(image=ctk_img, text="")
                self.camera_label.image = ctk_img

                self.root.after(20, self.update_frame) # Balanced refresh rate
            except:
                self.running = False

    # =============================
    # CAPTURE & NAVIGATION
    # =============================
    def capture_image(self):
        if self.current_frame is not None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.save_path, f"capture_{timestamp}.jpg")

            # CRITICAL: cv2.imwrite expects BGR, but current_frame is RGB
            # We convert it right before saving to keep colors accurate
            save_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(path, save_frame)

            mode_label = get_text("btn_disease") if self.capture_mode == "Disease" else get_text("btn_nutrient")
            print(f"[{mode_label}] {get_text('log_captured')}: {path}")

            self.cleanup_camera()
            self.root.destroy()

            from Pages.analysis_page import AnalysisPage
            analysis_app = AnalysisPage(
                image_path=path,
                view_only=False,
                mode=self.capture_mode
            )
            analysis_app.root.mainloop()

    def cleanup_camera(self):
        self.running = False
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
                print(f"✅ {get_text('log_camera_released')}.")
            except:
                pass

    def navigate_to_dashboard(self):
        self.cleanup_camera()
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.run()
