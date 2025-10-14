import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk

# Layout and color constant defaults (These now define the ORIGINAL design size)
ORIGINAL_WIDTH = 800
ORIGINAL_HEIGHT = 480
LEFT_PANEL_WIDTH = 107
LEFT_PANEL_COLOR = "#2A2E3F"
BG_COLOR = "#202332"
BUTTON_COLOR = "#2A2E3F"
BUTTON_HOVER = "#383C4E"

# Use system Helvetica fonts (Stored as lists to allow in-place size modification)
custom_font_title = ["Arial", 42, "bold"]
custom_font_bold = ["Arial", 23, "bold"]
custom_font_regular = ["Arial", 20]

class SharedComponents:

    custom_font_title = ["Arial", 42, "bold"]
    custom_font_bold = ["Arial", 23, "bold"]
    custom_font_regular = ["Arial", 20]
    # Class-level flag to ensure fonts are scaled only once
    _fonts_scaled = False

    def _scale_value(self, value, axis='x'):
        """Applies scaling and converts to integer. Handles None values."""
        if value is None:
            return None
        factor = self.scale_x if axis == 'x' else self.scale_y
        return round(value * factor)

    def _calculate_scaling_factors(self):
        """Sets the root to fullscreen and calculates scaling factors."""
        
        # Set the window to fullscreen
        self.root.attributes('-fullscreen', True)
        self.root.update_idletasks()
        
        # Get actual dimensions after fullscreen is set
        self.actual_width = self.root.winfo_width()
        self.actual_height = self.root.winfo_height()

        # Calculate screen scaling factors
        self.scale_x = self.actual_width / ORIGINAL_WIDTH
        self.scale_y = self.actual_height / ORIGINAL_HEIGHT
        
        # --- FIX: One-Time, Capped Font Scaling ---
        if not SharedComponents._fonts_scaled:
            
            # Use the average scale factor
            scale_avg = (self.scale_x + self.scale_y) / 2
            
            # Cap the font scale factor to prevent fonts from becoming too large (e.g., max 30% increase)
            FONT_MAX_CAP = 1.3
            font_scale_factor = min(scale_avg, FONT_MAX_CAP)
            
            global custom_font_title, custom_font_bold, custom_font_regular
            
            def scale_font(font_list):
                name, size, *styles = font_list
                # Scale the font size and update the list in place
                new_size = round(size * font_scale_factor)
                font_list[1] = new_size 

            scale_font(custom_font_title)
            scale_font(custom_font_bold)
            scale_font(custom_font_regular)
            
            SharedComponents._fonts_scaled = True # Set flag after scaling

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Agrivision Dashboard")
        self.root.configure(fg_color=BG_COLOR)
        
        # --- FIX: Set fullscreen and calculate scaling on initialization ---
        self._calculate_scaling_factors()


    # --- Component Creation Methods (All scaled and using tuple(font)) ---

    def create_leaf_image(self, image_path="_image_assets/Leaf.png", x=5, y=5, size=(100, 100)):
        # Scale position and size
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_size = (self._scale_value(size[0], 'x'), self._scale_value(size[1], 'y'))

        leaf_img = Image.open(image_path).convert("RGBA")
        leaf_img = leaf_img.resize(scaled_size)

        transparent_bg = Image.new("RGBA", leaf_img.size, (42, 46, 63))
        transparent_bg.paste(leaf_img, (0, 0), leaf_img)

        leaf_ctk = ctk.CTkImage(light_image=transparent_bg, dark_image=transparent_bg, size=scaled_size)
        self.leaf_label = ctk.CTkLabel(self.root, image=leaf_ctk, text="")
        self.leaf_label.place(x=scaled_x, y=scaled_y)
        self.leaf_label.image = leaf_ctk  
        return self.leaf_label

    def create_title(self, text="AGRIVISION v1.0", x=119, y=0):
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        
        if not hasattr(self, "title_label"):
            self.title_label = ctk.CTkLabel(
                self.root,
                text=text,
                font=tuple(custom_font_title), # FIX: Convert list to tuple
                text_color="#FFFFFF",
                fg_color=BG_COLOR
            )
            self.title_label.place(x=scaled_x, y=scaled_y)
        else:
            self.title_label.configure(text=text)
        return self.title_label

    def create_left_panel(self):
        # Scale width, height is set to actual_height
        scaled_width = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        scaled_height = self.actual_height 

        self.left_panel = ctk.CTkFrame(
            self.root,
            width=scaled_width,
            height=scaled_height,
            fg_color=LEFT_PANEL_COLOR,
            corner_radius=self._scale_value(8, 'x')
        )
        self.left_panel.pack(side="left", fill="y", padx=(0, self._scale_value(10, 'x')), pady=0)
        return self.left_panel

    def create_record_button(self, x, y, command=None):
        # Scale position, width, height, and image size
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_width = self._scale_value(90, 'x')
        scaled_height = self._scale_value(90, 'y')
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))

        record_img = Image.open("_image_assets/record.png")
        record_photo = ctk.CTkImage(light_image=record_img, dark_image=record_img, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root,
            text="",
            width=scaled_width,
            height=scaled_height,
            image=record_photo,
            compound="top",
            command=command,
            fg_color="#2A2E3F",
            hover_color="#2A2E3F",
        )
        btn.place(x=scaled_x, y=scaled_y, anchor="center")
        return btn

    def settings_button(self, command=None):
        # Scale image size, position, width, height, and hover offset
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        x, y = 10, 380
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')

        settings_img = Image.open("_image_assets/Settings.png").resize(scaled_img_size)
        settings_photo = ctk.CTkImage(light_image=settings_img, dark_image=settings_img, size=scaled_img_size) 

        btn = ctk.CTkButton(
            self.root,
            text="",
            width=scaled_width,
            height=scaled_height,
            image=settings_photo,
            compound="top",
            command=command,
            fg_color="#2A2E3F",
            hover_color="#2A2E3F",
            corner_radius=0
        )
        btn.place(x=scaled_x, y=scaled_y)
        btn.image = settings_photo

        def on_enter(event):
            btn.place_configure(y=scaled_y - scaled_hover_offset) 
        def on_leave(event):
            btn.place_configure(y=scaled_y) 

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def undo_button(self):
        # Scale image size, position, width, height, and hover offset
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        x, y = 5, 380
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')

        undo_img = Image.open("_image_assets/Undo.png")
        undo_photo = ctk.CTkImage(light_image=undo_img, dark_image=undo_img, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root,
            text="",
            width=scaled_width,
            height=scaled_height,
            image=undo_photo,
            compound="top",
            command=self.go_back_to_dashboard,
            fg_color="#2A2E3F",
            hover_color="#2A2E3F",
            corner_radius=0
        )
        btn.place(x=scaled_x, y=scaled_y)
        btn.image = undo_photo

        def on_enter(event):
            btn.place_configure(y=scaled_y - scaled_hover_offset)
        def on_leave(event):
            btn.place_configure(y=scaled_y)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def go_back_to_dashboard(self):
        # Removed geometry saving/loading as the app is always fullscreen
        self.root.destroy()
        # Note: You need to ensure Pages.main_dashboard is accessible here
        # E.g., from Pages.main_dashboard import MyDashboard
        # If your environment is correct, this will work:
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.root.mainloop()

    def load_futures_icon(self, size=(75, 78)):
        # Scale image size
        scaled_size = (self._scale_value(size[0], 'x'), self._scale_value(size[1], 'y'))
        try:
            futures_img = Image.open("_image_assets/futures.png")
            futures_ctk = ctk.CTkImage(light_image=futures_img, dark_image=futures_img, size=scaled_size)
            return futures_ctk
        except Exception as e:
            print(f"Error loading futures icon: {e}")
            return None

    def create_button(self, text="Button", x=100, y=100, 
                      width=140, height=140, anchor="sw", 
                      command=None, image=None, compound="top",
                      fg_color=BUTTON_COLOR, font=custom_font_bold, corner_radius=8):
        # Scale all geometry parameters
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_width = self._scale_value(width, 'x')
        scaled_height = self._scale_value(height, 'y')
        scaled_corner_radius = self._scale_value(corner_radius, 'x')
        scaled_hover_offset = self._scale_value(5, 'y')

        button = ctk.CTkButton(
            self.root,
            width=scaled_width,
            height=scaled_height,
            text=text,
            anchor=anchor,
            font=tuple(font), # FIX: Convert list to tuple
            fg_color=fg_color,
            hover_color=BUTTON_HOVER,
            corner_radius=scaled_corner_radius,
            command=command,
            image=image,
            compound=compound,
        )
        button.place(x=scaled_x, y=scaled_y)

        def on_enter(event):
            button.place_configure(y=scaled_y - scaled_hover_offset)
        def on_leave(event):
            button.place_configure(y=scaled_y)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        return button

    def create_panel(self, text="", x=100, y=100, 
                     width=140, height=140, anchor="nw", 
                     image=None, compound="top"):
        # Scale all geometry parameters
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_width = self._scale_value(width, 'x')
        scaled_height = self._scale_value(height, 'y')
        scaled_corner_radius = self._scale_value(8, 'x')
        
        panel = ctk.CTkFrame(
            self.root,
            width=scaled_width,
            height=scaled_height,
            fg_color=LEFT_PANEL_COLOR,
            corner_radius=scaled_corner_radius
        )
        panel.place(x=scaled_x, y=scaled_y, anchor=anchor)

        if text:
            label = ctk.CTkLabel(
                panel,
                text=text,
                font=tuple(custom_font_bold), # FIX: Convert list to tuple
                text_color="#FFFFFF",
                fg_color="transparent",
                image=image,
                compound=compound
            )
            label.place(relx=0.5, rely=0, anchor="n")

        return panel