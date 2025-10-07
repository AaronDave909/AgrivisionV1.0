import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageFont, ImageTk

# Paths to custom font files
FONT_BOLD = "Main Font Folder/AOTFShinGoProHeavy.otf"
FONT_REGULAR = "Main Font Folder/AOTFShinGoProRegular.otf"


def load_custom_font(path, size):
    try:
        pil_font = ImageFont.truetype(path, size)
        return (pil_font.getname()[0], size)  # returns tuple (FontName, size)
    except Exception as e:
        print(f"Error loading font: {e}")
        return ("TkDefaultFont", size)

custom_font_title = load_custom_font(FONT_BOLD, 32)
custom_font_bold = load_custom_font(FONT_BOLD, 12)
custom_font_regular = load_custom_font(FONT_REGULAR, 12)

# Layout and color constant defaults
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480
LEFT_PANEL_WIDTH = 107
LEFT_PANEL_COLOR = "#2A2E3F"
BG_COLOR = "#202332"
BUTTON_COLOR = "#2A2E3F"
BUTTON_HOVER = "#383C4E"
BUTTON_FONT = custom_font_bold

# default config for dashboard buttons
DASHBOARD_BUTTONS_CONFIG = [
    {
        "text": "Crops in Monitor\n",
        "x": 118, "y": 75, "width": 140, "height": 140, "anchor": "sw"
    },
    {
        "text": " Recent Diseases \n Detected",
        "x": 270, "y": 75, "width": 140, "height": 140, "anchor": "s"
    },
    {
        "text": "Manage Files\n",
        "x": 422, "y": 75, "width": 140, "height": 140, "anchor": "sw"
    },
    {
        "text": "Analytics",
        "x": 121, "y": 232, "width": 205, "height": 229, "anchor": "nw"
    },
    {
        "text": "Capture Gallery",
        "x": 340, "y": 232, "width": 222, "height": 229, "anchor": "nw"
    },
    {
        "text": "Disease Record History",
        "x": 572, "y": 75, "width": 217, "height": 386, "anchor": "n"
    }
]

class SharedComponents:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Agrivision Dashboard")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(fg_color=BG_COLOR)

    def create_leaf_image(self, image_path="Image Assets/Leaf.png", x=5, y=5, size=(100, 100)):
        leaf_img = Image.open(image_path).convert("RGBA")
        leaf_img = leaf_img.resize(size)
        bg_color = BUTTON_COLOR
        background = Image.new("RGBA", leaf_img.size, bg_color)
        background.paste(leaf_img, (0, 0), leaf_img)
        self.leaf_photo = ImageTk.PhotoImage(background)
        self.leaf_label = ctk.CTkLabel(self.root, image=self.leaf_photo, text="")
        self.leaf_label.place(x=x, y=y)
        self.leaf_label.image = self.leaf_photo  # Prevent garbage collection
        return self.leaf_label
    # use this def to create the title
    def create_title(self, text="AGRIVISION v1.0", x=119, y=0):
        if not hasattr(self, "title_label"):  # create only once
            self.title_label = ctk.CTkLabel(
                self.root,
                text=text,
                font=custom_font_title,
                text_color="#FFFFFF",
                fg_color=BG_COLOR
            )
            self.title_label.place(x=x, y=y)
        else:  # update text if already exists
            self.title_label.configure(text=text)
        return self.title_label


    # use this def to create the left panel
    def create_left_panel(self):
        self.left_panel = ctk.CTkFrame(
            self.root,
            width=LEFT_PANEL_WIDTH,
            height=WINDOW_HEIGHT,
            fg_color=LEFT_PANEL_COLOR,
            corner_radius=8
        )
        self.left_panel.pack(side="left", fill="y", padx=(0, 10), pady=0)
        return self.left_panel

    # use this def to create buttons
    def create_button(self, text="Button", x=100, y=100, 
                      width=140, height=140, anchor="sw", 
                      command=None, image=None, compound="top"):
        button = ctk.CTkButton(
            self.root,
            width=width,
            height=height,
            text=text,
            anchor=anchor,
            font=BUTTON_FONT,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_COLOR,
            corner_radius=8,
            command=command,
            image=image,
            compound=compound
        )
        button.place(x=x, y=y)

        def on_enter(event):
            button.place_configure(y=y-5)  # Move up by 5 pixels

        def on_leave(event):
            button.place_configure(y=y)    # Move back to original position

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

        return button
        