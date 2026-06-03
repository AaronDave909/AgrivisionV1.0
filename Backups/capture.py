import customtkinter as ctk
from PIL import Image
import datetime
import cv2
import os
from picamera2 import Picamera2 
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH 

class CapturePage(SC):
    ORIGINAL_LEFT_PANEL_WIDTH = LEFT_PANEL_WIDTH

    def __init__(self):
        super().__init__()

        self.fixed_w = 480 
        self.fixed_h = 480
        self.picam2 = None 
        self.running = False
        self.current_frame = None 
        self.save_path = "Page_files/captured_images"
        os.makedirs(self.save_path, exist_ok=True)

        # Default mode
        self.capture_mode = "Disease"

        self.create_left_panel()
        self.create_leaf_image()
        self.create_battery_indicator(x=15, y=100)

        # Create camera + buttons
        self.setup_layout()

        self.undo_button(command=self.navigate_to_dashboard) 
        self.record_button = self.create_record_button(
            x=53.5, y=480 / 2, command=self.capture_image
        )
        self.record_button.configure(state="disabled")

        self.root.after(100, self.open_camera)

    # =============================
    # NEW LAYOUT (Camera + Buttons)
    # =============================
    def setup_layout(self):
        self.root.update_idletasks()

        scaled_panel_w = self._scale_value(self.ORIGINAL_LEFT_PANEL_WIDTH, 'x')

        # Camera position (RIGHT NEXT TO PANEL)
        self.camera_w = self._scale_value(self.fixed_w, 'x')
        self.camera_h = self._scale_value(self.fixed_h, 'y')

        self.camera_x = scaled_panel_w
        self.camera_y = 0

        # Camera display
        self.camera_label = ctk.CTkLabel(
            self.root, text="", width=self.camera_w, height=self.camera_h
        )
        self.camera_label.place(x=self.camera_x, y=self.camera_y)

        # =============================
        # RIGHT SIDE BUTTONS
        # =============================
        button_area_x = self.camera_x + self.camera_w + self._scale_value(20, 'x')

        button_width = self._scale_value(160, 'x')
        button_height = self._scale_value(60, 'y')

        # Disease Button
        self.disease_btn = ctk.CTkButton(
            self.root,
            text="Disease",
            width=button_width,
            height=button_height,
            hover=False,
            font=("Arial", self._scale_value(18, 'y'), "bold"),
            command=lambda: self.set_mode("Disease")
        )
        self.disease_btn.place(
            x=button_area_x,
            y=self._scale_value(150, 'y')
        )

        # Nutrient Button
        self.nutrient_btn = ctk.CTkButton(
            self.root,
            text="Nutrient",
            width=button_width,
            height=button_height,
            hover=False,
            font=("Arial", self._scale_value(18, 'y'), "bold"),
            command=lambda: self.set_mode("Nutrient")
        )
        self.nutrient_btn.place(
            x=button_area_x,
            y=self._scale_value(230, 'y')
        )

        # Highlight default
        self.update_button_styles()

    # =============================
    # MODE SWITCHING
    # =============================
    def set_mode(self, mode):
        self.capture_mode = mode
        print(f"Mode set to: {mode}")
        self.update_button_styles()

    def update_button_styles(self):
        if self.capture_mode == "Disease":
            self.disease_btn.configure(fg_color="#383C4E")
            self.nutrient_btn.configure(fg_color="#2A2E3F")
        else:
            self.nutrient_btn.configure(fg_color="#383C4E")
            self.disease_btn.configure(fg_color="#2A2E3F")

    # =============================
    # CAMERA
    # =============================
    def open_camera(self):
        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_video_configuration(
                main={"size": (1280, 720), "format": "RGB888"}
            )
            self.picam2.configure(config)
            self.picam2.start()

            self.running = True
            self.record_button.configure(state="normal")
            self.update_frame()

        except Exception as e:
            self.camera_label.configure(text=f"Camera Error: {e}")

    def _crop_center_square(self, frame):
        h, w, _ = frame.shape
        min_dim = min(h, w)
        start_x = (w - min_dim) // 2
        start_y = (h - min_dim) // 2
        return frame[start_y:start_y + min_dim, start_x:start_x + min_dim]

    def update_frame(self):
        if self.running and self.picam2:
            try:
                raw_frame = self.picam2.capture_array() 
                rotated = cv2.rotate(raw_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                square = self._crop_center_square(rotated)

                self.current_frame = square.copy()

                rgb = cv2.cvtColor(square, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                img = img.resize((self.camera_w, self.camera_h))

                ctk_img = ctk.CTkImage(light_image=img, size=(self.camera_w, self.camera_h))

                self.camera_label.configure(image=ctk_img, text="")
                self.camera_label.image = ctk_img

                self.root.after(10, self.update_frame)

            except:
                self.running = False

    # =============================
    # CAPTURE
    # =============================
    def capture_image(self):
        if self.current_frame is not None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.save_path, f"capture_{timestamp}.jpg")

            cv2.imwrite(path, self.current_frame)

            print(f"[{self.capture_mode}] Captured: {path}")

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
            except:
                pass

    def navigate_to_dashboard(self):
        self.cleanup_camera()
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.run()
