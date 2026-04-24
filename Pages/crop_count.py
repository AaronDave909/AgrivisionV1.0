import os
import customtkinter as ctk

from language_manager import get_text

def show_crop_input_popup(root, target_button, scale_x_factor, scale_y_factor, scaled_title_font):

    # --- Scaling Helper ---
    def scale_val(value, axis='x'):
        factor = scale_x_factor if axis == 'x' else scale_y_factor
        return round(value * factor)
    # ---

    # --- Scale the original fixed dimensions ---
    ORIGINAL_POPUP_WIDTH = 300
    ORIGINAL_POPUP_HEIGHT = 180
    
    # 1. Calculate base scaled dimensions first
    popup_width = scale_val(ORIGINAL_POPUP_WIDTH, 'x')
    popup_height = scale_val(ORIGINAL_POPUP_HEIGHT, 'y')

    # 2. THEN calculate dimensions dependent on the popup size
    BUTTON_WIDTH_RATIO = 0.8
    scaled_button_width = round(popup_width * BUTTON_WIDTH_RATIO) 
    
    # Define internal font size (Original 14pt bold)
    scaled_label_font_size = scale_val(14, 'y')
    # Assuming you want bold for the button/label text inside the popup:
    scaled_label_font = ("Arial", scaled_label_font_size, "bold") 
    
    # Define button height and padding
    scaled_button_height = scale_val(30, 'y')
    scaled_pady_10 = scale_val(10, 'y')
    scaled_pady_5 = scale_val(5, 'y')

    # Ensure the folder and file exist
    crops_file = os.path.join("Page_files", "crops_monitored.txt")
    os.makedirs(os.path.dirname(crops_file), exist_ok=True)
    if not os.path.exists(crops_file):
        with open(crops_file, "w") as f:
            f.write("0")

    # Read existing crop count
    with open(crops_file, "r") as f:
        try:
            existing_value = int(f.read().strip())
        except ValueError:
            existing_value = 0

    # Scale Position Calculation (Centered on Root Window)
    root.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width() 
    root_height = root.winfo_height() 
    
    x = root_x + (root_width // 2) - (popup_width // 2)
    y = root_y + (root_height // 2) - (popup_height // 2)

    popup = ctk.CTkToplevel(root)
    popup.title(get_text("win_crops_monitor"))
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
    popup.configure(fg_color="#202332")
    popup.transient(root) 

    popup.after(50, lambda: (
        popup.lift(),                    
        popup.focus_force(),             
        popup.grab_set()                 
    ))

    label = ctk.CTkLabel(
        popup, 
        text=get_text("lbl_enter_crops_count"), 
        text_color="white", 
        font=scaled_label_font)
    label.pack(pady=scaled_pady_10)

    entry = ctk.CTkEntry(
        popup,
        justify="center",
        fg_color="#333645",
        text_color="#FFFFFF",
        width=scaled_button_width,
        font=scaled_label_font 
    )
    entry.insert(0, str(existing_value))
    entry.pack(pady=scaled_pady_5)

    def on_enter(event=None):
        value = entry.get()
        if value.isdigit():
            num = int(value)

            with open(crops_file, "w") as f:
                f.write(str(num))

            # Remove old label (if any)
            if hasattr(target_button, "number_frame") and target_button.number_frame is not None:
                target_button.number_frame.destroy()

            # Add updated label
            frame = ctk.CTkFrame(target_button, fg_color="transparent")
            frame.place(relx=0.15, rely=0.2, anchor="nw")
            num_label = ctk.CTkLabel(
                frame,
                text=str(num),
                font=scaled_title_font, 
                text_color="white",
                fg_color="transparent"
            )
            num_label.pack()
            target_button.number_frame = frame

            target_button.configure(text=f"{get_text('lbl_crops_monitor')}\n")
            popup.destroy()

        else:
            entry.delete(0, "end")
            entry.insert(0, get_text("err_number_only")) 
            entry.configure(text_color="red")

    entry.bind("<Return>", on_enter)

    # Both buttons now use the same, calculated width and height
    submit_btn = ctk.CTkButton(
        popup,
        text=get_text("btn_enter_submit"),
        command=on_enter,
        fg_color="#2A2E3F",
        hover_color="#383C4E",
        height=scaled_button_height,
        width=scaled_button_width,
        font=scaled_label_font
    )
    submit_btn.pack(pady=scaled_pady_10)

    def return_to_dashboard():
        popup.destroy()

    return_btn = ctk.CTkButton(
        popup,
        text=get_text("btn_back_to_dashboard"),
        command=return_to_dashboard,
        fg_color="#2A2E3F",
        hover_color="#383C4E",
        height=scaled_button_height,
        width=scaled_button_width,
        font=scaled_label_font
    )
    return_btn.pack(pady=scaled_pady_5)

    popup.after(100, entry.focus_set)
    root.wait_window(popup)