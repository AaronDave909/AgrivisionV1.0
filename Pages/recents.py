import customtkinter as ctk
import os
import json
from datetime import datetime
from shared_components import BUTTON_COLOR, TEXT_COLOR, LEFT_PANEL_COLOR

# --- Standalone Helper Function ---
def _format_disease_name(name_str):
    """Converts snake_case names into formatted Title Case."""
    if name_str == "Downy_mildew_on_lettuce":
        return "Downy Mildew"
    if name_str == "Powdery_mildew_on_lettuce":
        return "Powdery Mildew"
    
    # General rule
    return name_str.replace("_", " ").title()

# --- Standalone Function for Dashboard (Internal) ---
def get_most_recent_detection():
    """
    Loads the master JSON, finds the most recent *disease* entry,
    and returns its filename and data.
    """
    gallery_path = "Page_files/gallery_files"
    single_json_path = os.path.join(gallery_path, "gallery_data.json")
    
    try:
        # 1. Load the master dictionary
        if not os.path.exists(single_json_path):
            return None, None
        
        with open(single_json_path, 'r') as f:
            content = f.read()
            if not content:
                return None, None
            master_data = json.loads(content)
        
        if not master_data:
            return None, None

        # 2. Get all items (filename, data)
        all_entries = list(master_data.items())
        
        # --- NEW: Filter for diseases only ---
        # Only keep items where the data dict has the "disease" key
        disease_entries = [item for item in all_entries if "disease" in item[1]]
        
        if not disease_entries:
            print("[recents.py] No disease entries found.")
            return None, None
        # --- END FILTER ---

        # 3. Define timestamp format
        timestamp_format = "%b %d, %Y %I:%M %p"

        # 4. Sort the list
        def get_date(item_tuple):
            # item_tuple is (filename, data_dict)
            data_dict = item_tuple[1]
            try:
                return datetime.strptime(data_dict.get('timestamp', ''), timestamp_format)
            except ValueError:
                return datetime.min

        # MODIFIED: Sort the filtered disease_entries list
        disease_entries.sort(key=get_date, reverse=True)
        
        # 5. Return the most recent *disease* item
        return disease_entries[0] # Returns (filename, data_dict)

    except Exception as e:
        print(f"❌ Error in get_most_recent_detection: {e}")
        return None, None

# --- Standalone PREVIEW Function for Dashboard ---
def recent_disease_preview():
    """
    Gets the most recent *disease* detection and formats the data
    for the dashboard preview button.
    
    Returns:
        - disease_name (str): Formatted name, e.g., "Bacterial Leaf Spot" or "No Recent Detections"
        - date_str (str or None): Formatted date string, e.g., "Oct 26, 2025"
        - time_str (str or None): Formatted time string, e.g., "07:41 PM"
        - image_path (str or None): Full path to the associated image.
    """
    gallery_path = "Page_files/gallery_files"
    # This function now correctly gets the most recent *disease*
    filename, data = get_most_recent_detection() 

    if not filename or not data:
        return "No Recent\nDetections", None, None, None

    try:
        # Format disease name (this is safe as we know it's a disease)
        disease_name = _format_disease_name(data.get("disease", "Unknown"))

        # --- Parse and format timestamp ---
        timestamp_str = data.get("timestamp", None)
        date_str = None
        time_str = None
        if timestamp_str:
            try:
                # Use the format the JSON *currently* has for parsing
                timestamp_format_in_json = "%b %d, %Y %I:%M %p"
                dt_obj = datetime.strptime(timestamp_str, timestamp_format_in_json)
                # Format date and time separately for the button
                date_str = dt_obj.strftime("%b %d, %Y") # e.g., Oct 26, 2025
                time_str = dt_obj.strftime("%I:%M %p") # e.g., 07:41 PM
            except ValueError:
                print(f"❌ Error parsing timestamp in preview: {timestamp_str}")
                date_str = "Invalid Date"
                time_str = "Invalid Time"
        # --- END MODIFICATION ---

        # Get image path
        image_path = os.path.join(gallery_path, filename)
        if not os.path.exists(image_path):
            # Data exists but image is missing
            return "Data Error\nMissing Image", None, None, None

        # Return the separated date and time
        return disease_name, date_str, time_str, image_path

    except Exception as e:
        print(f"❌ Error in recent_disease_preview: {e}")
        return "Error", None, None, None


class RecentDiseaseList(ctk.CTkFrame):
    """
    A custom scrollable widget that loads data from the master JSON,
    sorts it by date, and displays *only disease* entries.
    
    Includes "drag-to-scroll" functionality.
    """
    
    def __init__(self, master, width, height, **kwargs):
        # Initialize the main frame
        super().__init__(master, width=width, height=height, **kwargs)

        # Prevent the frame from shrinking to fit its contents
        self.pack_propagate(False)

        # Define the path to the data
        self.gallery_path = "Page_files/gallery_files"
        self.single_json_path = os.path.join(self.gallery_path, "gallery_data.json")

        # --- Create Scrollable Components ---
        
        # --- Create Scrollable Components ---
        
        # 1. Canvas for scrolling
        # FIX: Unpack the tuple so the standard tkinter Canvas doesn't crash!
        current_mode = ctk.get_appearance_mode()
        canvas_bg = LEFT_PANEL_COLOR[0] if current_mode == "Light" else LEFT_PANEL_COLOR[1]
        
        self.canvas = ctk.CTkCanvas(self, bg=canvas_bg, highlightthickness=0)
        
        # 2. Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        
        # 3. Inner frame to hold the content
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")

        # --- Link Components ---
        
        # Link canvas and scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        

        # --- Place Components ---
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, pady=5)

        # --- Bind Drag-to-Scroll Events ---
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.scrollable_frame.bind("<ButtonPress-1>", self._on_press)
        self.scrollable_frame.bind("<B1-Motion>", self._on_motion)

        # --- Load and Display Data ---
        self._populate_list()

    def _on_canvas_configure(self, event):
        """
        Updates the inner frame's width to match the canvas's width.
        The scrollregion is updated by the scrollable_frame's own <Configure> binding.
        """
        canvas_width = event.width
        
        # Set the inner frame's width
        self.scrollable_frame.configure(width=canvas_width)
        
        # Update the canvas window item's width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _load_and_sort_data(self):
        """Loads master JSON and sorts *only disease* entries by timestamp, newest first."""
        try:
            # 1. Load the master dictionary
            if os.path.exists(self.single_json_path):
                with open(self.single_json_path, 'r') as f:
                    content = f.read()
                    if not content:
                        return [] # Return empty list if file is empty
                    master_data = json.loads(content)
            else:
                return [] # Return empty list if file doesn't exist

            # 2. MODIFIED: Get all items (filename, data)
            all_entries = list(master_data.items())
            
            # --- NEW: Filter for diseases only ---
            disease_entries = [item for item in all_entries if "disease" in item[1]]
            
            if not disease_entries:
                return []
            # --- END FILTER ---

            # 3. Define the timestamp format
            # Example: "Oct 19, 2025 09:50 PM"
            timestamp_format = "%b %d, %Y %I:%M %p"

            # 4. Sort the list
            def get_date(item_tuple):
                # item_tuple is (filename, data_dict)
                data_dict = item_tuple[1]
                try:
                    return datetime.strptime(data_dict.get('timestamp', ''), timestamp_format)
                except ValueError:
                    # Handle any malformed data by placing it at the bottom
                    return datetime.min

            # MODIFIED: Sort the filtered disease_entries list
            disease_entries.sort(key=get_date, reverse=True)
            
            return disease_entries # Returns list of (filename, data_dict)

        except Exception as e:
            print(f"❌ Error loading or sorting recent data: {e}")
            return []
            
    # _format_disease_name was removed from class, it is standalone now

    def _populate_list(self):
        """Creates the label widgets for each disease entry."""
        
        # This now receives only disease entries
        sorted_data = self._load_and_sort_data()
        
        if not sorted_data:
            label = ctk.CTkLabel(self.scrollable_frame, text="No disease records found.", text_color=TEXT_COLOR)
            label.pack(pady=10)
            # Bind drag events even to the "empty" label
            label.bind("<ButtonPress-1>", self._on_press)
            label.bind("<B1-Motion>", self._on_motion)
            return

        # Define fonts
        disease_font = ctk.CTkFont(family="Arial", size=14, weight="bold")
        date_font = ctk.CTkFont(family="Arial", size=12)

        # MODIFIED: Loop now gets filename and item
        for filename, item in sorted_data:
            # This code is now safe because we know "item" is a disease entry
            raw_disease = item.get("disease", "Unknown Disease")
            disease = _format_disease_name(raw_disease) # <-- Use standalone
            
            timestamp = item.get("timestamp", "Unknown Date")
            
            # Create a frame for each item
            item_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=BUTTON_COLOR, corner_radius=5)
            
            # Disease Label
            disease_label = ctk.CTkLabel(
                item_frame,
                text=disease,
                font=disease_font,
                text_color=TEXT_COLOR,
                anchor="w" # Anchor to the West (left)
            )
            disease_label.pack(pady=(5, 0), padx=10, fill="x")

            # Timestamp Label
            date_label = ctk.CTkLabel(
                item_frame,
                text=timestamp,
                font=date_font,
                text_color=TEXT_COLOR,
                anchor="w" # Anchor to the West (left)
            )
            # MODIFIED: Use vertical packing (default) and fill="x"
            date_label.pack(pady=(0, 5), padx=10, fill="x")

            # Pack the item frame into the scrollable list
            # We still need fill="x" and expand=True here to make the item_frame fill the panel width
            item_frame.pack(fill="x", expand=True, pady=(0, 5)) 

            # --- Bind Drag Events to ALL new widgets ---
            item_frame.bind("<ButtonPress-1>", self._on_press)
            item_frame.bind("<B1-Motion>", self._on_motion)
            disease_label.bind("<ButtonPress-1>", self._on_press)
            disease_label.bind("<B1-Motion>", self._on_motion)
            date_label.bind("<ButtonPress-1>", self._on_press)
            date_label.bind("<B1-Motion>", self._on_motion)

        bottom_padding = ctk.CTkFrame(self.scrollable_frame, height=20, fg_color="transparent")
        bottom_padding.pack()
        
        # Bind drag events to the padding as well
        bottom_padding.bind("<ButtonPress-1>", self._on_press)
        bottom_padding.bind("<B1-Motion>", self._on_motion)

    # --- Drag-to-Scroll Methods ---
    
    def _on_press(self, event):
        """Called on mouse click. Marks the starting point for the drag."""
        self.canvas.scan_mark(event.x, event.y)

    def _on_motion(self, event):
        """Called on mouse drag. Scrolls the canvas relative to the mark."""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
