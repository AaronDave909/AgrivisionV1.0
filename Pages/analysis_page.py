import customtkinter as ctk
from PIL import Image
import cv2
import os
from ultralytics import YOLO
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH # Import LEFT_PANEL_WIDTH

class AnalysisPage(SC):
    # Constants from CapturePage for reference
    CAPTURE_SIZE = 480 
    ORIGINAL_LEFT_PANEL_WIDTH = LEFT_PANEL_WIDTH 

    def __init__(self, captured_image_path):
        super().__init__()
        
        self.original_image_path = captured_image_path
        self.annotated_image_data = None
        self.gallery_path = "Page_files/gallery_files"
        os.makedirs(self.gallery_path, exist_ok=True)

        # Calculate the target display size based on the 480x480 original size
        self.display_w = self._scale_value(self.CAPTURE_SIZE, 'x')
        self.display_h = self._scale_value(self.CAPTURE_SIZE, 'y')
        
        # --- UI Setup ---
        self.create_left_panel()
        self.create_leaf_image()

        self.save_button(x=53.5, y=480 / 2, command=self.save_annotated_image)
        self.trash_button(command=self.trash_image)
        
        # Initialize the label but defer placement until dimensions are known
        # Pre-set the label size to the calculated scaled dimensions
        self.image_label = ctk.CTkLabel(
            self.root, 
            text="Analyzing...", 
            font=("Arial", 20), 
            fg_color="#1F1F1F", 
            width=self.display_w, 
            height=self.display_h
        )

        # Use root.after to ensure placement happens after the main window is drawn
        self.root.after(100, self._setup_display)


    def _setup_display(self):
        """Places the image label and then runs the analysis."""
        self._place_image_label()
        self.run_yolo_analysis()

    def _place_image_label(self):
        """Calculates and places the image label to align exactly with the top-left corner of the right viewing area."""
        self.root.update_idletasks()
        
        # Calculate the X position, which is the exact width of the left panel
        x_position_next_to_panel = self._scale_value(self.ORIGINAL_LEFT_PANEL_WIDTH, 'x')
        
        # Y position is 0 (top of the window)
        y_position = 0 
        
        self.image_label.place(
            x=x_position_next_to_panel, 
            y=y_position,  
            anchor="nw" # Anchor North-West (top-left) so the image starts at this position
        )
        
    def save_button(self, x, y, command=None):
        """Creates the 'Save' button using an image, placed in the left panel."""
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_width = self._scale_value(90, 'x')
        scaled_height = self._scale_value(90, 'y')
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_hover_offset = self._scale_value(5, 'y')

        save_img = Image.open("_image_assets/save.png")
        save_photo = ctk.CTkImage(light_image=save_img, dark_image=save_img, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root,
            text="", width=scaled_width, height=scaled_height,
            image=save_photo, compound="top", command=command, fg_color="#2A2E3F", hover_color="#2A2E3F",
        )
        btn.place(x=scaled_x, y=scaled_y, anchor="center")

        def on_enter(event):
            btn.place_configure(y=scaled_y - scaled_hover_offset) 
        def on_leave(event):
            btn.place_configure(y=scaled_y) 

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def trash_button(self,command=None):
        """Creates the 'Trash' button using an image, replacing the 'Undo' button."""
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        x, y = 5, 380
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')

        trash_img = Image.open("_image_assets/trash.png")
        trash_photo = ctk.CTkImage(light_image=trash_img, dark_image=trash_img, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root,
            text="", width=scaled_width, height=scaled_height,
            image=trash_photo, compound="top", command=command,
            fg_color="#2A2E3F", hover_color="#2A2E3F", corner_radius=0
        )
        btn.place(x=scaled_x, y=scaled_y)
        btn.image = trash_photo

        def on_enter(event):
            btn.place_configure(y=scaled_y - scaled_hover_offset)
        def on_leave(event):
            btn.place_configure(y=scaled_y)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def run_yolo_analysis(self):
        """Loads the YOLO model and annotates the captured image."""
        try:
            model_path = "Page_files/yolov11_models/diseases.pt" 
            model = YOLO(model_path)
            
            results = model(self.original_image_path)
            self.annotated_image_data = results[0].plot() 
            self.display_image(self.annotated_image_data)
            
        except Exception as e:
            print(f"❌ Error during YOLO analysis: {e}")
            self.image_label.configure(text=f"Error analyzing image.\nModel not found or invalid.\n{e}", text_color="red")

    def display_image(self, image_data_bgr):
        """
        Converts a numpy image array, resizes it to the scaled 480x480 dimensions 
        (self.display_w x self.display_h), and displays it.
        """
        image_rgb = cv2.cvtColor(image_data_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        # Resize the annotated image to match the scaled UI dimensions (self.display_w x self.display_h)
        pil_image_resized = pil_image.resize((self.display_w, self.display_h), Image.Resampling.BILINEAR)
        
        ctk_image = ctk.CTkImage(light_image=pil_image_resized, size=(self.display_w, self.display_h))
        self.image_label.configure(image=ctk_image, text="")
        self.image_label.image = ctk_image

    def save_annotated_image(self):
        if self.annotated_image_data is not None:
            filename = os.path.basename(self.original_image_path)
            save_path = os.path.join(self.gallery_path, filename)
            cv2.imwrite(save_path, self.annotated_image_data)
            print(f"✅ Annotated image saved to: {save_path}")
            os.remove(self.original_image_path)
            self.return_to_capture()

    def trash_image(self):
        if os.path.exists(self.original_image_path):
            os.remove(self.original_image_path)
            print(f"🗑️ Image trashed: {self.original_image_path}")
        self.return_to_capture()

    def return_to_capture(self):
        self.root.destroy()
        from Pages.capture import CapturePage 
        capture_app = CapturePage()
        capture_app.root.mainloop()
