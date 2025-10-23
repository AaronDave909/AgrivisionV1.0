import customtkinter as ctk
from PIL import Image
import cv2
import os
from ultralytics import YOLO
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH
import datetime
import json  # NEW: Import json

class AnalysisPage(SC):
    CAPTURE_SIZE = 480
    ORIGINAL_LEFT_PANEL_WIDTH = LEFT_PANEL_WIDTH

    # __init__ now accepts an image_path and an optional view_only flag
    def __init__(self, image_path, view_only=False):
        super().__init__()

        self.image_path = image_path
        self.view_only = view_only
        self.analysis_data_dict = {}  # NEW: To store data for saving
        self.annotated_image_data = None
        self.gallery_path = "Page_files/gallery_files"
        self.single_json_path = os.path.join(self.gallery_path, "gallery_data.json")
        os.makedirs(self.gallery_path, exist_ok=True)

        self.display_w = self._scale_value(self.CAPTURE_SIZE, 'x')
        self.display_h = self._scale_value(self.CAPTURE_SIZE, 'y')

        # --- UI Setup ---
        self.create_left_panel()
        self.create_leaf_image()
        self._create_info_panel() # Create info panel first

        if self.view_only:
            # In view-only mode
            # undo button
            self.undo_button(command=self.return_to_gallery)
            
            # trash button
            self.trash_button(command=self.delete_gallery_entry, y_offset=195)
            # Set image label text for loading
            initial_text = "Loading..."
        else:
            # In analysis mode, show "save" and "trash" (discard) buttons
            self.original_image_path = image_path # Use a specific name for clarity
            self.save_button(x=53.5, y=480 / 2, command=self.save_annotated_image)
            self.trash_button(command=self.trash_image)
            # Set image label text for analyzing
            initial_text = "Analyzing..."

        self.image_label = ctk.CTkLabel(
            self.root, text=initial_text, font=("Arial", 20),
            fg_color="#1F1F1F", width=self.display_w, height=self.display_h
        )

        self.root.after(100, self._setup_display)

    def _load_master_json(self):
        """Loads the master JSON file. Returns an empty dict if it doesn't exist."""
        try:
            if os.path.exists(self.single_json_path):
                with open(self.single_json_path, 'r') as f:
                    # Handle empty file case
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
            else:
                return {} # Return an empty dictionary if file doesn't exist
        except (json.JSONDecodeError, Exception) as e:
            print(f"❌ Error reading master JSON or file is empty: {e}. Returning empty dict.")
            return {}

    def _save_master_json(self, data):
        """Saves the provided dictionary to the master JSON file."""
        try:
            with open(self.single_json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"❌ Error writing master JSON: {e}")

    def _setup_display(self):
        """Places the UI elements and then runs the correct process."""
        self._place_ui_elements()
        
        # MODIFIED: Run different functions based on mode
        if self.view_only:
            self.load_and_display_data()
        else:
            self.run_yolo_analysis()

    def _create_info_panel(self):
        """Creates the frame and labels for displaying analysis results."""
        info_panel_w = self._scale_value(213, 'x')
        info_panel_h = self._scale_value(480, 'y')

        self.info_frame = ctk.CTkFrame(self.root, width=info_panel_w, height=info_panel_h, fg_color="#2A2E3F")
        self.info_frame.pack_propagate(False) # Prevent the frame from shrinking to fit widgets

        # Title Label
        title = ctk.CTkLabel(self.info_frame, text="Analysis Results", font=ctk.CTkFont(size=20, weight="bold"), text_color="white")
        title.pack(pady=(20, 15), padx=10)

        # Helper function to create uniform label pairs
        def create_info_row(parent, label_text):
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
            label = ctk.CTkLabel(row_frame, text=f"{label_text}:", font=ctk.CTkFont(size=14, weight="bold"), text_color="white", anchor="w")
            label.pack(side="left", padx=(10, 5))
            value_label = ctk.CTkLabel(row_frame, text="---", font=ctk.CTkFont(size=14), anchor="w", text_color="white")
            value_label.pack(side="left", expand=True, fill="x", padx=5)
            row_frame.pack(fill="x", pady=8)
            return value_label

        self.disease_label = create_info_row(self.info_frame, "Disease")
        self.accuracy_label = create_info_row(self.info_frame, "Accuracy")
        self.count_label = create_info_row(self.info_frame, "Detections")
        self.datetime_label = create_info_row(self.info_frame, "Timestamp")

    def _place_ui_elements(self):
        """Calculates and places the image label and the info panel."""
        self.root.update_idletasks()
        
        x_pos_image = self._scale_value(self.ORIGINAL_LEFT_PANEL_WIDTH, 'x')
        self.image_label.place(x=x_pos_image, y=0, anchor="nw")
        
        # Place the info panel to the right of the image
        x_pos_info = x_pos_image + self.display_w
        self.info_frame.place(x=x_pos_info, y=0, anchor="nw")

    def save_button(self, x, y, command=None):
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_width = self._scale_value(90, 'x')
        scaled_height = self._scale_value(90, 'y')
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_hover_offset = self._scale_value(5, 'y')

        save_img = Image.open("_image_assets/save.png")
        save_photo = ctk.CTkImage(light_image=save_img, dark_image=save_img, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root, text="", width=scaled_width, height=scaled_height,
            image=save_photo, compound="top", command=command, fg_color="#2A2E3F", hover_color="#2A2E3F",
        )
        btn.place(x=scaled_x, y=scaled_y, anchor="center")

        def on_enter(event): btn.place_configure(y=scaled_y - scaled_hover_offset) 
        def on_leave(event): btn.place_configure(y=scaled_y) 

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def trash_button(self,command=None, y_offset=None):
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        x, y = 5, 380

        if y_offset is not None:
            y = y_offset
        
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')

        trash_img = Image.open("_image_assets/trash.png")
        trash_photo = ctk.CTkImage(light_image=trash_img, dark_image=trash_img, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root, text="", width=scaled_width, height=scaled_height,
            image=trash_photo, compound="top", command=command,
            fg_color="#2A2E3F", hover_color="#2A2E3F", corner_radius=0
        )
        btn.place(x=scaled_x, y=scaled_y)
        btn.image = trash_photo

        def on_enter(event): btn.place_configure(y=scaled_y - scaled_hover_offset)
        def on_leave(event): btn.place_configure(y=scaled_y)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def run_yolo_analysis(self):
        try:
            model_path = "Page_files/yolov11_models/diseases.pt"
            model = YOLO(model_path)
            results = model(self.original_image_path)

            self.annotated_image_data = results[0].plot()
            self.display_image(self.annotated_image_data)

            # MODIFIED: Call the refactored update function
            self.update_info_panel(results)

        except Exception as e:
            print(f"❌ Error during YOLO analysis: {e}")
            self.image_label.configure(text=f"Error analyzing image.", text_color="red")
            self.disease_label.configure(text="Analysis Failed")
            self.accuracy_label.configure(text="---")
            self.count_label.configure(text="---")

    def update_info_panel(self, results):
        """Extracts data from YOLO results and populates the panel."""
        now = datetime.datetime.now()
        timestamp = now.strftime("%b %d, %Y %I:%M %p")

        if len(results[0].boxes) > 0:
            top_detection = results[0].boxes[0]
            disease_name = results[0].names[int(top_detection.cls)]
            accuracy = f"{top_detection.conf.item()*100:.2f}%"
            detection_count = str(len(results[0].boxes))
        else:
            disease_name = "No Disease Detected"
            accuracy = "N/A"
            detection_count = "0"
            
        # NEW: Store data in the class dictionary
        self.analysis_data_dict = {
            "disease": disease_name,
            "accuracy": accuracy,
            "count": detection_count,
            "timestamp": timestamp
        }
        
        # Call a separate function to update labels
        self.populate_info_panel(self.analysis_data_dict)

    # This function just updates the labels from a dictionary
    def populate_info_panel(self, data_dict):
        """Populates the info panel labels from a given data dictionary."""
        self.disease_label.configure(text=data_dict.get("disease", "---"))
        self.accuracy_label.configure(text=data_dict.get("accuracy", "---"))
        self.count_label.configure(text=data_dict.get("count", "---"))
        self.datetime_label.configure(text=data_dict.get("timestamp", "---"))

    def load_and_display_data(self):
        """Loads annotated image and analysis data from the master JSON."""
        try:
            # self.image_path is the full path, e.g., "gallery/img1.jpg"
            # We need just the filename to use as the key
            image_filename = os.path.basename(self.image_path)

            if not os.path.exists(self.image_path):
                print(f"❌ Error: Missing image file.")
                self.image_label.configure(text="Error: File not found.", text_color="red")
                return

            # Load and display the annotated image (unchanged)
            self.annotated_image_data = cv2.imread(self.image_path)
            self.display_image(self.annotated_image_data)

            # --- MODIFIED: JSON Loading Logic ---
            
            # 1. Load the master dictionary
            master_data = self._load_master_json()
            
            # 2. Find the data for this specific image using its filename as the key
            image_specific_data = master_data.get(image_filename)

            # 3. Populate the panel
            if image_specific_data:
                self.populate_info_panel(image_specific_data)
            else:
                # This case handles if the image exists but its data is missing from the JSON
                print(f"❌ Error: No data found for {image_filename} in {self.single_json_path}")
                self.populate_info_panel({}) # Pass empty dict to clear labels

        except Exception as e:
            print(f"❌ Error loading gallery data: {e}")
            self.image_label.configure(text="Error loading data.", text_color="red")

    def display_image(self, image_data_bgr):
        image_rgb = cv2.cvtColor(image_data_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        pil_image_resized = pil_image.resize((self.display_w, self.display_h), Image.Resampling.BILINEAR)
        ctk_image = ctk.CTkImage(light_image=pil_image_resized, size=(self.display_w, self.display_h))
        self.image_label.configure(image=ctk_image, text="")
        self.image_label.image = ctk_image

    def save_annotated_image(self):
        if self.annotated_image_data is not None:
            filename = os.path.basename(self.original_image_path)
            base_filename = os.path.splitext(filename)[0]
            
            image_filename = f"{base_filename}.jpg"
            save_path_img = os.path.join(self.gallery_path, image_filename)

            try:
                # Save the image (this is unchanged)
                cv2.imwrite(save_path_img, self.annotated_image_data)
                print(f"✅ Annotated image saved to: {save_path_img}")
                
                # --- MODIFIED: JSON Saving Logic ---
                
                # 1. Load the master dictionary
                master_data = self._load_master_json()
                
                # 2. Add or update the entry for this image
                # The key is the image filename
                master_data[image_filename] = self.analysis_data_dict
                
                # 3. Save the master dictionary back to the file
                self._save_master_json(master_data)
                print(f"✅ Analysis data updated in: {self.single_json_path}")

                # Clean up the original capture
                os.remove(self.original_image_path)
                self.return_to_capture()

            except Exception as e:
                print(f"❌ Error saving files: {e}")

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

    def delete_gallery_entry(self):
        """Deletes the .jpg and its corresponding entry from the master .json file."""
        try:
            # Get the filename to use as the key
            image_filename = os.path.basename(self.image_path)
            
            # 1. Delete the image file
            if os.path.exists(self.image_path):
                os.remove(self.image_path)
                print(f"🗑️ Deleted image: {self.image_path}")
            
            # --- MODIFIED: JSON Deletion Logic ---
            
            # 2. Load the master dictionary
            master_data = self._load_master_json()
            
            # 3. Remove the entry for this image (if it exists)
            if image_filename in master_data:
                del master_data[image_filename]
                print(f"🗑️ Deleted data for {image_filename} from {self.single_json_path}")
                
                # 4. Save the modified master dictionary
                self._save_master_json(master_data)
            else:
                print(f"⚠️ Warning: No data found for {image_filename} in master JSON. Only image was deleted.")
                
        except Exception as e:
            print(f"❌ Error deleting files: {e}")
        
        self.return_to_gallery() # Go back to gallery after deleting

    # Function to return to the gallery
    def return_to_gallery(self):
        self.root.destroy()
        # MODIFIED: Ensure correct import path for your project
        from Pages.gallery import GalleryPage 
        gallery_app = GalleryPage()
        gallery_app.root.mainloop()