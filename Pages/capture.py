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
        self.current_frame = None # This will now store the PROCESSED (square) frame
        self.save_path = "Page_files/captured_images"
        os.makedirs(self.save_path, exist_ok=True)
        
        self.camera_w, self.camera_h, self.camera_x, self.camera_y = 0, 0, 0, 0
        
        self.create_left_panel()
        self.create_leaf_image()
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
            self.camera_x = scaled_panel_w + (space_right_of_panel // 2) - (self.camera_w // 2)
            self.camera_y = 0
            print(f"Camera position ALIGNED TOP, CENTERED RIGHT at: {self.camera_x}, {self.camera_y}")

    def open_camera(self):
        if self.cap and self.cap.isOpened():
             self.cap.release()
        self.cap = cv2.VideoCapture(1) # For Pi, may need to try 0 or use a GStreamer pipeline
        if not self.cap.isOpened():
            self.camera_label.configure(text="Camera not found or busy", text_color="red")
            self.record_button.configure(state="disabled")
            return
        self.running = True
        self.record_button.configure(state="normal")
        self.update_frame()

    def _crop_center_square(self, frame):
        """Crops the center square of a given frame."""
        h, w, _ = frame.shape
        min_dim = min(h, w)
        start_x = (w - min_dim) // 2
        start_y = (h - min_dim) // 2
        return frame[start_y:start_y + min_dim, start_x:start_x + min_dim]

    def update_frame(self):
        """
        Reads a frame, crops it to a square to maintain aspect ratio, and displays it.
        """
        if self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # --- NEW: Crop the raw frame to a square first ---
                square_frame = self._crop_center_square(frame)
                
                # Store the processed (square) frame for capture
                self.current_frame = square_frame.copy() 
                
                # --- Continue with display logic using the square frame ---
                image_rgb = cv2.cvtColor(square_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(image_rgb)
                
                # Resize the square frame to fit the 480x480 UI label
                pil_image_resized = pil_image.resize((self.camera_w, self.camera_h), Image.Resampling.BILINEAR)
                tk_image = ctk.CTkImage(light_image=pil_image_resized, size=(self.camera_w, self.camera_h))
                
                self.camera_label.configure(image=tk_image, text="")
                self.camera_label.image = tk_image 
                
                self.root.after(10, self.update_frame)

    def capture_image(self):
        """Saves the current square frame, cleans up, and navigates to the AnalysisPage."""
        if self.current_frame is not None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"capture_{timestamp}.jpg"
            temp_path = os.path.join(self.save_path, temp_filename)
            
            # --- MODIFIED: Save the already-cropped square frame ---
            cv2.imwrite(temp_path, self.current_frame)
            print(f"📸 Square image captured for analysis: {temp_path}")

            self.cleanup_camera()
            self.root.destroy()
            from Pages.analysis_page import AnalysisPage
            analysis_app = AnalysisPage(image_path=temp_path, view_only=False)
            analysis_app.root.mainloop()
            
    def cleanup_camera(self):
        """Reliably stops the camera feed and releases the camera resource."""
        print("Cleaning up camera resources...")
        self.running = False
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

