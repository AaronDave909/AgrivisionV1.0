import customtkinter as ctk
from shared_components import SharedComponents 

def show_crop_input_popup(root, target_button):
    popup_width = 300
    popup_height = 180

    # Update root to get correct geometry
    root.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    x = root_x + (root_width // 2) - (popup_width // 2)
    y = root_y + (root_height // 2) - (popup_height // 2)

    # Create popup window
    popup = ctk.CTkToplevel(root)
    popup.title("Crops in Monitor")
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
    popup.grab_set()
    popup.lift()
    popup.configure(fg_color="#202332")

    label = ctk.CTkLabel(popup, text="Enter number of crops:")
    label.pack(pady=10)

    entry = ctk.CTkEntry(popup, justify="center", fg_color="#333645", text_color="#FFFFFF")
    entry.pack(pady=5)

    def on_enter(event=None):
        value = entry.get()
        if value.isdigit():
            num = int(value)
            if hasattr(target_button, "number_frame") and target_button.number_frame is not None:
                target_button.number_frame.destroy()
            frame = ctk.CTkFrame(target_button, fg_color="transparent")
            frame.place(relx=0.15, rely=0.2, anchor="nw")  # upper left
            num_label = ctk.CTkLabel(frame, text=str(num), font=("Arial", 32, "bold"), fg_color="transparent")
            num_label.pack()
            target_button.number_frame = frame
            target_button.configure(text="Crops in Monitor\n")
            popup.destroy()
        else:
            entry.delete(0, "end")
            entry.insert(0, "Enter number only")

    entry.bind("<Return>", on_enter)

    submit_btn = ctk.CTkButton(
        popup, text="Enter", command=on_enter, fg_color="#2A2E3F", hover_color="#383C4E"
    )
    submit_btn.pack(pady=10)

    def return_to_dashboard():
        popup.destroy()

    return_btn = ctk.CTkButton(
        popup, text="Return to Dashboard", command=return_to_dashboard, fg_color="#2A2E3F", hover_color="#383C4E"
    )
    return_btn.pack(pady=5)

    entry.focus_set()