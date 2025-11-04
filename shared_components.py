import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import cv2

# Layout and color constant defaults (These now define the ORIGINAL design size)
ORIGINAL_WIDTH = 800
ORIGINAL_HEIGHT = 480
LEFT_PANEL_WIDTH = 107
LEFT_PANEL_COLOR = "#2A2E3F"
BG_COLOR = "#202332"
BUTTON_COLOR = "#2A2E3F"
BUTTON_HOVER = "#383C4E"

ADJUSTED_HEIGHT_MARGIN_PIXELS = 40

# Use system Helvetica fonts (Stored as lists to allow in-place size modification)
custom_font_title = ["Arial", 50, "bold"]
custom_font_bold = ["Arial", 14, "bold"]
custom_font_regular = ["Arial", 12]

class SharedComponents:

    _fonts_scaled = False

    def _scale_value(self, value, axis='x'):
        """Applies scaling and converts to integer. Handles None values."""
        if value is None:
            return None
        factor = self.scale_x if axis == 'x' else self.scale_y
        return round(value * factor)

    def _calculate_scaling_factors(self):
        """Sets window geometry to fill screen (minus margin) and calculates scaling factors."""
        
        # Get actual screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate the scaled margin based on the screen's size
        estimated_scale_y = screen_height / ORIGINAL_HEIGHT
        scaled_margin = round(ADJUSTED_HEIGHT_MARGIN_PIXELS * estimated_scale_y)
                
        # 1. Determine the final desired usable window size
        self.actual_width = screen_width
        self.actual_height = screen_height - scaled_margin
        
        # 2. Set geometry to the REDUCED height. This creates the space at the bottom.
        self.root.geometry(f"{self.actual_width}x{self.actual_height}+0+0") 
        
        # 3. Update the window to make sure the new geometry is registered
        self.root.update_idletasks()
        
        # 4. Calculate scaling factors based on the final window size
        self.scale_x = self.actual_width / ORIGINAL_WIDTH
        self.scale_y = self.actual_height / ORIGINAL_HEIGHT
        
        if not SharedComponents._fonts_scaled:
            
            scale_avg = (self.scale_x + self.scale_y) / 2
            
            FONT_MAX_CAP = 1.3
            font_scale_factor = min(scale_avg, FONT_MAX_CAP)
            
            global custom_font_title, custom_font_bold, custom_font_regular
            
            def scale_font(font_list):
                name, size, *styles = font_list
                new_size = round(size * font_scale_factor)
                font_list[1] = new_size 

            scale_font(custom_font_title)
            scale_font(custom_font_bold)
            scale_font(custom_font_regular)
            
            SharedComponents._fonts_scaled = True 

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Agrivision Dashboard")
        self.root.configure(fg_color=BG_COLOR)
        
        self._calculate_scaling_factors()

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
        # Scale width, height is set to actual_height (the reduced height)
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
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_hover_offset = self._scale_value(5, 'y')

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

        def on_enter(event):
            btn.place_configure(y=scaled_y - scaled_hover_offset) 
        def on_leave(event):
            btn.place_configure(y=scaled_y) 

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

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

    def undo_button(self,command=None):
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
            command=command,
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
    
    def cleanup_camera(self):
        """Releases the camera and turns off the LED/resource."""
        if self.cap and self.cap.isOpened():
            self.running = False # Stop the update loop
            self.cap.release()
            cv2.destroyAllWindows()
            print("✅ Camera successfully released.")
        
        # NOTE: You should also destroy the camera_label widget 
        # to ensure it's removed from the UI when navigating pages.
        if hasattr(self, 'camera_label') and self.camera_label.winfo_exists():
            self.camera_label.destroy()

    def go_back_to_dashboard(self):
        # self.cleanup_camera()
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.root.mainloop()
    
    def camera_to_dashboard(self):
        self.cleanup_camera()
        self.root.destroy()
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
                      fg_color=BUTTON_COLOR, font=custom_font_bold, corner_radius=8,
                      handle_hover=True, hover_color=BUTTON_HOVER): # <-- 1. ADD hover_color PARAM
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
            hover_color=hover_color, # <-- 2. USE THE PARAMETER HERE
            corner_radius=scaled_corner_radius,
            command=command,
            image=image,
            compound=compound,
        )
        button.place(x=scaled_x, y=scaled_y)

        # --- MODIFICATION: Make hover optional ---
        if handle_hover:
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
# --- NEW FUNCTION ADDED HERE ---
    def create_weather_analytics_panel(self, x, y, width, height, anchor, command):
        """
        Creates the composite weather analytics button.
        This button contains multiple labels and icons but acts as a single button.
        """
        
        # --- ADDED: Re-calculate scaled values for hover logic ---
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')
        
        # 1. Create the main button
        weather_button = self.create_button(
            text="", # Text will be added inside
            x=x, y=y,
            width=width, height=height,
            anchor=anchor,
            command=command, # This makes the main button clickable
            handle_hover=False, # <-- Disable default raise
            hover_color=BUTTON_COLOR # <-- Disable default hover color
        )
        # Prevent the button from shrinking
        weather_button.pack_propagate(False) 

        # 2. Load Icons
        try:
            # Note: 'Image' is imported at the top of this file
            icon_size = (self._scale_value(40, 'x'), self._scale_value(40, 'y'))
            self.temp_icon = ctk.CTkImage(light_image=Image.open("_image_assets/temperature.png"), size=icon_size)
            self.hum_icon = ctk.CTkImage(light_image=Image.open("_image_assets/humidity.png"), size=icon_size)
            self.pres_icon = ctk.CTkImage(light_image=Image.open("_image_assets/pressure.png"), size=icon_size)
        except Exception as e:
            print(f"Error loading weather icons: {e}")
            self.temp_icon = self.hum_icon = self.pres_icon = None

        # 3. Create Title Label
        shared_button_font = tuple(custom_font_bold)
        
        title_label = ctk.CTkLabel(
            weather_button, 
            text="Weather Analytics", 
            font=shared_button_font, # Use shared font
            text_color="white",
            fg_color="transparent" # <-- Ensure title_label has a background we can change
        )
        # --- FIX: Removed invalid 'hover_color' parameter from title_label ---
        title_label.pack(pady=self._scale_value(10, 'y'))

        # 4. Create Data Frames
        
        # --- Temperature Row ---
        temp_frame = ctk.CTkFrame(weather_button, fg_color="#2A2E3F")
        temp_icon_label = ctk.CTkLabel(temp_frame, text="", image=self.temp_icon)
        temp_icon_label.pack(side="left", padx=10)
        self.temp_label = ctk.CTkLabel(temp_frame, text="-- °C", font=shared_button_font, text_color="white")
        self.temp_label.pack(side="left", padx=10)
        temp_frame.pack(fill="x", pady=self._scale_value(5, 'y'))
        
        # --- Humidity Row ---
        hum_frame = ctk.CTkFrame(weather_button, fg_color="#2A2E3F")
        hum_icon_label = ctk.CTkLabel(hum_frame, text="", image=self.hum_icon)
        hum_icon_label.pack(side="left", padx=10)
        self.hum_label = ctk.CTkLabel(hum_frame, text="-- %", font=shared_button_font, text_color="white")
        self.hum_label.pack(side="left", padx=10)
        hum_frame.pack(fill="x", pady=self._scale_value(5, 'y'))
        
        # --- Pressure Row ---
        pres_frame = ctk.CTkFrame(weather_button, fg_color="transparent")
        pres_icon_label = ctk.CTkLabel(pres_frame, text="", image=self.pres_icon)
        pres_icon_label.pack(side="left", padx=10)
        self.pres_label = ctk.CTkLabel(pres_frame, text="-- hPa", font=shared_button_font, text_color="white")
        self.pres_label.pack(side="left", padx=10)
        pres_frame.pack(fill="x", pady=self._scale_value(5, 'y'))

        # --- 5. UPDATED: Hover logic controls all colors ---
        def on_composite_enter(event):
            weather_button.place_configure(y=scaled_y - scaled_hover_offset)
            weather_button.configure(fg_color=BUTTON_HOVER) 
            
            # Change colors for all child elements that need it
            title_label.configure(fg_color=BUTTON_HOVER) # <-- NOW HIGHLIGHTS TITLE BACKGROUND
            temp_frame.configure(fg_color=BUTTON_HOVER)
            hum_frame.configure(fg_color=BUTTON_HOVER)
            pres_frame.configure(fg_color=BUTTON_HOVER)

        def on_composite_leave(event):
            weather_button.place_configure(y=scaled_y)
            weather_button.configure(fg_color=BUTTON_COLOR) 
            
            # Revert colors for all child elements
            title_label.configure(fg_color="transparent") # <-- Revert title
            temp_frame.configure(fg_color=BUTTON_COLOR)
            hum_frame.configure(fg_color=BUTTON_COLOR)
            pres_frame.configure(fg_color="transparent") 

        # 6. Make all inner widgets clickable and hoverable
        # Store all widgets that need to be bound
        widgets_to_bind = [
            weather_button, 
            title_label, 
            temp_frame, temp_icon_label, self.temp_label,
            hum_frame, hum_icon_label, self.hum_label,
            pres_frame, pres_icon_label, self.pres_label
        ]
        
        # Bind all widgets to the main button's command and new hover logic
        for widget in widgets_to_bind:
             # Use <Button-1> for left-click
             widget.bind("<Button-1>", lambda e, cmd=command: cmd() if cmd else None)
             
             # --- Bind the NEW composite hover functions ---
             widget.bind("<Enter>", on_composite_enter)
             widget.bind("<Leave>", on_composite_leave)

        return weather_button