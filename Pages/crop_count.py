import os
import subprocess
import customtkinter as ctk
from language_manager import get_text

def show_crop_input_popup(root, target_button, scale_x_factor, scale_y_factor, scaled_title_font):

    # --- Scaling Helper ---
    def scale_val(value, axis='x'):
        factor = scale_x_factor if axis == 'x' else scale_y_factor
        return max(1, round(value * factor))  # prevent zero sizes
    # ---

    # --- Dimensions ---
    ORIGINAL_POPUP_WIDTH = 300
    ORIGINAL_POPUP_HEIGHT = 180

    popup_width = scale_val(ORIGINAL_POPUP_WIDTH, 'x')
    popup_height = scale_val(ORIGINAL_POPUP_HEIGHT, 'y')

    BUTTON_WIDTH_RATIO = 0.8
    scaled_button_width = round(popup_width * BUTTON_WIDTH_RATIO)

    scaled_label_font_size = scale_val(14, 'y')
    scaled_label_font = ("Arial", scaled_label_font_size, "bold")

    scaled_button_height = scale_val(30, 'y')
    scaled_pady_10 = scale_val(10, 'y')
    scaled_pady_5 = scale_val(5, 'y')

    # --- File Setup ---
    crops_file = os.path.join("Page_files", "crops_monitored.txt")
    os.makedirs(os.path.dirname(crops_file), exist_ok=True)

    if not os.path.exists(crops_file):
        with open(crops_file, "w") as f:
            f.write("0")

    with open(crops_file, "r") as f:
        try:
            existing_value = int(f.read().strip())
        except ValueError:
            existing_value = 0

    # --- Center Popup ---
    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (popup_width // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (popup_height // 2)

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

    # -------------------------
    # ONBOARD KEYBOARD CONTROL
    # -------------------------
    def open_keyboard(event=None):
        try:
            # Try to show existing onboard
            subprocess.run(
                ["onboard", "--show"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            # If something fails, fallback to launching
            subprocess.Popen(["onboard"])

    def close_keyboard():
        subprocess.run(
            ["onboard", "--hide"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    # -------------------------
    # UI ELEMENTS
    # -------------------------
    label = ctk.CTkLabel(
        popup,
        text=get_text("lbl_enter_crops_count"),
        text_color="white",
        font=scaled_label_font
    )
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

    # 👉 Trigger onboard when interacting
    entry.bind("<FocusIn>", open_keyboard)
    entry.bind("<Button-1>", open_keyboard)

    # -------------------------
    # SUBMIT FUNCTION
    # -------------------------
    def on_enter(event=None):
        value = entry.get()

        if value.isdigit():
            num = int(value)

            with open(crops_file, "w") as f:
                f.write(str(num))

            if hasattr(target_button, "number_frame") and target_button.number_frame is not None:
                target_button.number_frame.destroy()

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

            close_keyboard()  # 👈 close onboard
            popup.destroy()

        else:
            entry.delete(0, "end")
            entry.insert(0, get_text("err_number_only"))
            entry.configure(text_color="red")

    entry.bind("<Return>", on_enter)

    # -------------------------
    # BUTTONS
    # -------------------------
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
        close_keyboard()  # 👈 also close here
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