import customtkinter as ctk
import os
import json
from datetime import datetime

class RecentDiseaseList(ctk.CTkFrame):
    """
    A custom scrollable widget that loads data from the master JSON,
    sorts it by date, and displays it in a list.
    
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
        
        # 1. Canvas for scrolling
        self.canvas = ctk.CTkCanvas(self, bg=self.cget("fg_color"), highlightthickness=0)
        
        # 2. Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        
        # 3. Inner frame to hold the content
        self.scrollable_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")

        # --- Link Components ---
        
        # Link canvas and scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # --- MODIFIED: THIS IS THE KEY FIX ---
        
        # BINDING 1: 
        # When the inner frame's content changes (making it taller/shorter),
        # tell the canvas to update its scrollable area.
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        # Place the inner frame inside the canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # BINDING 2:
        # When the *canvas* is resized (or first drawn),
        # force the inner frame's width to match the canvas's width.
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # --- END OF MODIFIED SECTION ---

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

    # MODIFIED: This function is now simpler
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
        """Loads master JSON and sorts entries by timestamp, newest first."""
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

            # 2. Get all analysis entries (the values of the dict)
            all_entries = list(master_data.values())

            # 3. Define the timestamp format
            # Example: "Oct 19, 2025 09:50 PM"
            timestamp_format = "%b %d, %Y %I:%M %p"

            # 4. Sort the list
            # We use strptime to convert the string timestamp into a real
            # datetime object, which can be sorted correctly.
            def get_date(item):
                try:
                    return datetime.strptime(item.get('timestamp', ''), timestamp_format)
                except ValueError:
                    # Handle any malformed data by placing it at the bottom
                    return datetime.min

            # sort(key=..., reverse=True) puts the newest items at the top
            all_entries.sort(key=get_date, reverse=True)
            
            return all_entries

        except Exception as e:
            print(f"❌ Error loading or sorting recent data: {e}")
            return []
            
    # NEW: Helper function to format disease names
    def _format_disease_name(self, name_str):
        """Converts snake_case names into formatted Title Case."""
        # Specific overrides
        if name_str == "Downy_mildew_on_lettuce":
            return "Downy Mildew"
        if name_str == "Powdery_mildew_on_lettuce":
            return "Powdery Mildew"
        
        # General rule
        return name_str.replace("_", " ").title()

    def _populate_list(self):
        """Creates the label widgets for each disease entry."""
        
        sorted_data = self._load_and_sort_data()
        
        if not sorted_data:
            label = ctk.CTkLabel(self.scrollable_frame, text="No records found.", text_color="gray")
            label.pack(pady=10)
            # Bind drag events even to the "empty" label
            label.bind("<ButtonPress-1>", self._on_press)
            label.bind("<B1-Motion>", self._on_motion)
            return

        # Define fonts
        disease_font = ctk.CTkFont(family="Arial", size=14, weight="bold")
        date_font = ctk.CTkFont(family="Arial", size=12)

        for item in sorted_data:
            # MODIFIED: Get the raw name and format it
            raw_disease = item.get("disease", "Unknown Disease")
            disease = self._format_disease_name(raw_disease) # <-- Use the formatter
            
            timestamp = item.get("timestamp", "Unknown Date")
            
            # Create a frame for each item
            item_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#3B3F51", corner_radius=5)
            
            # Disease Label
            disease_label = ctk.CTkLabel(
                item_frame,
                text=disease,
                font=disease_font,
                text_color="white",
                anchor="w"
            )
            # MODIFIED: Pack to the left, expand, and add consistent padding
            disease_label.pack(side="left", pady=5, padx=10, fill="x", expand=True)

            # Timestamp Label
            date_label = ctk.CTkLabel(
                item_frame,
                text=timestamp,
                font=date_font,
                text_color="#BCBCBC", # A lighter gray
                anchor="e" # Anchor text to the East (right)
            )
            # MODIFIED: Pack to the right and add consistent padding
            date_label.pack(side="right", pady=5, padx=10)

            # Pack the item frame into the scrollable list
            # MODIFIED: Removed padx to allow the frame to fill the width
            item_frame.pack(fill="x", expand=True, pady=(0, 5))

            # --- Bind Drag Events to ALL new widgets ---
            # This is crucial so dragging works on top of the labels
            item_frame.bind("<ButtonPress-1>", self._on_press)
            item_frame.bind("<B1-Motion>", self._on_motion)
            disease_label.bind("<ButtonPress-1>", self._on_press)
            disease_label.bind("<B1-Motion>", self._on_motion)
            date_label.bind("<ButtonPress-1>", self._on_press)
            date_label.bind("<B1-Motion>", self._on_motion)

        # --- THIS IS STILL NEEDED ---
        # Add an empty frame at the bottom to act as padding.
        # This makes the inner_frame *taller*, which triggers its <Configure>
        # event, which in turn updates the scrollregion to include this padding.
        bottom_padding = ctk.CTkFrame(self.scrollable_frame, height=20, fg_color="transparent")
        bottom_padding.pack()
        
        # Bind drag events to the padding as well
        bottom_padding.bind("<ButtonPress-1>", self._on_press)
        bottom_padding.bind("<B1-Motion>", self._on_motion)
        # --- END OF PADDING SECTION ---


    # --- Drag-to-Scroll Methods ---
    
    def _on_press(self, event):
        """Called on mouse click. Marks the starting point for the drag."""
        self.canvas.scan_mark(event.x, event.y)

    def _on_motion(self, event):
        """Called on mouse drag. Scrolls the canvas relative to the mark."""
        self.canvas.scan_dragto(event.x, event.y, gain=1)