import customtkinter as ctk
from PIL import Image
from shared_components import SharedComponents as SC, custom_font_regular
import os
import random
import json  # NEW: Import json
# NEW: Import the analysis page to switch to it
from Pages.analysis_page import AnalysisPage 

# ... (No changes to gallery_preview function) ...
def gallery_preview(root):
    
    if hasattr(root, 'scale_x') and hasattr(root, 'scale_y'):
        scale_x = root.scale_x
        scale_y = root.scale_y
    else:
        scale_x = 1
        scale_y = 1

    def scale_val(value, axis='x'):
        factor = scale_x if axis == 'x' else scale_y
        return round(value * factor)

    gallery_folder = "Page_files/gallery_files"
    random_image = None
    gallery_photo = None
    file_label = ""
    ORIGINAL_IMG_SIZE = 168

    if os.path.exists(gallery_folder):
        jpg_files = [f for f in os.listdir(gallery_folder) if f.lower().endswith(".jpg")]
        if jpg_files:
            random_image = random.choice(jpg_files)
            img_path = os.path.join(gallery_folder, random_image)

            # Scale image size
            scaled_img_size = scale_val(ORIGINAL_IMG_SIZE, 'x')
            
            # Load & resize the image
            img = Image.open(img_path)
            img = img.resize((scaled_img_size, scaled_img_size))
            gallery_photo = ctk.CTkImage(light_image=img, dark_image=img, size=(scaled_img_size, scaled_img_size))

            # Extract filename (without extension)
            file_label = os.path.splitext(random_image)[0]
        else:
            file_label = "No Images" # Show label if folder exists but no images
            print("No JPG images found in Page_files/gallery_files.")
    else:
        file_label = "Gallery Empty" # Show label if folder not found
        print(f"Folder '{gallery_folder}' not found.")

    return gallery_photo, file_label


class GalleryPage(SC):
    def __init__(self):
        super().__init__()
        self.root.update_idletasks()
        self.create_title(text="Capture Gallery", x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        self.undo_button(command=self.go_back_to_dashboard)
        
        self.scale_x_val = lambda val: self._scale_value(val, 'x')
        self.scale_y_val = lambda val: self._scale_value(val, 'y')

        self.create_scrollable_gallery()
        
    # ... (No changes to create_scrollable_gallery) ...
    def create_scrollable_gallery(self):
        
        scaled_x_start = self.scale_x_val(120)
        scaled_scrollbar_width = self.scale_x_val(40)
        

        self.canvas = ctk.CTkCanvas(
            self.root,
            bg="#202332",
            highlightthickness=0
        )
        self.canvas.place(x=scaled_x_start, y=self.scale_y_val(60), relwidth=0.84, relheight=0.85)

        self.scrollbar = ctk.CTkScrollbar(
            self.root,
            orientation="vertical",
            command=self.canvas.yview,
            width=scaled_scrollbar_width,  
            fg_color="#222533",   
            button_color="#4C516D",  
            button_hover_color="#6A7090", 
        )
        self.scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne") 

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color="#202332")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Load the gallery images
        self.load_gallery_images()

    # NEW: Add the helper function to load the master JSON
    def _load_master_json(self, json_path):
        """Loads the master JSON file. Returns an empty dict if it doesn't exist."""
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
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

    def load_gallery_images(self, folder_path="Page_files/gallery_files"):
        
        ORIGINAL_PANEL_WIDTH = 197.33
        ORIGINAL_PANEL_HEIGHT = 190.45
        ORIGINAL_IMAGE_WIDTH = 141
        ORIGINAL_IMAGE_HEIGHT = 146
        ORIGINAL_SPACING = 10
        
        panel_width = self.scale_x_val(ORIGINAL_PANEL_WIDTH)
        panel_height = self.scale_y_val(ORIGINAL_PANEL_HEIGHT)
        image_width = self.scale_x_val(ORIGINAL_IMAGE_WIDTH)
        image_height = self.scale_y_val(ORIGINAL_IMAGE_HEIGHT)
        spacing = self.scale_x_val(ORIGINAL_SPACING) 

        max_per_row = 3

        if not os.path.exists(folder_path):
            print(f"Folder '{folder_path}' not found.")
            return

        # --- MODIFIED: JSON Loading Logic ---
        
        # 1. Define and load the master JSON file
        master_json_path = os.path.join(folder_path, "gallery_data.json")
        master_data = self._load_master_json(master_json_path)

        if not master_data:
            print("⚠️ Warning: gallery_data.json is empty or not found. No items will be loaded.")
            # We can just return here, as no images should be shown
            # if their data doesn't exist.
            return
            
        # 2. Get all .jpg files
        jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
        if not jpg_files:
            print("No JPG images found.")
            return

        scaled_name_font = tuple(custom_font_regular)

        # 3. We need a new index variable to handle grid placement
        #    since some images might be skipped.
        valid_image_index = 0

        # MODIFIED: Loop through all .jpg files found
        for filename in jpg_files:
            file_path = os.path.join(folder_path, filename)
            
            # 4. MODIFIED: Check if the image filename is a key in the master JSON
            if filename not in master_data:
                print(f"⚠️ Warning: No data for {filename} in master JSON. Skipping.")
                continue # Skip this file as it has no data

            # --- End of modifications ---

            # Load and resize image
            img = Image.open(file_path)
            img = img.resize((image_width, image_height))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(image_width, image_height))

            # MODIFIED: Use the new valid_image_index for grid placement
            col = valid_image_index % max_per_row
            row = valid_image_index // max_per_row
            
            valid_image_index += 1 # Increment index ONLY for valid images

            frame = ctk.CTkFrame(
                self.scrollable_frame, 
                width=panel_width, 
                height=panel_height, 
                fg_color="#2A2E3F", 
                corner_radius=self.scale_x_val(10)
            )
            frame.grid(row=row, column=col, padx=spacing, pady=spacing)

            # Image button
            img_button = ctk.CTkButton(
                frame,
                image=ctk_img,
                text="",
                width=image_width,
                height=image_height,
                fg_color="transparent",
                hover_color="#3B3F51",
                # This command is still correct
                command=lambda path=file_path: self.open_analysis_view(path)
            )
            img_button.image = ctk_img
            img_button.place(relx=0.5, rely=0.45, anchor="center")

            # Filename label
            name = os.path.splitext(filename)[0]
            name_label = ctk.CTkLabel(
                frame, 
                text=name, 
                text_color="white", 
                font=scaled_name_font 
            )
            name_label.place(relx=0.5, rely=0.9, anchor="center")

    # NEW: Function to switch from Gallery to Analysis page
    def open_analysis_view(self, image_path):
        """Destroys the gallery and opens the analysis page in view-only mode."""
        self.root.destroy()
        # Pass the path to the image and set view_only=True
        app = AnalysisPage(image_path=image_path, view_only=True)
        app.root.mainloop()