import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk

# Layout and color constant defaults
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480
LEFT_PANEL_WIDTH = 107
LEFT_PANEL_COLOR = "#2A2E3F"
BG_COLOR = "#202332"
BUTTON_COLOR = "#2A2E3F"
BUTTON_HOVER = "#383C4E"

# Use system Helvetica fonts
custom_font_title = ("Arial", 32, "bold")
custom_font_bold = ("Arial", 12, "bold")
custom_font_regular = ("Arial", 12)

class SharedComponents:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Agrivision Dashboard")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(fg_color=BG_COLOR)

    def create_leaf_image(self, image_path="_image_assets/Leaf.png", x=5, y=5, size=(100, 100)):
        leaf_img = Image.open(image_path).convert("RGBA")
        leaf_img = leaf_img.resize(size)

        # Create a background that matches panel color
        transparent_bg = Image.new("RGBA", leaf_img.size, (42, 46, 63))
        transparent_bg.paste(leaf_img, (0, 0), leaf_img)

        leaf_ctk = ctk.CTkImage(light_image=transparent_bg, dark_image=transparent_bg, size=size)
        self.leaf_label = ctk.CTkLabel(self.root, image=leaf_ctk, text="")
        self.leaf_label.place(x=x, y=y)
        self.leaf_label.image = leaf_ctk  
        return self.leaf_label

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
        else:
            self.title_label.configure(text=text)
        return self.title_label

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

    def create_record_button(self, x, y, command=None):
        record_img = Image.open("_image_assets/record.png")
        record_photo = ctk.CTkImage(light_image=record_img, dark_image=record_img, size=(80, 80))
        btn = ctk.CTkButton(
            self.root,
            text="",
            width=90,
            height=90,
            image=record_photo,
            compound="top",
            command=command,
            fg_color="#2A2E3F",
            hover_color="#2A2E3F",
        )
        btn.place(x=x, y=y, anchor="center")
        return btn

    def settings_button(self):
        settings_img = Image.open("_image_assets/Settings.png").resize((80, 80))
        settings_photo = ctk.CTkImage(light_image=settings_img, dark_image=settings_img, size=(80, 80)) 

        btn = ctk.CTkButton(
            self.root,
            text="",
            width=80,
            height=80,
            image=settings_photo,
            compound="top",
            command=None,
            fg_color="#2A2E3F",
            hover_color="#2A2E3F",
            corner_radius=0
        )
        x, y = 10, 380
        btn.place(x=x, y=y)
        btn.image = settings_photo

        def on_enter(event):
            btn.place_configure(y=y - 5)  # Raise up by 5 pixels
        def on_leave(event):
            btn.place_configure(y=y)  # Return to original position

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def undo_button(self):
        undo_img = Image.open("_image_assets/Undo.png")
        undo_photo = ctk.CTkImage(light_image=undo_img, dark_image=undo_img, size=(80, 80))
        btn = ctk.CTkButton(
            self.root,
            text="",
            width=80,
            height=80,
            image=undo_photo,
            compound="top",
            command=self.go_back_to_dashboard,
            fg_color="#2A2E3F",
            hover_color="#2A2E3F",
            corner_radius=0
        )
        x, y = 5, 380
        btn.place(x=x, y=y)
        btn.image = undo_photo

        def on_enter(event):
            btn.place_configure(y=y - 5)
        def on_leave(event):
            btn.place_configure(y=y)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def go_back_to_dashboard(self):
        geometry = self.root.geometry()
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard
        dashboard = MyDashboard()
        dashboard.root.geometry(geometry)
        dashboard.root.mainloop()

    def load_futures_icon(self, size=(75, 78)):
        try:
            futures_img = Image.open("_image_assets/futures.png")
            futures_ctk = ctk.CTkImage(light_image=futures_img, dark_image=futures_img, size=size)
            return futures_ctk
        except Exception as e:
            print(f"Error loading futures icon: {e}")
            return None

    def create_button(self, text="Button", x=100, y=100, 
                      width=140, height=140, anchor="sw", 
                      command=None, image=None, compound="top",
                      fg_color=BUTTON_COLOR, font=custom_font_bold, corner_radius=8):
        button = ctk.CTkButton(
            self.root,
            width=width,
            height=height,
            text=text,
            anchor=anchor,
            font=font,
            fg_color=fg_color,
            hover_color=BUTTON_COLOR,
            corner_radius=corner_radius,
            command=command,
            image=image,
            compound=compound,
        )
        button.place(x=x, y=y)

        def on_enter(event):
            button.place_configure(y=y - 5)
        def on_leave(event):
            button.place_configure(y=y)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        return button

    def create_panel(self, text="", x=100, y=100, 
                     width=140, height=140, anchor="nw", 
                     image=None, compound="top"):
        panel = ctk.CTkFrame(
            self.root,
            width=width,
            height=height,
            fg_color=LEFT_PANEL_COLOR,
            corner_radius=8
        )
        panel.place(x=x, y=y, anchor=anchor)

        if text:
            label = ctk.CTkLabel(
                panel,
                text=text,
                font=custom_font_bold,
                text_color="#FFFFFF",
                fg_color="transparent",
                image=image,
                compound=compound
            )
            label.place(relx=0.5, rely=0, anchor="n")

        return panel
