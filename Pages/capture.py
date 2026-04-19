import customtkinter as ctk
from PIL import Image
import datetime
import cv2
import os
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH 

class CapturePage(SC):
    ORIGINAL_LEFT_PANEL_WIDTH = LEFT_PANEL_WIDTH

    def __init__(self):
        super().__init__()

        # Camera dimensions
        self.fixed_w = 480 
        self.fixed_h = 480
        
        # Camera & State variables
        self.cap = None 
        self.running = False
        self.current_frame = None 
        self.capture_mode = "Disease" # Default mode
        
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

        # Camera positioning
        self.camera_w = self._scale_value(self.fixed_w, 'x')
        self.camera_h = self._scale_value(self.fixed_h, 'y')
        self.camera_x = scaled_panel_w
        self.camera_y = 0

        # Camera Display Label
        self.camera_label = ctk.CTkLabel(
            self.root, text="", width=self.camera_w, height=self.camera_h, fg_color="#1F1F1F"
        )
        self.camera_label.place(x=self.camera_x, y=self.camera_y)

        # Right Side Button Area
        button_area_x = self.camera_x + self.camera_w + self._scale_value(20, 'x')
        button_width = self._scale_value(160, 'x')
        button_height = self._scale_value(60, 'y')

        # Disease Mode Button
        self.disease_btn = ctk.CTkButton(
            self.root,
            text="Disease",
            width=button_width,
            height=button_height,
            hover=False,
            font=("Arial", self._scale_value(18, 'y'), "bold"),
            command=lambda: self.set_mode("Disease")
        )
        self.disease_btn.place(x=button_area_x, y=self._scale_value(150, 'y'))

        # Nutrient Mode Button
        self.nutrient_btn = ctk.CTkButton(
            self.root,
            text="Nutrient",
            width=button_width,
            height=button_height,
            hover=False,
            font=("Arial", self._scale_value(18, 'y'), "bold"),
            command=lambda: self.set_mode("Nutrient")
        )
        self.nutrient_btn.place(x=button_area_x, y=self._scale_value(230, 'y'))

        self.update_button_styles()

    # =============================
    # MODE SWITCHING
    # =============================
    def set_mode(self, mode):
        self.capture_mode = mode
        print(f"Mode set to: {mode}")
        self.update_button_styles()

    def update_button_styles(self):
        """Changes button colors based on active mode."""
        if self.capture_mode == "Disease":
            self.disease_btn.configure(fg_color="#383C4E")
            self.nutrient_btn.configure(fg_color="#2A2E3F")
        else:
            self.nutrient_btn.configure(fg_color="#383C4E")
            self.disease_btn.configure(fg_color="#2A2E3F")

    # =============================
    # CAMERA LOGIC (Computer Compatible)
    # =============================
    def open_camera(self):
        if self.cap and self.cap.isOpened():
             self.cap.release()
        
        self.cap = cv2.VideoCapture(0) # Standard USB/Laptop webcam
        
        if not self.cap.isOpened():
            self.camera_label.configure(text="Camera not found", text_color="red")
            return

        self.running = True
        self.record_button.configure(state="normal")
        self.update_frame()

    def _crop_center_square(self, frame):
        h, w, _ = frame.shape
        min_dim = min(h, w)
        start_x = (w - min_dim) // 2
        start_y = (h - min_dim) // 2
        return frame[start_y:start_y + min_dim, start_x:start_x + min_dim]

    def update_frame(self):
        if self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 1. Process: Crop to square and rotate if necessary 
                # (Removed Pi's 90-degree rotate unless your laptop camera is sideways)
                square_frame = self._crop_center_square(frame)
                self.current_frame = square_frame.copy()

                # 2. Convert for CustomTkinter
                rgb = cv2.cvtColor(square_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                
                # 3. Resize and Display
                ctk_img = ctk.CTkImage(light_image=img, size=(self.camera_w, self.camera_h))
                self.camera_label.configure(image=ctk_img, text="")
                self.camera_label.image = ctk_img

                self.root.after(10, self.update_frame)
            else:
                self.running = False

    # =============================
    # CAPTURE & NAVIGATION
    # =============================
    def capture_image(self):
        if self.current_frame is not None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.save_path, f"capture_{timestamp}.jpg")

            # Save the processed square frame
            cv2.imwrite(path, self.current_frame)
            print(f"[{self.capture_mode}] Captured: {path}")

            self.cleanup_camera()
            self.root.destroy()

            # Import here to avoid circular imports
            from Pages.analysis_page import AnalysisPage
            analysis_app = AnalysisPage(
                image_path=path,
                view_only=False,
                mode=self.capture_mode # Pass the selected mode!
            )
            analysis_app.root.mainloop()

    def cleanup_camera(self):
        self.running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print("✅ Camera released.")

    def navigate_to_dashboard(self):
        self.cleanup_camera()
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.run()