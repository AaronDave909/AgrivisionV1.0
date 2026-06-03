from language_manager import get_text
from shared_components import (
    SharedComponents as SC, custom_font_bold, custom_font_regular, 
    LEFT_PANEL_WIDTH, LEFT_PANEL_COLOR, BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR, BG_COLOR
)
import customtkinter as ctk
import json
import os
import re
from datetime import datetime, timedelta
from PIL import Image
from fpdf import FPDF
import fitz  # PyMuPDF for viewing the PDF inside Tkinter

class ReportPage(SC):
    def __init__(self):
        super().__init__()
        
        # 1. Initialize attributes immediately to prevent AttributeErrors
        self.viewer_frame = None 
        self.selected_diseases = {}  
        self.selected_pests = {}  
        self.current_view = "create"
        
        # Tracks the currently open report for the master delete button
        self.current_viewed_report = None 
        self.del_btn = None
        self.gen_btn = None
        
        # Variables to track touch/mouse drag positions
        self._drag_start_y = 0 
        self._left_drag_start_y = 0 
        
        self.create_title(text=get_text("title_report"), x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        self.undo_button(command=self.go_back_to_dashboard)
        
        # 2. Load the data
        self.data = self.load_json_data()
        self.months = self.get_unique_months()
        self.diseases = self.get_unique_diseases()
        self.pests = self.get_unique_pests()   

        self.setup_ui()

    # --- Touch Scrolling Logic for RIGHT PANEL (PDF Viewer) ---
    def _start_pan(self, event):
        """Records the starting Y coordinate when the user touches/clicks the PDF viewer."""
        self._drag_start_y = event.y_root

    def _pan(self, event):
        """Calculates the drag distance and scrolls the PDF viewer."""
        delta = self._drag_start_y - event.y_root
        if abs(delta) > 2:
            self.viewer_frame._parent_canvas.yview_scroll(int(delta / 3), "units")
            self._drag_start_y = event.y_root

    # --- Touch Scrolling Logic for LEFT PANEL (Filters/List) ---
    def _start_pan_left(self, event):
        """Records the starting Y coordinate when the user touches the left panel."""
        self._left_drag_start_y = event.y_root

    def _pan_left(self, event):
        """Calculates the drag distance and scrolls the active left panel."""
        delta = self._left_drag_start_y - event.y_root
        if abs(delta) > 2:
            # Scroll whichever container is currently active
            if self.current_view == "create":
                self.create_container._parent_canvas.yview_scroll(int(delta / 3), "units")
            else:
                self.view_container._parent_canvas.yview_scroll(int(delta / 3), "units")
            self._left_drag_start_y = event.y_root

    # --- Helper to bind scrolling to all child widgets ---
    def _bind_scrolling(self, widget):
        """Recursively binds the pan events to a widget and all its children."""
        # Critical: add="+" prevents the scroll binding from overwriting the button's command
        widget.bind("<ButtonPress-1>", self._start_pan_left, add="+")
        widget.bind("<B1-Motion>", self._pan_left, add="+")
        
        if hasattr(widget, "_canvas"):
            widget._canvas.bind("<ButtonPress-1>", self._start_pan_left, add="+")
            widget._canvas.bind("<B1-Motion>", self._pan_left, add="+")
        if hasattr(widget, "_text_label"):
            widget._text_label.bind("<ButtonPress-1>", self._start_pan_left, add="+")
            widget._text_label.bind("<B1-Motion>", self._pan_left, add="+")
            
        for child in widget.winfo_children():
            self._bind_scrolling(child)

    def load_json_data(self):
        try:
            gallery_path = "Page_files/gallery_files/gallery_data.json"
            if os.path.exists(gallery_path):
                with open(gallery_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"{get_text('err_loading_json')}: {e}")
            return {}

    def get_unique_months(self):
        month_set = set()
        for key, val in self.data.items():
            try:
                dt = datetime.strptime(val["timestamp"], "%b %d, %Y %I:%M %p")
                month_set.add(dt.strftime("%B %Y"))  
            except:
                pass
        return sorted(list(month_set), key=lambda m: datetime.strptime(m, "%B %Y"))

    def get_unique_diseases(self):
        diseases = set()
        for key, val in self.data.items():
            disease = val.get("disease")
            if disease and disease != "None":
                diseases.add(disease)
        return sorted(list(diseases))

    def get_unique_pests(self):
        pests = set()
        for key, val in self.data.items():
            pest = val.get("pest")
            if pest and pest != "None":
                pests.add(pest)
        return sorted(list(pests))

    def setup_ui(self):
        # --- LEFT PANEL BUTTONS (Create/View) ---
        scaled_button_width = self._scale_value(100, 'x')
        scaled_button_height = self._scale_value(40, 'y')
        scaled_padding = self._scale_value(10, 'y')
        
        x_pos = self._scale_value(LEFT_PANEL_WIDTH / 2, 'x')
        y_create = self._scale_value(150, 'y')
        y_view = y_create + scaled_button_height + scaled_padding
        
        btn_font = ("Arial", 14)
        
        self.create_tab_btn = ctk.CTkButton(
            self.left_panel, text=get_text("btn_create"), 
            width=scaled_button_width, height=scaled_button_height,
            command=self.show_create_view,
            fg_color=self._get_color(BUTTON_HOVER), 
            hover_color=self._get_color(BUTTON_HOVER),
            corner_radius=20, text_color=self._get_color(TEXT_COLOR), font=btn_font
        )
        self.create_tab_btn.place(x=x_pos, y=y_create, anchor="center")
        
        self.view_tab_btn = ctk.CTkButton(
            self.left_panel, text=get_text("btn_view"), 
            width=scaled_button_width, height=scaled_button_height,
            command=self.show_view_list,
            fg_color=self._get_color(LEFT_PANEL_COLOR), 
            hover_color=self._get_color(BUTTON_HOVER),
            corner_radius=20, text_color=self._get_color(TEXT_COLOR), font=btn_font
        )
        self.view_tab_btn.place(x=x_pos, y=y_view, anchor="center")
        
        # --- PDF VIEWER SECTION (Right Side) ---
        self.viewer_frame = ctk.CTkScrollableFrame(
            self.root, 
            fg_color=self._get_color(BUTTON_COLOR),
            width=self._scale_value(390, 'x'), 
            height=self._scale_value(400, 'y')
        )
        self.viewer_frame.place(x=self._scale_value(390, 'x'), y=self._scale_value(60, 'y'))
        
        self.viewer_frame._parent_canvas.bind("<ButtonPress-1>", self._start_pan)
        self.viewer_frame._parent_canvas.bind("<B1-Motion>", self._pan)
        
        self.viewer_placeholder = ctk.CTkLabel(
            self.viewer_frame, 
            text=get_text("viewer_placeholder"),
            text_color="gray"
        )
        self.viewer_placeholder.pack(pady=50)
        
        self.viewer_placeholder.bind("<ButtonPress-1>", self._start_pan)
        self.viewer_placeholder.bind("<B1-Motion>", self._pan)

        # --- FILTER/CONTENT SECTION (Center-Left) ---
        self.filter_frame = ctk.CTkFrame(
            self.root, fg_color="transparent",
            width=self._scale_value(250, 'x'), 
            height=self._scale_value(400, 'y')
        )
        self.filter_frame.place(x=self._scale_value(120, 'x'), y=self._scale_value(60, 'y'))
        self.filter_frame.pack_propagate(False)

        # --- CONTAINERS FOR THE TWO MODES ---
        self.create_container = ctk.CTkScrollableFrame(self.filter_frame, fg_color="transparent", height=self._scale_value(300, 'y'))
        self.view_container = ctk.CTkScrollableFrame(self.filter_frame, fg_color="transparent", height=self._scale_value(300, 'y'))
        
        # Bind scrolling to the empty containers themselves
        self.create_container._parent_canvas.bind("<ButtonPress-1>", self._start_pan_left)
        self.create_container._parent_canvas.bind("<B1-Motion>", self._pan_left)
        self.view_container._parent_canvas.bind("<ButtonPress-1>", self._start_pan_left)
        self.view_container._parent_canvas.bind("<B1-Motion>", self._pan_left)

        self.build_create_ui()
        self.create_container.place(x=0, y=0, relwidth=1.0) 

        # --- FIXED BOTTOM BUTTONS ---
        self.gen_btn = ctk.CTkButton(
            self.filter_frame,
            text=get_text("btn_gen_report"),
            font=tuple(custom_font_bold),
            fg_color=self._get_color(BUTTON_COLOR),
            hover_color=self._get_color(BUTTON_HOVER),
            text_color=self._get_color(TEXT_COLOR),
            command=self.generate_and_display_report,
            width=self._scale_value(230, 'x'),
            height=self._scale_value(40, 'y')
        )
        self.gen_btn.place(x=self._scale_value(10, 'x'), y=self._scale_value(320, 'y'))

        # Bluetooth Share Button (Left Side)
        self.share_btn = ctk.CTkButton(
            self.filter_frame,
            text=get_text("btn_share"),
            font=tuple(custom_font_bold),
            fg_color="#2980b9", # Bluetooth Blue
            hover_color="#3498db",
            text_color="white", # Keep white for contrast on blue
            command=self.share_via_bluetooth,
            width=self._scale_value(110, 'x'), # Half width
            height=self._scale_value(40, 'y')
        )

        # Delete Button (Right Side)
        self.del_btn = ctk.CTkButton(
            self.filter_frame,
            text=get_text("btn_delete"),
            font=tuple(custom_font_bold),
            fg_color="#CC0000", # Red
            hover_color="#FF4C4C",
            text_color="white", # Keep white for contrast on red
            command=self.trigger_delete,
            width=self._scale_value(110, 'x'), # Half width
            height=self._scale_value(40, 'y')
        )

    def build_create_ui(self):
        """Builds the Date Range and Checkboxes inside the Create Container."""
        lbl_date = ctk.CTkLabel(self.create_container, text=get_text("lbl_date_range"), font=tuple(custom_font_bold), text_color=self._get_color(TEXT_COLOR))
        lbl_date.pack(anchor="w", pady=(10, 5), padx=10)
        
        lbl_from = ctk.CTkLabel(self.create_container, text=get_text("lbl_from"), font=tuple(custom_font_regular), text_color=self._get_color(TEXT_COLOR))
        lbl_from.pack(anchor="w", pady=(0, 2), padx=10)
        
        menu_bg = self._get_color(BUTTON_COLOR)
        menu_text = self._get_color(TEXT_COLOR)
        menu_hover = self._get_color(BUTTON_HOVER)

        self.month_from_var = ctk.StringVar(value=self.months[0] if self.months else "")
        month_from_dropdown = ctk.CTkOptionMenu(
            self.create_container, 
            values=self.months, 
            variable=self.month_from_var,
            font=("Arial", 14), dropdown_font=("Arial", 14),
            fg_color=self._get_color(BUTTON_COLOR), 
            text_color=self._get_color(TEXT_COLOR), 
            button_color=self._get_color(BUTTON_HOVER), 
            button_hover_color=self._get_color(BUTTON_HOVER),
            dropdown_fg_color=menu_bg, 
            dropdown_hover_color=menu_hover, 
            dropdown_text_color=menu_text
        )
        month_from_dropdown.pack(fill="x", pady=(0, 10), padx=10)
        
        lbl_to = ctk.CTkLabel(self.create_container, text=get_text("lbl_to"), font=tuple(custom_font_regular), text_color=self._get_color(TEXT_COLOR))
        lbl_to.pack(anchor="w", pady=(0, 2), padx=10)
        
        self.month_to_var = ctk.StringVar(value=self.months[-1] if self.months else "")
        month_to_dropdown = ctk.CTkOptionMenu(
            self.create_container, 
            values=self.months, 
            variable=self.month_to_var,
            font=("Arial", 14), dropdown_font=("Arial", 14),
            fg_color=self._get_color(BUTTON_COLOR), 
            text_color=self._get_color(TEXT_COLOR), 
            button_color=self._get_color(BUTTON_HOVER), 
            button_hover_color=self._get_color(BUTTON_HOVER),
            dropdown_fg_color=menu_bg, 
            dropdown_hover_color=menu_hover, 
            dropdown_text_color=menu_text
        )
        month_to_dropdown.pack(fill="x", pady=(0, 15), padx=10)

        lbl_dis = ctk.CTkLabel(self.create_container, text=get_text("lbl_select_diseases"), font=tuple(custom_font_bold), text_color=self._get_color(TEXT_COLOR))
        lbl_dis.pack(anchor="w", pady=(0, 5), padx=10)
        
        disease_frame = ctk.CTkScrollableFrame(self.create_container, height=self._scale_value(65, 'y'), fg_color=self._get_color(BUTTON_COLOR))
        disease_frame.pack(fill="x", pady=(0, 10), padx=10)

        if self.diseases:
            for disease in self.diseases:
                var = ctk.BooleanVar(value=True) 
                cb = ctk.CTkCheckBox(disease_frame, text=disease.replace("_", " "), variable=var, text_color=self._get_color(TEXT_COLOR))
                cb.pack(anchor="w", pady=3, padx=5)
                self.selected_diseases[disease] = var
        else:
            ctk.CTkLabel(disease_frame, text=get_text("lbl_no_diseases"), text_color="gray").pack()

        lbl_pest = ctk.CTkLabel(self.create_container, text=get_text("lbl_select_pests"), font=tuple(custom_font_bold), text_color=self._get_color(TEXT_COLOR))
        lbl_pest.pack(anchor="w", pady=(0, 5), padx=10)
        
        pest_frame = ctk.CTkScrollableFrame(self.create_container, height=self._scale_value(65, 'y'), fg_color=self._get_color(BUTTON_COLOR))
        pest_frame.pack(fill="x", pady=(0, 15), padx=10)

        if self.pests:
            for pest in self.pests:
                var = ctk.BooleanVar(value=True) 
                cb = ctk.CTkCheckBox(pest_frame, text=pest.replace("_", " "), variable=var, text_color=self._get_color(TEXT_COLOR))
                cb.pack(anchor="w", pady=3, padx=5)
                self.selected_pests[pest] = var
        else:
            ctk.CTkLabel(pest_frame, text=get_text("lbl_no_pests"), text_color="gray").pack()

        self._bind_scrolling(self.create_container)

    def show_create_view(self):
        self.current_view = "create"
        self.view_container.place_forget()

        if hasattr(self, 'del_btn'): self.del_btn.place_forget()
        if hasattr(self, 'share_btn'): self.share_btn.place_forget()

        self.create_container.place(x=0, y=0, relwidth=1.0)
        self.gen_btn.place(x=self._scale_value(10, 'x'), y=self._scale_value(320, 'y'))

        self.create_tab_btn.configure(fg_color=self._get_color(BUTTON_HOVER), hover_color=self._get_color(BUTTON_HOVER))
        self.view_tab_btn.configure(fg_color=self._get_color(LEFT_PANEL_COLOR), hover_color=self._get_color(BUTTON_HOVER))

    def show_view_list(self):
        self.current_view = "view"
        self.create_container.place_forget()

        if hasattr(self, 'gen_btn'): self.gen_btn.place_forget()

        self.view_container.place(x=0, y=0, relwidth=1.0)
        
        # Place Share on the left (x=10)
        self.share_btn.place(x=self._scale_value(10, 'x'), y=self._scale_value(320, 'y'))
        # Place Delete on the right (x=130)
        self.del_btn.place(x=self._scale_value(130, 'x'), y=self._scale_value(320, 'y'))

        self.view_tab_btn.configure(fg_color=self._get_color(BUTTON_HOVER), hover_color=self._get_color(BUTTON_HOVER))
        self.create_tab_btn.configure(fg_color=self._get_color(LEFT_PANEL_COLOR), hover_color=self._get_color(BUTTON_HOVER))

        self.refresh_reports_list()

    def share_via_bluetooth(self):
        """Triggers the Raspberry Pi system Bluetooth file transfer."""
        if not self.current_viewed_report or not os.path.exists(self.current_viewed_report):
            return

        import subprocess
        
        # UI Feedback: Change button text temporarily
        original_text = self.share_btn.cget("text")
        original_color = self.share_btn.cget("fg_color")
        self.share_btn.configure(text="Launching...", fg_color="#2980b9")
        self.root.update_idletasks()

        try:
            subprocess.Popen(['blueman-sendto', self.current_viewed_report])
            
            print(f"✓ {get_text('log_bluetooth_launched')}: {self.current_viewed_report}")
            
        except FileNotFoundError:
            for widget in self.viewer_frame.winfo_children():
                widget.destroy()
            
            lbl = ctk.CTkLabel(
                self.viewer_frame, 
                text=get_text("err_bluetooth_tools_missing"), 
                text_color="red"
            )
            lbl.pack(pady=20)
        
        # Reset the button back to normal after 2 seconds
        self.root.after(2000, lambda: self.share_btn.configure(text=original_text, fg_color=original_color))

    def refresh_reports_list(self):
        for widget in self.view_container.winfo_children():
            widget.destroy()

        reports_dir = "_reports_"
        os.makedirs(reports_dir, exist_ok=True)
        
        reports = [f for f in os.listdir(reports_dir) if f.endswith('.pdf')]
        reports.sort(reverse=True)

        if not reports:
            lbl = ctk.CTkLabel(self.view_container, text=get_text("lbl_no_reports"), text_color="gray")
            lbl.pack(pady=20)
            self._bind_scrolling(lbl)
            return

        for report in reports:
            btn = ctk.CTkButton(
                self.view_container,
                text=report,
                anchor="w", 
                fg_color=self._get_color(BUTTON_COLOR),
                hover_color=self._get_color(BUTTON_HOVER),
                text_color=self._get_color(TEXT_COLOR),
                command=lambda r=report: self.render_pdf_to_viewer(os.path.join(reports_dir, r))
            )
            btn.pack(fill="x", pady=2, padx=5)
            self._bind_scrolling(btn)

    def trigger_delete(self):
        if not self.current_viewed_report or not os.path.exists(self.current_viewed_report):
            return 

        report_filename = os.path.basename(self.current_viewed_report)
        self.confirm_delete_report(report_filename)

    def confirm_delete_report(self, report_filename):
        def scale_val(value, axis='x'):
            factor = self.scale_x if axis == 'x' else self.scale_y
            return round(value * factor)

        popup_width = scale_val(300, 'x')
        popup_height = scale_val(150, 'y')

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (popup_width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (popup_height // 2)

        popup = ctk.CTkToplevel(self.root)
        popup.title(get_text("title_delete_report"))
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        popup.configure(fg_color=self._get_color(BG_COLOR))
        popup.transient(self.root)
        
        popup.after(50, lambda: (popup.lift(), popup.focus_force(), popup.grab_set()))

        label = ctk.CTkLabel(
            popup, 
            # In your UI code:
            text = get_text("msg_confirm_delete").replace("{filename}", report_filename), 
            text_color=self._get_color(TEXT_COLOR), 
            font=("Arial", scale_val(12, 'y'), "bold")
        )
        label.pack(pady=scale_val(20, 'y'))

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=scale_val(20, 'x'))

        def on_delete():
            try:
                report_path = os.path.join("_reports_", report_filename)
                os.remove(report_path)
                print(f"✓ {get_text('log_report_deleted')}: {report_path}")
                
                if self.current_viewed_report == report_path:
                    for widget in self.viewer_frame.winfo_children():
                        widget.destroy()
                    self.viewer_placeholder = ctk.CTkLabel(self.viewer_frame, text=get_text("viewer_placeholder"), text_color="gray")
                    self.viewer_placeholder.pack(pady=50)
                    self.viewer_placeholder.bind("<ButtonPress-1>", self._start_pan)
                    self.viewer_placeholder.bind("<B1-Motion>", self._pan)
                    self.current_viewed_report = None
                    
            except Exception as e:
                print(f"⚠︎ {get_text('log_err_delete_report')}: {e}")
                
            
            popup.destroy()
            self.refresh_reports_list()

        del_btn = ctk.CTkButton(
            btn_frame, text=get_text("btn_delete"), fg_color="#FF4C4C", hover_color="#CC0000", 
            text_color="white", width=scale_val(100, 'x'), command=on_delete
        )
        del_btn.pack(side="left", expand=True, padx=5)

        cancel_btn = ctk.CTkButton(
            btn_frame, text=get_text("btn_cancel"), fg_color=self._get_color(BUTTON_COLOR), hover_color=self._get_color(BUTTON_HOVER), 
            text_color=self._get_color(TEXT_COLOR), width=scale_val(100, 'x'), command=popup.destroy
        )
        cancel_btn.pack(side="right", expand=True, padx=5)

    def generate_and_display_report(self):
        if not self.months:
            return

        month_from = self.month_from_var.get()
        month_to = self.month_to_var.get()
        active_diseases = [dis for dis, var in self.selected_diseases.items() if var.get()]
        active_pests = [pest for pest, var in self.selected_pests.items() if var.get()]
        
        filtered_data = []
        
        try:
            from_date = datetime.strptime(month_from, "%B %Y")
            to_date = datetime.strptime(month_to, "%B %Y")
            
            if from_date > to_date:
                from_date, to_date = to_date, from_date
            
            if to_date.month == 12:
                last_day_of_month = datetime(to_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day_of_month = datetime(to_date.year, to_date.month + 1, 1) - timedelta(days=1)
        except:
            if self.viewer_frame:
                for widget in self.viewer_frame.winfo_children():
                    widget.destroy()
                lbl = ctk.CTkLabel(self.viewer_frame, text=get_text("err_date_range"), text_color="red")
                lbl.pack()
                lbl.bind("<ButtonPress-1>", self._start_pan)
                lbl.bind("<B1-Motion>", self._pan)
            return
        
        for filename, val in self.data.items():
            try:
                dt = datetime.strptime(val["timestamp"], "%b %d, %Y %I:%M %p")
                
                if not (from_date <= dt <= last_day_of_month):
                    continue
                
                disease = val.get("disease", "")
                pest = val.get("pest", "")
                
                has_match = False
                if active_diseases and disease in active_diseases:
                    has_match = True
                if active_pests and pest in active_pests:
                    has_match = True
                
                if has_match:
                    filtered_data.append((filename, val))
            except:
                continue
        
        if not filtered_data:
            if self.viewer_frame:
                for widget in self.viewer_frame.winfo_children():
                    widget.destroy()
                lbl = ctk.CTkLabel(self.viewer_frame, text=get_text("lbl_no_data"), text_color="orange")
                lbl.pack(pady=20)
                lbl.bind("<ButtonPress-1>", self._start_pan)
                lbl.bind("<B1-Motion>", self._pan)
            return
        
        self.show_report_name_popup(filtered_data, month_from, month_to)

    def show_report_name_popup(self, filtered_data, month_from, month_to):
        def scale_val(value, axis='x'):
            factor = self.scale_x if axis == 'x' else self.scale_y
            return round(value * factor)

        popup_width = scale_val(350, 'x')
        popup_height = scale_val(200, 'y')
        scaled_button_width = round(popup_width * 0.8)
        scaled_label_font = ("Arial", scale_val(12, 'y'), "bold")
        scaled_button_height = scale_val(30, 'y')
        scaled_pady_10 = scale_val(10, 'y')
        scaled_pady_5 = scale_val(5, 'y')

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (popup_width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (popup_height // 2)

        popup = ctk.CTkToplevel(self.root)
        popup.title(get_text("title_report_name"))
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        popup.configure(fg_color=self._get_color(BG_COLOR))
        popup.transient(self.root)

        popup.after(50, lambda: (popup.lift(), popup.focus_force(), popup.grab_set()))

        label = ctk.CTkLabel(popup, text=get_text("lbl_enter_report_name"), text_color=self._get_color(TEXT_COLOR), font=scaled_label_font)
        label.pack(pady=scaled_pady_10)

        entry = ctk.CTkEntry(
            popup, justify="center", fg_color=self._get_color(BUTTON_COLOR), text_color=self._get_color(TEXT_COLOR),
            width=scaled_button_width, font=scaled_label_font, placeholder_text=get_text("lbl_placeholder_report_name")
        )
        entry.pack(pady=scaled_pady_5)

        def on_confirm(event=None):
            report_name = entry.get().strip()
            if not report_name:
                entry.delete(0, "end")
                entry.insert(0, get_text("lbl_report_name_empty"))
                entry.configure(text_color="#FF6B6B")
                return
            
            safe_name = re.sub(r'[<>:"/\\|?*]', '', report_name).replace(" ", "_")
            if not safe_name:
                return
            
            report_filename = f"{safe_name}.pdf"
            report_path = os.path.join("_reports_", report_filename)
            os.makedirs("_reports_", exist_ok=True)
            
            counter = 1
            base_name = safe_name
            while os.path.exists(report_path):
                report_filename = f"{base_name}_{counter}.pdf"
                report_path = os.path.join("_reports_", report_filename)
                counter += 1
            
            self.create_pdf(filtered_data, report_path, month_from, month_to)
            popup.destroy()
            self.show_view_list()
            self.render_pdf_to_viewer(report_path)

        entry.bind("<Return>", on_confirm)

        confirm_btn = ctk.CTkButton(
            popup, text=get_text("btn_gen_report"), command=on_confirm,
            fg_color=self._get_color(BUTTON_COLOR), hover_color=self._get_color(BUTTON_HOVER), 
            text_color=self._get_color(TEXT_COLOR), height=scaled_button_height,
            width=scaled_button_width, font=scaled_label_font
        )
        confirm_btn.pack(pady=scaled_pady_10)

        cancel_btn = ctk.CTkButton(
            popup, text=get_text("btn_cancel"), command=popup.destroy,
            fg_color=self._get_color(BUTTON_COLOR), hover_color=self._get_color(BUTTON_HOVER), 
            text_color=self._get_color(TEXT_COLOR), height=scaled_button_height,
            width=scaled_button_width, font=scaled_label_font
        )
        cancel_btn.pack(pady=scaled_pady_5)

        popup.after(100, entry.focus_set)
        self.root.wait_window(popup)

    def create_pdf(self, filtered_data, output_path, month_from, month_to):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 15, "AGRIVISION SYSTEM", ln=True, align="C")
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(0, 10, f"Disease and Pest Detection Report", ln=True, align="C")
        
        if month_from == month_to:
            pdf.cell(0, 10, f"Period: {month_from}", ln=True, align="C")
        else:
            pdf.cell(0, 10, f"Period: {month_from} to {month_to}", ln=True, align="C")
             
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        
        pdf.ln(5) 
        current_y = pdf.get_y() 
        pdf.line(10, current_y, 200, current_y)  
        pdf.ln(5) 

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Total Detections: {len(filtered_data)}", ln=True)
        pdf.ln(5)

        y_position = pdf.get_y() 
        for filename, item in filtered_data:
            if y_position > 220:
                pdf.add_page()
                y_position = 20

            pdf.set_xy(15, y_position)
            pdf.set_font("Helvetica", "B", 11)
            
            disease = item.get("disease", "")
            pest = item.get("pest", "")
            display_name = (disease or pest or "Unknown").replace("_", " ")
            
            if disease:
                pdf.cell(100, 8, f"Disease: {display_name}", ln=True)
            else:
                pdf.cell(100, 8, f"Pest: {display_name}", ln=True)
            
            pdf.set_font("Helvetica", "", 9)
            pdf.set_x(15)
            pdf.cell(100, 6, f"Accuracy: {item.get('accuracy', 'N/A')}", ln=True)
            pdf.set_x(15)
            pdf.cell(100, 6, f"Count: {item.get('count', '1')}", ln=True)
            pdf.set_x(15)
            pdf.cell(100, 6, f"Time: {item.get('timestamp', 'N/A')}", ln=True)
            
            img_path = os.path.join("Page_files/gallery_files", filename)
            if os.path.exists(img_path):
                pdf.image(img_path, x=130, y=y_position, w=50)
            else:
                pdf.set_xy(130, y_position)
                pdf.cell(50, 20, "[Image Missing]", border=1, align="C")

            y_position += 60  
            pdf.line(15, y_position - 5, 195, y_position - 5)  

        pdf.output(output_path)

    def render_pdf_to_viewer(self, pdf_path):
        if not self.viewer_frame: return
        self.current_viewed_report = pdf_path
        
        for widget in self.viewer_frame.winfo_children():
            widget.destroy()

        self.viewer_frame._parent_canvas.yview_moveto(0)

        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=120) 
                
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(self._scale_value(350, 'x'), self._scale_value(450, 'y')))
                lbl = ctk.CTkLabel(self.viewer_frame, image=ctk_img, text="")
                lbl.pack(pady=10)
                
                lbl.bind("<ButtonPress-1>", self._start_pan)
                lbl.bind("<B1-Motion>", self._pan)
            doc.close()
        except Exception as e:
            ctk.CTkLabel(
                self.viewer_frame, 
                text=f"{get_text('err_pdf_render')}:\n{e}", 
                text_color="red"
            ).pack()

    def go_back_to_dashboard(self):
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard
        app = MyDashboard()
        app.run()

if __name__ == "__main__":
    app = ReportPage()
    app.root.mainloop()