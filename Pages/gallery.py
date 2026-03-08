import customtkinter as ctk
from PIL import Image
from shared_components import BG_COLOR, SharedComponents as SC, custom_font_regular
import os
import random
import json
from Pages.analysis_page import AnalysisPage 
from shared_components import (
    custom_font_bold, custom_font_title, custom_font_regular, 
    BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR, LEFT_PANEL_COLOR
)
# --- FIX for UnicodeEncodeError ---
import sys
import io
# Forces stdout to use UTF-8 encoding for Unicode characters (like emojis)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# --- End of fix ---


# --- No changes to gallery_preview function ---
def gallery_preview(root):
    
    if hasattr(root, 'scale_x') and hasattr(root, 'scale_y'):
        scale_x = root.scale_x
        scale_y = root.scale_y
    else:
        scale_x = 1.1
        scale_y = 1.1

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

            scaled_img_size = scale_val(ORIGINAL_IMG_SIZE, 'x')
            
            img = Image.open(img_path)
            img = img.resize((scaled_img_size, scaled_img_size))
            gallery_photo = ctk.CTkImage(light_image=img, dark_image=img, size=(scaled_img_size, scaled_img_size))

            file_label = os.path.splitext(random_image)[0]
        else:
            file_label = "No Images" 
            print("No JPG images found in Page_files/gallery_files.")
    else:
        file_label = "Gallery Empty" 
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

        # --- MODIFIED: Setup state variables ---
        self.current_filter = "All Captures" # Default filter
        self.gallery_folder_path = "Page_files/gallery_files"
        self.master_json_path = os.path.join(self.gallery_folder_path, "gallery_data.json")

        # --- MODIFIED: Create top-right filter dropdown ---
        filter_options = self._get_available_filters()
        
        self.filter_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.filter_frame.place(
            relx=0.90, 
            y=self._scale_value(25, 'y'), 
            anchor="ne" # Top-right anchor
        )
        
        self.filter_label = ctk.CTkLabel(
            self.filter_frame, 
            text="Filter by:",
            font=("Arial", self._scale_value(14, 'y')),
            text_color=TEXT_COLOR
        )
        self.filter_label.pack(side="left", padx=(5, 5))

        # Unpack the colors for the dropdown menu
        current_mode = ctk.get_appearance_mode()
        menu_bg = BUTTON_COLOR[0] if current_mode == "Light" else BUTTON_COLOR[1]
        menu_text = TEXT_COLOR[0] if current_mode == "Light" else TEXT_COLOR[1]
        menu_hover = BUTTON_HOVER[0] if current_mode == "Light" else BUTTON_HOVER[1]

        self.filter_selector = ctk.CTkOptionMenu(
            self.filter_frame,
            values=filter_options, 
            command=self.on_filter_selected,
            font=("Arial", self._scale_value(14, 'y')),
            dropdown_font=("Arial", self._scale_value(20, 'y')),
            
            fg_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            button_color=BUTTON_HOVER,
            button_hover_color=("#C1C3C8", "#50556b"), 
            
            dropdown_fg_color=menu_bg,          
            dropdown_hover_color=menu_hover,    
            dropdown_text_color=menu_text       
        )
        self.filter_selector.set(self.current_filter)
        self.filter_selector.pack(side="left", padx=(0, 10))
        # --- End of new dropdown code ---
        
        self.create_scrollable_gallery()
        
    def _format_name(self, name_str):
        """Converts snake_case names into formatted Title Case."""
        if name_str is None:
            return ""
        if name_str == "Downy_mildew_on_lettuce":
            return "Downy Mildew"
        if name_str == "Powdery_mildew_on_lettuce":
            return "Powdery Mildew"
        
        return name_str.replace("_", " ").title()

    # --- NEW: Function to get all filter names for the dropdown ---
    def _get_available_filters(self):
        """Loads all unique disease/pest types for the filter dropdown."""
        
        master_data = self._load_master_json(self.master_json_path)
        all_names = set()
        for item_data in master_data.values():
            name = item_data.get("disease") or item_data.get("pest")
            if name and name != "No Disease Detected":
                all_names.add(self._format_name(name))
        
        sorted_names = sorted(list(all_names))
        
        # Create the final list, starting with "All Captures"
        filter_list = ["All Captures"]
        filter_list.extend(sorted_names)
        
        return filter_list

    # --- NEW: Function called by the dropdown ---
    def on_filter_selected(self, selected_name: str):
        """Sets the current filter and rebuilds the gallery."""
        self.current_filter = selected_name
        self.apply_filter()

    # --- NEW: Refactored filter logic ---
    def apply_filter(self):
        """Clears and rebuilds the gallery based on self.current_filter."""
        # 1. Clear the existing gallery
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        # 2. Re-load images with the new filter
        self.load_gallery_images(self.gallery_folder_path)

    def create_scrollable_gallery(self):
        scaled_x_start = self.scale_x_val(120)
        scaled_scrollbar_width = self.scale_x_val(40)
        
        # --- FIX: Unpack tuples for standard tkinter components ---
        current_mode = ctk.get_appearance_mode()
        # Extract single hex strings from your tuples
        self.unpacked_bg = BG_COLOR[0] if current_mode == "Light" else BG_COLOR[1]
        self.unpacked_btn = BUTTON_COLOR[0] if current_mode == "Light" else BUTTON_COLOR[1]
        self.unpacked_hover = BUTTON_HOVER[0] if current_mode == "Light" else BUTTON_HOVER[1]

        # 1. The Canvas
        self.canvas = ctk.CTkCanvas(
            self.root,
            bg=self.unpacked_bg,        # <--- FIX: Use unpacked hex string
            highlightthickness=0
        )
        self.canvas.place(x=scaled_x_start, y=self.scale_y_val(60), relwidth=0.84, relheight=0.85)

        # 2. The Scrollbar
        self.scrollbar = ctk.CTkScrollbar(
            self.root,
            orientation="vertical",
            command=self.canvas.yview,
            width=scaled_scrollbar_width,  
            fg_color=self.unpacked_bg,      # <--- FIX: Use unpacked hex string
            button_color=self.unpacked_btn, # <--- FIX: Use unpacked hex string
            button_hover_color=self.unpacked_hover, 
        )
        self.scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne") 

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 3. The Inner Frame
        # CTkFrame usually handles tuples, but inside a Canvas window, 
        # it's safer to use the unpacked hex.
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color=self.unpacked_bg)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Load the gallery images
        self.load_gallery_images(self.gallery_folder_path)

    def _load_master_json(self, json_path):
        """Loads the master JSON file. Returns an empty dict if it doesn't exist."""
        try:
            # Use encoding='utf-8' for reading the JSON file as well
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
            else:
                return {} 
        except (json.JSONDecodeError, Exception) as e:
            print(f"❌ Error reading master JSON or file is empty: {e}. Returning empty dict.")
            return {}

    # --- MODIFIED: This function now uses self.current_filter ---
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

        # 1. Load the master JSON file
        master_data = self._load_master_json(self.master_json_path)

        if not master_data:
            print("⚠️ Warning: gallery_data.json is empty or not found. No items will be loaded.")
            return
            
        # 2. Get all .jpg files
        jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
        if not jpg_files:
            print("No JPG images found.")
            return

        scaled_name_font = tuple(custom_font_regular)

        # 3. We need a new index variable to handle grid placement
        valid_image_index = 0

        # Loop through all .jpg files found
        for filename in jpg_files:
            file_path = os.path.join(folder_path, filename)
            
            # 4. Check if the image filename is a key in the master JSON
            if filename not in master_data:
                # This print statement is now safe because of the fix at the top
                print(f"⚠️ Warning: No data for {filename} in master JSON. Skipping.")
                continue 

            # --- 5. MODIFIED: Apply the filter ---
            item_data = master_data[filename]
            
            if self.current_filter != "All Captures":
                # Get the formatted name from the JSON data
                raw_name = item_data.get("disease") or item_data.get("pest")
                formatted_name = self._format_name(raw_name)
                
                # If it doesn't match the filter, skip this image
                if formatted_name != self.current_filter:
                    continue
            # --- End of filter logic ---

            # Load and resize image
            img = Image.open(file_path)
            img = img.resize((image_width, image_height))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(image_width, image_height))

            # Use the new valid_image_index for grid placement
            col = valid_image_index % max_per_row
            row = valid_image_index // max_per_row
            
            valid_image_index += 1 # Increment index ONLY for valid images

            # 1. Create the container frame
            frame = ctk.CTkFrame(
                self.scrollable_frame, 
                width=panel_width, 
                height=panel_height, 
                fg_color=self.unpacked_bg, # This is where you were pasting the color
                corner_radius=self.scale_x_val(10)
            )
            # 2. Add this line to LOCK the size
            frame.grid_propagate(False) 
            
            # 3. Use 'sticky' to ensure it fills the grid slot
            frame.grid(row=row, column=col, padx=spacing, pady=spacing, sticky="nsew")

            # Image button
            img_button = ctk.CTkButton(
                frame,
                image=ctk_img,
                text="",
                width=image_width,
                height=image_height,
                fg_color=BUTTON_COLOR,
                hover_color=BUTTON_HOVER,
                command=lambda path=file_path: self.open_analysis_view(path)
            )
            img_button.image = ctk_img
            img_button.place(relx=0.5, rely=0.45, anchor="center")

            # Filename label
            name = os.path.splitext(filename)[0]
            name_label = ctk.CTkLabel(
                frame, 
                text=name, 
                text_color=TEXT_COLOR, 
                font=scaled_name_font 
            )
            name_label.place(relx=0.5, rely=0.9, anchor="center")

    def open_analysis_view(self, image_path):
        """Destroys the gallery and opens the analysis page in view-only mode."""
        self.root.destroy()
        app = AnalysisPage(image_path=image_path, view_only=True)
        app.root.mainloop()
