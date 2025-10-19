import customtkinter as ctk
from PIL import Image
import cv2
import os
from ultralytics import YOLO
from shared_components import SharedComponents as SC

class AnalysisPage(SC):
    def __init__(self, captured_image_path):
        super().__init__()
        
        # Store paths and the annotated image data
        self.original_image_path = captured_image_path
        self.annotated_image_data = None
        self.gallery_path = "Page_files/gallery_files"
        os.makedirs(self.gallery_path, exist_ok=True)
        
        # --- UI Setup ---
        self.create_left_panel()
        self.create_leaf_image()
        # The undo button will now just return to the capture page
        self.undo_button(command=self.trash_image) 
        
        # Label to display the annotated image
        self.image_label = ctk.CTkLabel(self.root, text="Analyzing...", font=ctk.CTkFont(size=20))
        self.image_label.pack(pady=40, padx=60, expand=True, fill="both")
        
        # Frame for action buttons
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=20)
        
        # Save Button
        self.save_button = ctk.CTkButton(button_frame, text="Save Annotated Image", command=self.save_annotated_image, height=40)
        self.save_button.pack(side="left", padx=10)
        
        # Trash Button
        self.trash_button = ctk.CTkButton(button_frame, text="Trash Image", command=self.trash_image, fg_color="#D32F2F", hover_color="#B71C1C", height=40)
        self.trash_button.pack(side="left", padx=10)
        
        # Run the model immediately after setting up the UI
        self.run_yolo_analysis()

    def run_yolo_analysis(self):
        """Loads the YOLO model and annotates the captured image."""
        try:
            model_path = "Page_files/yolov11_models/diseases.pt"
            model = YOLO(model_path)
            
            # Run inference
            results = model(self.original_image_path)
            
            # Use the .plot() method which returns a BGR numpy array with annotations
            self.annotated_image_data = results[0].plot() 
            
            # Display the annotated image
            self.display_image(self.annotated_image_data)
            
        except Exception as e:
            print(f"❌ Error during YOLO analysis: {e}")
            self.image_label.configure(text=f"Error analyzing image.\nModel not found or invalid.\n{e}", text_color="red")

    def display_image(self, image_data_bgr):
        """Converts a numpy image array (BGR) and displays it in the CTkLabel."""
        # Convert from OpenCV's BGR format to RGB for PIL
        image_rgb = cv2.cvtColor(image_data_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        # Create CTkImage and display it
        ctk_image = ctk.CTkImage(light_image=pil_image, size=(pil_image.width, pil_image.height))
        self.image_label.configure(image=ctk_image, text="")
        self.image_label.image = ctk_image

    def save_annotated_image(self):
        """Saves the annotated image to the gallery and returns to the capture page."""
        if self.annotated_image_data is not None:
            filename = os.path.basename(self.original_image_path)
            save_path = os.path.join(self.gallery_path, filename)
            
            # Save the image using OpenCV
            cv2.imwrite(save_path, self.annotated_image_data)
            print(f"✅ Annotated image saved to: {save_path}")
            
            # Clean up the original un-annotated image
            os.remove(self.original_image_path)
            
            self.return_to_capture()

    def trash_image(self):
        """Deletes the original captured image and returns to the capture page."""
        if os.path.exists(self.original_image_path):
            os.remove(self.original_image_path)
            print(f"🗑️ Image trashed: {self.original_image_path}")
        
        self.return_to_capture()

    def return_to_capture(self):
        """Closes the current page and re-opens the CapturePage."""
        self.root.destroy()
        from Pages.capture import CapturePage  # Local import to avoid circular dependency
        capture_app = CapturePage()
        capture_app.root.mainloop()
