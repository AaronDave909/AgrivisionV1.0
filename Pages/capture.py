import customtkinter as ctk
from PIL import Image, ImageTk
import datetime
import cv2
import os
from shared_components import SharedComponents as SC, custom_font_regular, LEFT_PANEL_WIDTH # Import scaled font

class CapturePage(SC):
    ORIGINAL_LEFT_PANEL_WIDTH = LEFT_PANEL_WIDTH
    ORIGINAL_MARGIN = 20
    ORIGINAL_TITLE_AREA_HEIGHT = 70 

    def __init__(self, fixed_w=None, fixed_h=None, offset_x=None, offset_y=None):
        super().__init__()

        self.fixed_w = 480 
        self.fixed_h = 480
        self.offset_x = offset_x
        self.offset_y = offset_y

        self.cap = None
        self.running = False
        self.current_frame = None
        self.save_path = "Page_files/captured_images"
        os.makedirs(self.save_path, exist_ok=True)
        
        self.camera_w, self.camera_h, self.camera_x, self.camera_y = 0, 0, 0, 0
        
        self.create_left_panel()
        self.create_leaf_image()
        # The undo button now calls a method that cleans up the camera first
        self.undo_button(command=self.navigate_to_dashboard) 
        
        self.record_button = self.create_record_button(x=53.5, y=480 / 2, command=self.capture_image) 
        self.record_button.configure(state="disabled")

        self.root.after(100, self.setup_camera_ui)

    def setup_camera_ui(self):
        self.calculate_camera_geometry()
        self.camera_label = ctk.CTkLabel(self.root, text="", width=self.camera_w, height=self.camera_h, fg_color="#1F1F1F")
        self.camera_label.place(x=self.camera_x, y=self.camera_y)
        self.open_camera()

    def calculate_camera_geometry(self):
        self.root.update_idletasks()
        scaled_panel_w = self._scale_value(self.ORIGINAL_LEFT_PANEL_WIDTH, 'x')
        self.camera_w = self._scale_value(self.fixed_w, 'x')
        self.camera_h = self._scale_value(self.fixed_h, 'y')
        
        if self.offset_x is not None and self.offset_y is not None:
            self.camera_x = self._scale_value(self.offset_x, 'x')
            self.camera_y = self._scale_value(self.offset_y, 'y')
        else:
            space_right_of_panel = self.root.winfo_width() - scaled_panel_w
            # Corrected centering logic to place it next to the left panel
            self.camera_x = scaled_panel_w + (space_right_of_panel // 2) - (self.camera_w // 2)
            self.camera_y = 0
            print(f"Camera position ALIGNED TOP, CENTERED RIGHT at: {self.camera_x}, {self.camera_y}")

    def open_camera(self):
        if self.cap and self.cap.isOpened():
             self.cap.release()
        self.cap = cv2.VideoCapture(1)
        if not self.cap.isOpened():
            self.camera_label.configure(text="Camera not found or busy", text_color="red")
            self.record_button.configure(state="disabled")
            return
        self.running = True
        self.record_button.configure(state="normal")
        self.update_frame()

    def update_frame(self):
        if self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame.copy() 
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(image_rgb)
                pil_image_resized = pil_image.resize((self.camera_w, self.camera_h), Image.Resampling.BILINEAR)
                tk_image = ctk.CTkImage(light_image=pil_image_resized, size=(self.camera_w, self.camera_h))
                self.camera_label.configure(image=tk_image, text="")
                self.camera_label.image = tk_image 
                self.root.after(10, self.update_frame)

    def capture_image(self):
        """Saves a temporary image, cleans up, and navigates to the AnalysisPage."""
        if self.current_frame is not None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"capture_{timestamp}.jpg"
            temp_path = os.path.join(self.save_path, temp_filename)
            cv2.imwrite(temp_path, self.current_frame)
            print(f"📸 Image captured for analysis: {temp_path}")

            # --- NEW WORKFLOW ---
            # 1. Clean up the camera resources
            self.cleanup_camera()
            
            # 2. Close this window and open the Analysis Page
            self.root.destroy()
            from Pages.analysis_page import AnalysisPage # Local import to avoid circular dependency
            analysis_app = AnalysisPage(captured_image_path=temp_path)
            analysis_app.root.mainloop()
            
    def cleanup_camera(self):
        """Reliably stops the camera feed and releases the camera resource."""
        print("Cleaning up camera resources...")
        self.running = False  # This stops the self.root.after loop
        if self.cap and self.cap.isOpened():
            self.cap.release()
            cv2.destroyAllWindows()
            print("✅ Camera released.")

    def navigate_to_dashboard(self):
        """Cleans up camera resources and then navigates to the main dashboard."""
        self.cleanup_camera()
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.root.mainloop()
