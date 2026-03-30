import customtkinter as ctk
from PIL import Image
from shared_components import BG_COLOR, SharedComponents as SC, custom_font_regular, LEFT_PANEL_WIDTH
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
    # --- NEW: Class variables to remember filter state across page reloads ---
    saved_category = "All"
    saved_sub = "All"

    def __init__(self):
        super().__init__()
        self.root.update_idletasks()
        self.create_title(text="Capture Gallery", x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        self.create_battery_indicator(x=15, y=100)
        self.undo_button(command=self.go_back_to_dashboard)
        
        self.scale_x_val = lambda val: self._scale_value(val, 'x')
        self.scale_y_val = lambda val: self._scale_value(val, 'y')

        self.gallery_folder_path = "Page_files/gallery_files"
        self.master_json_path = os.path.join(self.gallery_folder_path, "gallery_data.json")

        # --- Setup Left Panel Dual Dropdowns ---
        menu_bg = self._get_color(BUTTON_COLOR)
        menu_text = self._get_color(TEXT_COLOR)
        menu_hover = self._get_color(BUTTON_HOVER)

        # 1. Category Dropdown
        self.category_label = ctk.CTkLabel(
            self.left_panel, text="Category:", font=("Arial", self._scale_value(12, 'y'), "bold"), text_color=self._get_color(TEXT_COLOR)
        )
        self.category_label.place(x=self._scale_value(LEFT_PANEL_WIDTH / 2, 'x'), y=self._scale_value(150, 'y'), anchor="center")

        self.category_var = ctk.StringVar(value=GalleryPage.saved_category)
        self.category_dropdown = ctk.CTkOptionMenu(
            self.left_panel,
            values=["All", "Deficiencies", "Diseases", "Pests"],
            variable=self.category_var,
            command=self.on_category_changed,
            font=("Arial", self._scale_value(12, 'y')),
            dropdown_font=("Arial", self._scale_value(14, 'y')),
            width=self._scale_value(100, 'x'),
            fg_color=self._get_color(BUTTON_COLOR),
            text_color=self._get_color(TEXT_COLOR),
            button_color=self._get_color(BUTTON_HOVER),
            button_hover_color=self._get_color(BUTTON_HOVER),
            dropdown_fg_color=menu_bg,
            dropdown_hover_color=menu_hover,
            dropdown_text_color=menu_text
        )
        self.category_dropdown.place(x=self._scale_value(LEFT_PANEL_WIDTH / 2, 'x'), y=self._scale_value(180, 'y'), anchor="center")

        # 2. Sub-filter Dropdown
        self.sub_label = ctk.CTkLabel(
            self.left_panel, text="Filter:", font=("Arial", self._scale_value(12, 'y'), "bold"), text_color=self._get_color(TEXT_COLOR)
        )
        self.sub_label.place(x=self._scale_value(LEFT_PANEL_WIDTH / 2, 'x'), y=self._scale_value(230, 'y'), anchor="center")

        # --- Ensure the sub-dropdown has the correct list of options on reload ---
        initial_sub_values = ["All"]
        if GalleryPage.saved_category == "Deficiencies":
            initial_sub_values = ["All", "Calcium", "Magnesium", "Nitrogen", "Potassium", "Phosphorus"]
        elif GalleryPage.saved_category == "Diseases":
            initial_sub_values = ["All", "Downy Mildew", "Powdery Mildew", "Bacterial", "Lettuce Mosaic Virus"]
        elif GalleryPage.saved_category == "Pests": # <-- NEW: Pests sub-menu
            initial_sub_values = ["All", "Aphids", "Caterpillars", "Slugs", "Droplets"]

        self.sub_var = ctk.StringVar(value=GalleryPage.saved_sub)
        self.sub_dropdown = ctk.CTkOptionMenu(
            self.left_panel,
            values=initial_sub_values,
            variable=self.sub_var,
            command=self.on_sub_changed,
            font=("Arial", self._scale_value(12, 'y')),
            dropdown_font=("Arial", self._scale_value(14, 'y')),
            width=self._scale_value(100, 'x'),
            fg_color=self._get_color(BUTTON_COLOR),
            text_color=self._get_color(TEXT_COLOR),
            button_color=self._get_color(BUTTON_HOVER),
            button_hover_color=self._get_color(BUTTON_HOVER),
            dropdown_fg_color=menu_bg,
            dropdown_hover_color=menu_hover,
            dropdown_text_color=menu_text
        )
        self.sub_dropdown.place(x=self._scale_value(LEFT_PANEL_WIDTH / 2, 'x'), y=self._scale_value(260, 'y'), anchor="center")

        self.create_scrollable_gallery()
        
    def _format_name(self, name_str):
        """Converts raw JSON names into clean, readable Title Case."""
        if not name_str:
            return ""
            
        name_str = name_str.replace("_", " ").title()
        
        # Specific cleanups based on the JSON file
        replacements = {
            "N Deficiency": "Nitrogen Deficiency",
            "P Deficiency": "Phosphorus Deficiency",
            "K Deficiency": "Potassium Deficiency",
            "Ca Deficiency": "Calcium Deficiency",
            "Mg Deficiency": "Magnesium Deficiency",
            "Downy Mildew On Lettuce": "Downy Mildew",
            "Powdery Mildew On Lettuce": "Powdery Mildew",
            "Bacterial": "Bacterial Leaf Spot"
        }
        
        for old, new in replacements.items():
            name_str = name_str.replace(old, new)
            
        return name_str.strip()

    def on_category_changed(self, choice):
        """Updates the choices in the second dropdown based on the first dropdown."""
        GalleryPage.saved_category = choice # Save the state
        
        if choice == "All":
            new_values = ["All"]
        elif choice == "Deficiencies":
            new_values = ["All", "Calcium", "Magnesium", "Nitrogen", "Potassium", "Phosphorus"]
        elif choice == "Diseases":
            new_values = ["All", "Downy Mildew", "Powdery Mildew", "Bacterial", "Lettuce Mosaic Virus"]
        elif choice == "Pests":
            new_values = ["All", "Aphids", "Caterpillars", "Slugs", "Droplets"] # <-- NEW: Added options
            
        self.sub_dropdown.configure(values=new_values)
        self.sub_var.set("All")
        GalleryPage.saved_sub = "All" # Reset the sub-filter memory when category changes
        self.apply_filter()

    def on_sub_changed(self, choice):
        """Called when the second dropdown is changed."""
        GalleryPage.saved_sub = choice # Save the state
        self.apply_filter()

    def apply_filter(self):
        """Clears and rebuilds the gallery based on both dropdowns."""
        # 1. Clear the existing gallery
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        # 2. Reset the scrollbar to the very top
        if hasattr(self, 'canvas'):
            self.canvas.yview_moveto(0)
            
        # 3. Re-load images with the new filter
        self.load_gallery_images(self.gallery_folder_path)

    def create_scrollable_gallery(self):
        scaled_x_start = self.scale_x_val(120)
        scaled_scrollbar_width = self.scale_x_val(40)
        
        self.unpacked_bg = self._get_color(BG_COLOR)
        self.unpacked_btn = self._get_color(BUTTON_COLOR)
        self.unpacked_hover = self._get_color(BUTTON_HOVER)

        # 1. The Canvas
        self.canvas = ctk.CTkCanvas(
            self.root,
            bg=self.unpacked_bg,        
            highlightthickness=0
        )
        self.canvas.place(x=scaled_x_start, y=self.scale_y_val(60), relwidth=0.84, relheight=0.85)

        # 2. The Scrollbar
        self.scrollbar = ctk.CTkScrollbar(
            self.root,
            orientation="vertical",
            command=self.canvas.yview,
            width=scaled_scrollbar_width,  
            fg_color=self.unpacked_bg,      
            button_color=self.unpacked_btn, 
            button_hover_color=self.unpacked_hover, 
        )
        self.scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne") 

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 3. The Inner Frame
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

        master_data = self._load_master_json(self.master_json_path)

        if not master_data:
            print("⚠️ Warning: gallery_data.json is empty or not found. No items will be loaded.")
            return
            
        jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
        if not jpg_files:
            print("No JPG images found.")
            return

        scaled_name_font = tuple(custom_font_regular)
        card_color = self._get_color(BUTTON_COLOR) 
        valid_image_index = 0

        # Mapping for exact YOLO symbols to full dropdown names
        NUTRIENT_ALIASES = {
            "Nitrogen": ["nitrogen", "n"],
            "Phosphorus": ["phosphorus", "p"],
            "Potassium": ["potassium", "k"],
            "Calcium": ["calcium", "ca"],
            "Magnesium": ["magnesium", "mg"]
        }
        
        PEST_ALIASES = {
            "Aphids": ["aphid", "aphids"],
            "Caterpillars": ["caterpillar", "caterpillars", "worm", "looper"],
            "Slugs": ["slug", "slugs", "snail"],
            "Droplets": ["droplet", "droplets", "water"]
        }

        # Current selections
        cat = self.category_var.get()
        sub = self.sub_var.get()

        for filename in jpg_files:
            file_path = os.path.join(folder_path, filename)
            
            if filename not in master_data:
                print(f"⚠️ Warning: No data for {filename} in master JSON. Skipping.")
                continue 

            item_data = master_data[filename]
            
            # --- BULLETPROOF EXTRACTION: Match exactly how we did it in AnalysisPage ---
            raw_name = item_data.get("disease", "") or item_data.get("pest_name", "") or item_data.get("pest", "")
            if not raw_name: 
                continue
                
            individual_names = [self._format_name(n.strip()) for n in raw_name.split(',')]
            
            is_match = False
            
            if cat == "All":
                is_match = True
                
            elif cat == "Pests":
                for name in individual_names:
                    clean_words = name.lower().split()
                    
                    if sub == "All":
                        # Match ANY pest or droplet
                        for aliases in PEST_ALIASES.values():
                            if name.lower() in aliases or any(alias in clean_words for alias in aliases):
                                is_match = True
                                break
                    else:
                        # Match ONLY the selected sub-filter (e.g., sub = "Aphids")
                        aliases = PEST_ALIASES.get(sub, [])
                        if name.lower() in aliases or any(alias in clean_words for alias in aliases):
                            is_match = True
                            
            elif cat == "Deficiencies":
                for name in individual_names:
                    clean_words = name.lower().split()
                    
                    if sub == "All":
                        # Match ANY deficiency if any alias is an isolated word or exact match
                        for aliases in NUTRIENT_ALIASES.values():
                            if name.lower() in aliases or any(alias in clean_words for alias in aliases):
                                is_match = True
                                break
                    else:
                        # Match ONLY the selected sub-filter
                        aliases = NUTRIENT_ALIASES.get(sub, [])
                        if name.lower() in aliases or any(alias in clean_words for alias in aliases):
                            is_match = True
                            
            elif cat == "Diseases":
                for name in individual_names:
                    clean_words = name.lower().split()
                    
                    if sub == "All":
                        # A disease is anything that is NOT a pest and NOT a deficiency
                        is_deficiency_or_pest = False
                        
                        # Check against both nutrient and pest aliases
                        all_other_aliases = list(NUTRIENT_ALIASES.values()) + list(PEST_ALIASES.values())
                        for aliases in all_other_aliases:
                            if name.lower() in aliases or any(alias in clean_words for alias in aliases):
                                is_deficiency_or_pest = True
                                break
                        
                        if not is_deficiency_or_pest and name.lower() != "healthy" and name != "No Disease Detected":
                            is_match = True
                    else:
                        # Check for specific disease
                        if sub in name:
                            is_match = True
                            
            if not is_match:
                continue
            # --- End of filter logic ---

            # Load and resize image
            img = Image.open(file_path)
            img = img.resize((image_width, image_height))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(image_width, image_height))

            # Use the valid_image_index for perfect grid placement
            col = valid_image_index % max_per_row
            row = valid_image_index // max_per_row
            
            valid_image_index += 1 

            # 1. Create the container frame
            frame = ctk.CTkFrame(
                self.scrollable_frame, 
                width=panel_width, 
                height=panel_height, 
                fg_color=card_color, 
                corner_radius=self.scale_x_val(10)
            )
            frame.grid_propagate(False) 
            frame.grid(row=row, column=col, padx=spacing, pady=spacing, sticky="nsew")

            # Image button
            img_button = ctk.CTkButton(
                frame,
                image=ctk_img,
                text="",
                width=image_width,
                height=image_height,
                fg_color="transparent",
                hover_color=self.unpacked_hover,
                command=lambda path=file_path: self.open_analysis_view(path)
            )
            img_button.image = ctk_img
            img_button.place(relx=0.5, rely=0.45, anchor="center")

            # Filename label
            name = os.path.splitext(filename)[0]
            name_label = ctk.CTkLabel(
                frame, 
                text=name, 
                text_color=self._get_color(TEXT_COLOR),
                font=scaled_name_font 
            )
            name_label.place(relx=0.5, rely=0.9, anchor="center")

    def open_analysis_view(self, image_path):
        """Destroys the gallery and opens the analysis page in view-only mode."""
        self.root.destroy()
        app = AnalysisPage(image_path=image_path, view_only=True)
        app.root.mainloop()

# --- To run this page directly for testing (if needed) ---
if __name__ == "__main__":
    app = GalleryPage()
    app.root.mainloop()