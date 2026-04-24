import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import cv2
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import os

# Layout and color constant defaults (These now define the ORIGINAL design size)
ORIGINAL_WIDTH = 800
ORIGINAL_HEIGHT = 480
LEFT_PANEL_WIDTH = 107

# The Magic Tuples: ("Light Mode Color", "Dark Mode Color")
BG_COLOR = ("#F8F8F8", "#202332")             # Pure white / Darkest blue
LEFT_PANEL_COLOR = ("#E4E6EB", "#2F3344")     # Very light gray-blue / Dark panel blue
BUTTON_COLOR = ("#E4E6EB", "#2A2E3F")         # Light gray / Dark panel blue
BUTTON_HOVER = ("#D8DADF", "#383C4E")         # Slightly darker gray / Lighter dark blue
TEXT_COLOR = ("#0A1128", "#FFFFFF")           # Dark Dark Blue / Pure White

ADJUSTED_HEIGHT_MARGIN_PIXELS = 40

# Use system Helvetica fonts (Stored as lists to allow in-place size modification)
custom_font_title = ["Arial", 50, "bold"]
custom_font_bold = ["Arial", 14, "bold"]
custom_font_regular = ["Arial", 12]

class SharedComponents:

    _fonts_scaled = False

    # ---------------------------------------------------------
    # THEME HELPER (FIX FOR COLOR TUPLES)
    # ---------------------------------------------------------
    def _get_color(self, color_tuple):
        mode = ctk.get_appearance_mode()
        # If it's not a tuple (e.g. "transparent" or a hex string), return it directly
        if not isinstance(color_tuple, tuple):
            return color_tuple
        return color_tuple[0] if mode == "Light" else color_tuple[1]

    # ---------------------------------------------------------
    # SCALE UTIL
    # ---------------------------------------------------------
    def _scale_value(self, value, axis='x'):
        """Applies scaling and converts to integer. Handles None values."""
        if value is None:
            return None
        factor = self.scale_x if axis == 'x' else self.scale_y
        return round(value * factor)

    # ---------------------------------------------------------
    # WINDOW SCALING
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # INIT
    # ---------------------------------------------------------
    def __init__(self):
        self.root = ctk.CTk()
        
        theme_file = "Page_files/theme_state.txt"
        if os.path.exists(theme_file):
            try:
                with open(theme_file, "r") as f:
                    saved_theme = f.read().strip()
                    if saved_theme in ["Light", "Dark"]:
                        ctk.set_appearance_mode(saved_theme)
            except Exception as e:
                print(f"Failed to load saved theme: {e}")
        
        self.root.title("Agrivision")
        self.root.configure(fg_color=self._get_color(BG_COLOR))
        
        try:
            icon_path = "_image_assets/Leaf.png"
            if os.path.exists(icon_path):
                # Load the image using PIL and convert to a Tkinter-compatible PhotoImage
                icon_img = ImageTk.PhotoImage(file=icon_path)
                self.icon_img = icon_img
                
                # Apply the icon to the window. 
                # True means it applies to all future TopLevel windows too.
                self.root.wm_iconphoto(True, self.icon_img)
            else:
                print(f"Icon not found at: {icon_path}")
        except Exception as e:
            print(f"Error setting application icon: {e}")
        
        # Missing variable initialized to prevent crashes in cleanup_camera
        self.cap = None 
        self.running = False
        
        self._calculate_scaling_factors()

    # ---------------------------------------------------------
    # ICON RECOLOR
    # ---------------------------------------------------------
    def _recolor_icon(self, image_path, hex_color):
        """Dynamically recolors a white transparent PNG to a new hex color."""
        original = Image.open(image_path).convert("RGBA")
        alpha_mask = original.split()[3] 
        color_block = Image.new("RGBA", original.size, color=hex_color)
        color_block.putalpha(alpha_mask)
        return color_block

    # ---------------------------------------------------------
    # LEAF IMAGE
    # ---------------------------------------------------------
    def create_leaf_image(self, image_path="_image_assets/Leaf.png", x=5, y=5, size=(100, 100)):
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_size = (self._scale_value(size[0], 'x'), self._scale_value(size[1], 'y'))

        img_white = Image.open(image_path).convert("RGBA")
        img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])

        leaf_ctk = ctk.CTkImage(
            light_image=img_dark,  
            dark_image=img_white,  
            size=scaled_size
        )
        
        self.leaf_label = ctk.CTkLabel(self.root, image=leaf_ctk, text="", fg_color=self._get_color(LEFT_PANEL_COLOR))
        self.leaf_label.place(x=scaled_x, y=scaled_y)
        self.leaf_label.image = leaf_ctk  
        return self.leaf_label

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------
    def create_title(self, text="AGRIVISION v1.0", x=119, y=0):
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        
        if not hasattr(self, "title_label"):
            self.title_label = ctk.CTkLabel(
                self.root,
                text=text,
                font=tuple(custom_font_title), 
                text_color=self._get_color(TEXT_COLOR),
                fg_color="transparent"
            )
            self.title_label.place(x=scaled_x, y=scaled_y)
        else:
            self.title_label.configure(text=text)
        return self.title_label

    # ---------------------------------------------------------
    # LEFT PANEL
    # ---------------------------------------------------------
    def create_left_panel(self):
        scaled_width = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        scaled_height = self.actual_height 

        self.left_panel = ctk.CTkFrame(
            self.root,
            width=scaled_width,
            height=scaled_height,
            fg_color=self._get_color(LEFT_PANEL_COLOR),
            corner_radius=self._scale_value(8, 'x')
        )
        self.left_panel.pack(side="left", fill="y", padx=(0, self._scale_value(10, 'x')), pady=0)
        return self.left_panel

    # ---------------------------------------------------------
    # BUTTONS
    # ---------------------------------------------------------
    def create_record_button(self, x, y, command=None):
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_hover_offset = self._scale_value(1, 'y')

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
            fg_color=self._get_color(LEFT_PANEL_COLOR),
            hover_color=self._get_color(LEFT_PANEL_COLOR),
            corner_radius=0
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
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        x, y = 10, 380
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')

        image_path = "_image_assets/Settings.png"
        img_white = Image.open(image_path).convert("RGBA")
        img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])

        settings_photo = ctk.CTkImage(light_image=img_dark, dark_image=img_white, size=scaled_img_size) 

        btn = ctk.CTkButton(
            self.root,
            text="",
            width=scaled_width,
            height=scaled_height,
            image=settings_photo,
            compound="top",
            command=command,
            fg_color=self._get_color(LEFT_PANEL_COLOR),
            hover_color=self._get_color(LEFT_PANEL_COLOR),
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

    def undo_button(self, command=None):
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        x, y = 5, 380
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')

        image_path = "_image_assets/Undo.png"
        img_white = Image.open(image_path).convert("RGBA")
        img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])
        
        undo_photo = ctk.CTkImage(light_image=img_dark, dark_image=img_white, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root,
            text="",
            width=scaled_width,
            height=scaled_height,
            image=undo_photo,
            compound="top",
            command=command,
            fg_color=self._get_color(LEFT_PANEL_COLOR),
            hover_color=self._get_color(LEFT_PANEL_COLOR),
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

    # ---------------------------------------------------------
    # NAVIGATION AND HARDWARE CLEANUP
    # ---------------------------------------------------------
    def cleanup_camera(self):
        """Releases the camera and turns off the LED/resource."""
        if self.cap and self.cap.isOpened():
            self.running = False 
            self.cap.release()
            cv2.destroyAllWindows()
            print("✅ Camera successfully released.")
        
        if hasattr(self, 'camera_label') and self.camera_label.winfo_exists():
            self.camera_label.destroy()

    def go_back_to_dashboard(self):
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.run()
    
    def camera_to_dashboard(self):
        self.cleanup_camera()
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard 
        dashboard = MyDashboard()
        dashboard.root.mainloop()

    # ---------------------------------------------------------
    # GENERIC WIDGET CREATORS
    # ---------------------------------------------------------
    def load_futures_icon(self, size=(75, 78)):
        scaled_size = (self._scale_value(size[0], 'x'), self._scale_value(size[1], 'y'))
        try:
            image_path = "_image_assets/futures.png"
            img_white = Image.open(image_path).convert("RGBA")
            img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])

            futures_ctk = ctk.CTkImage(
                light_image=img_dark,
                dark_image=img_white,
                size=scaled_size
            )
            return futures_ctk
        except Exception as e:
            print(f"Error loading futures icon: {e}")
            return None

    def create_button(self, text="Button", x=100, y=100, 
                      width=140, height=140, anchor="sw", 
                      command=None, image=None, compound="top",
                      fg_color=BUTTON_COLOR, font=custom_font_bold, corner_radius=8,
                      handle_hover=True, hover_color=BUTTON_HOVER): 
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
            font=tuple(font), 
            fg_color=self._get_color(fg_color),
            hover_color=self._get_color(hover_color), 
            corner_radius=scaled_corner_radius,
            command=command,
            image=image,
            compound=compound,
            text_color=self._get_color(TEXT_COLOR)
        )
        button.place(x=scaled_x, y=scaled_y)

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
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_width = self._scale_value(width, 'x')
        scaled_height = self._scale_value(height, 'y')
        scaled_corner_radius = self._scale_value(8, 'x')
        
        panel = ctk.CTkFrame(
            self.root,
            width=scaled_width,
            height=scaled_height,
            fg_color=self._get_color(LEFT_PANEL_COLOR),
            corner_radius=scaled_corner_radius
        )
        panel.place(x=scaled_x, y=scaled_y, anchor=anchor)

        if text:
            label = ctk.CTkLabel(
                panel,
                text=text,
                font=tuple(custom_font_bold), 
                text_color=self._get_color(TEXT_COLOR), 
                fg_color="transparent",
                image=image,
                compound=compound
            )
            label.place(relx=0.5, rely=0, anchor="n")

        return panel

    def create_weather_analytics_panel(self, x, y, width, height, anchor, command):
        """Creates the composite weather analytics button containing the line chart."""
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')
        
        weather_button = self.create_button(
            text="", 
            x=x, y=y,
            width=width, height=height,
            anchor=anchor,
            command=command, 
            handle_hover=False, 
            hover_color=BUTTON_COLOR 
        )
        weather_button.pack_propagate(False) 

        try:
            icon_size = (self._scale_value(40, 'x'), self._scale_value(40, 'y'))
            image_path = "_image_assets/temperature.png"
            img_white = Image.open(image_path).convert("RGBA")
            img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])

            self.temp_icon = ctk.CTkImage(
                light_image=img_dark,
                dark_image=img_white, 
                size=icon_size
            )
        except Exception as e:
            print(f"Error loading temperature icon: {e}")
            self.temp_icon = None

        shared_button_font = tuple(custom_font_bold)
        
        title_label = ctk.CTkLabel(
            weather_button, 
            text="Analytics", 
            font=shared_button_font, 
            text_color=self._get_color(TEXT_COLOR),
            fg_color="transparent" 
        )
        title_label.pack(pady=(self._scale_value(10, 'y'), 0))

        # Temperature Row (Average)
        temp_frame = ctk.CTkFrame(weather_button, fg_color=self._get_color(BUTTON_COLOR))
        temp_icon_label = ctk.CTkLabel(temp_frame, text="", image=self.temp_icon)
        temp_icon_label.pack(side="left", padx=10)
        self.temp_label = ctk.CTkLabel(temp_frame, text="-- °C", font=shared_button_font, text_color=self._get_color(TEXT_COLOR))
        self.temp_label.pack(side="left", padx=10)
        temp_frame.pack(fill="x", pady=self._scale_value(5, 'y'))
        
        self.recent_date_label = ctk.CTkLabel(
            weather_button,
            text="Date: --",
            font=shared_button_font,
            text_color=self._get_color(TEXT_COLOR),
            fg_color="transparent"
        )
        self.recent_date_label.pack(side="bottom", anchor="w", padx=self._scale_value(10, 'x'), pady=(0, self._scale_value(5, 'y')))

        # Chart Frame and Canvas
        chart_frame = ctk.CTkFrame(weather_button, fg_color="transparent")
        chart_frame.pack(fill="none", expand=True, padx=self._scale_value(5, 'x'), pady=(0, self._scale_value(5, 'y')))
        
        current_bg = self._get_color(BUTTON_COLOR)

        self.chart_fig = Figure(facecolor=current_bg, dpi=100)
        self.chart_ax = self.chart_fig.add_subplot(111, facecolor=current_bg)
        self.chart_fig.subplots_adjust(left=0.18, right=0.95, bottom=0.2, top=0.95)
        
        self.chart_ax.spines['top'].set_visible(False)
        self.chart_ax.spines['right'].set_visible(False)
        self.chart_ax.spines['left'].set_color('white')
        self.chart_ax.spines['bottom'].set_color('white')

        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, master=chart_frame)
        self.chart_canvas_widget = self.chart_canvas.get_tk_widget()
        self.chart_canvas_widget.pack(fill="both", expand=True)

        def on_composite_enter(event):
            weather_button.place_configure(y=scaled_y - scaled_hover_offset)
            hover_color = self._get_color(BUTTON_HOVER)
            weather_button.configure(fg_color=hover_color) 
            title_label.configure(fg_color=hover_color) 
            temp_frame.configure(fg_color=hover_color)
            
            self.chart_fig.set_facecolor(hover_color)
            self.chart_ax.set_facecolor(hover_color)
            self.chart_canvas.draw_idle() 

        def on_composite_leave(event):
            weather_button.place_configure(y=scaled_y)
            normal_color = self._get_color(BUTTON_COLOR)
            weather_button.configure(fg_color=normal_color) 
            title_label.configure(fg_color="transparent")
            temp_frame.configure(fg_color=normal_color)
            
            self.chart_fig.set_facecolor(normal_color)
            self.chart_ax.set_facecolor(normal_color)
            self.chart_canvas.draw_idle()

        widgets_to_bind = [
            weather_button, title_label, temp_frame, temp_icon_label, self.temp_label,
            chart_frame, self.chart_canvas_widget, self.recent_date_label 
        ]
        
        for widget in widgets_to_bind:
             widget.bind("<Button-1>", lambda e, cmd=command: cmd() if cmd else None)
             #widget.bind("<Enter>", on_composite_enter)
             #widget.bind("<Leave>", on_composite_leave)

        return weather_button

    # ---------------------------------------------------------
    # BATTERY INDICATOR & I2C LOOP
    # ---------------------------------------------------------
    def create_battery_indicator(self, x=530, y=21):
        """Creates a MacBook-style battery icon with a depletion bar."""
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        text_c = self._get_color(TEXT_COLOR)

        self.battery_container = ctk.CTkFrame(self.root, fg_color=LEFT_PANEL_COLOR)
        self.battery_container.place(x=scaled_x, y=scaled_y)

        self.battery_body = ctk.CTkFrame(
            self.battery_container,
            width=self._scale_value(45, 'x'),
            height=self._scale_value(20, 'y'),
            border_width=2,
            border_color=text_c, # Fixed hardcoded white
            fg_color="transparent",
            corner_radius=4
        )
        self.battery_body.pack(side="left", padx=(0, 2))
        self.battery_body.pack_propagate(False)

        self.battery_bar = ctk.CTkFrame(
            self.battery_body,
            width=self._scale_value(37, 'x'),
            height=self._scale_value(12, 'y'),
            corner_radius=2,
            fg_color="#4CAF50" # Start Green
        )
        self.battery_bar.place(relx=0.05, rely=0.5, anchor="w")

        self.battery_tip = ctk.CTkFrame(
            self.battery_container,
            width=self._scale_value(3, 'x'),
            height=self._scale_value(8, 'y'),
            fg_color=text_c, # Fixed hardcoded white
            corner_radius=1
        )
        self.battery_tip.pack(side="left")

        self.battery_label = ctk.CTkLabel(
            self.battery_container,
            text="--%",
            font=tuple(custom_font_regular),
            text_color=text_c, # Fixed hardcoded white
            justify="center"
        )
        self.battery_label.pack(side="left", padx=(8, 0), anchor="center")

        # Start the hardware-direct loop
        self._update_battery_loop()

    def _update_battery_loop(self):
        """Simulates battery reading for development/testing without hardware."""
        # Check if we are in a 'simulation' state, if not, initialize it
        if not hasattr(self, '_sim_battery_percent'):
            self._sim_battery_percent = 100.0
            print("🚀 Battery Simulation Started (Development Mode)")

        # --- SIMULATION LOGIC ---
        # Slowly decrease the battery by 1% each time the loop runs
        self._sim_battery_percent -= 1.0
        if self._sim_battery_percent < 0:
            self._sim_battery_percent = 100.0 # Reset to full once it hits 0
            
        p = self._sim_battery_percent
        text_c = self._get_color(TEXT_COLOR)

        # --- 4. Update the UI safely (Same as your original UI logic) ---
        if hasattr(self, 'battery_label') and self.battery_label.winfo_exists():
            self.battery_label.configure(text=f"{int(p)}%")

            max_width = self._scale_value(37, 'x')
            new_width = max(1, int(max_width * (p / 100.0)))
            self.battery_bar.configure(width=new_width)

            # MacBook-style Color & Border Logic
            if p > 20:
                self.battery_bar.configure(fg_color="#4CAF50") # Green
                self.battery_body.configure(border_color=text_c)
                self.battery_label.configure(text_color=text_c)
            elif p > 10:
                self.battery_bar.configure(fg_color="#FFEB3B") # Yellow
                self.battery_body.configure(border_color=text_c)
                self.battery_label.configure(text_color=text_c)
            else:
                self.battery_bar.configure(fg_color="#F44336") # Red warning
                self.battery_body.configure(border_color="#F44336")
                self.battery_label.configure(text_color="#F44336")
                
            # Update faster (every 1 second) during testing so you can see it move
            self.root.after(1000, self._update_battery_loop)