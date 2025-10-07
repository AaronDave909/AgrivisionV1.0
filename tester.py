import customtkinter as ctk
import os
from viewer import list_items, open_pdf  # Assuming viewer.py holds your functions


def open_file_manager(main_window):
    """
    Opens a file manager gallery for the '_reports_' folder.
    Displays files/folders as clickable tiles in a grid layout.
    """
    folder_name = "_reports_"

    # Hide main window (collapse it)
    main_window.withdraw()

    # Make sure the folder exists (directly handled here)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Create gallery window
    manager = ctk.CTkToplevel()
    manager.title("Reports File Manager Gallery")
    manager.geometry("900x700")

    # Function to return to main window
    def return_to_main():
        manager.destroy()
        main_window.deiconify()  # Show the main window again

    # Top bar with return button
    top_bar = ctk.CTkFrame(manager, fg_color="transparent")
    top_bar.pack(fill="x", pady=10, padx=10)

    back_button = ctk.CTkButton(top_bar, text="← Return", width=100, command=return_to_main)
    back_button.pack(anchor="w")

    # Scrollable area
    frame = ctk.CTkScrollableFrame(manager, width=880, height=620)
    frame.pack(padx=10, pady=10, fill="both", expand=True)

    # Get items from folder
    items = list_items(folder_name)

    if not items:
        ctk.CTkLabel(frame, text="The _reports_ folder is empty").pack(pady=20)
        return

    # Emoji icons for file types
    folder_icon = "📁"
    pdf_icon = "📄"
    file_icon = "📦"

    # Grid layout
    columns = 4
    for index, item in enumerate(items):
        item_path = os.path.join(folder_name, item)
        ext = os.path.splitext(item)[1].lower()

        # Select icon
        if os.path.isdir(item_path):
            icon = folder_icon
        elif ext == ".pdf":
            icon = pdf_icon
        else:
            icon = file_icon

        # Tile container
        tile = ctk.CTkFrame(frame, width=180, height=140, corner_radius=12)
        tile.grid(row=index // columns, column=index % columns, padx=10, pady=10, sticky="nsew")

        # Icon label
        icon_label = ctk.CTkLabel(tile, text=icon, font=("Arial", 48))
        icon_label.pack(pady=(10, 0))

        # File/folder name label
        display_name = item if len(item) <= 20 else item[:17] + "..."
        name_label = ctk.CTkLabel(tile, text=display_name, wraplength=160)
        name_label.pack(pady=(5, 10))

        # Click handlers
        for widget in (tile, icon_label, name_label):
            widget.bind("<Button-1>", lambda e, path=item_path: open_pdf(path))


def main_app():
    """Main GUI entry point."""
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("Main App")
    app.geometry("400x200")

    open_button = ctk.CTkButton(app, text="Open Reports Gallery", command=lambda: open_file_manager(app))
    open_button.pack(expand=True, pady=40)

    app.mainloop()


if __name__ == "__main__":
    main_app()
