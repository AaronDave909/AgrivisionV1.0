from shared_components import SharedComponents as SC, custom_font_bold, custom_font_regular, LEFT_PANEL_WIDTH, LEFT_PANEL_COLOR
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
        
        # Variable to track touch/mouse drag position
        self._drag_start_y = 0 
        
        self.create_title(text="Report Generation", x=119, y=0)
        self.create_left_panel()
        self.create_leaf_image()
        self.undo_button(command=self.go_back_to_dashboard)
        
        # 2. Load the data
        self.data = self.load_json_data()
        self.months = self.get_unique_months()
        self.diseases = self.get_unique_diseases()
        self.pests = self.get_unique_pests()   

        self.setup_ui()

    # --- Touch Scrolling Logic ---
    def _start_pan(self, event):
        """Records the starting Y coordinate when the user touches/clicks."""
        self._drag_start_y = event.y_root

    def _pan(self, event):
        """Calculates the drag distance and scrolls the PDF viewer."""
        delta = self._drag_start_y - event.y_root
        if abs(delta) > 2:
            self.viewer_frame._parent_canvas.yview_scroll(int(delta / 3), "units")
            self._drag_start_y = event.y_root

    def load_json_data(self):
        try:
            gallery_path = "Page_files/gallery_files/gallery_data.json"
            if os.path.exists(gallery_path):
                with open(gallery_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading JSON: {e}")
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
            self.left_panel, text="Create", 
            width=scaled_button_width, height=scaled_button_height,
            command=self.show_create_view,
            fg_color="#50556b", hover_color="#50556b",
            corner_radius=20, text_color="white", font=btn_font
        )
        self.create_tab_btn.place(x=x_pos, y=y_create, anchor="center")
        
        self.view_tab_btn = ctk.CTkButton(
            self.left_panel, text="View", 
            width=scaled_button_width, height=scaled_button_height,
            command=self.show_view_list,
            fg_color=LEFT_PANEL_COLOR, hover_color="#50556b",
            corner_radius=20, text_color="white", font=btn_font
        )
        self.view_tab_btn.place(x=x_pos, y=y_view, anchor="center")
        
        # --- PDF VIEWER SECTION (Right Side) ---
        self.viewer_frame = ctk.CTkScrollableFrame(self.root, fg_color="#2A2E3F",
                                                   width=self._scale_value(390, 'x'), 
                                                   height=self._scale_value(400, 'y'))
        self.viewer_frame.place(x=self._scale_value(390, 'x'), y=self._scale_value(60, 'y'))
        
        self.viewer_frame._parent_canvas.bind("<ButtonPress-1>", self._start_pan)
        self.viewer_frame._parent_canvas.bind("<B1-Motion>", self._pan)
        
        self.viewer_placeholder = ctk.CTkLabel(self.viewer_frame, text="Select or generate a report to view.", text_color="gray")
        self.viewer_placeholder.pack(pady=50)
        
        self.viewer_placeholder.bind("<ButtonPress-1>", self._start_pan)
        self.viewer_placeholder.bind("<B1-Motion>", self._pan)

        # --- FILTER/CONTENT SECTION (Center-Left) ---
        self.filter_frame = ctk.CTkFrame(self.root, fg_color="transparent",
                                    width=self._scale_value(250, 'x'), 
                                    height=self._scale_value(400, 'y'))
        self.filter_frame.place(x=self._scale_value(120, 'x'), y=self._scale_value(60, 'y'))
        self.filter_frame.pack_propagate(False)

        # --- CONTAINERS FOR THE TWO MODES ---
        # FIX: The frames are now shorter (300px) so they don't cover the bottom buttons
        self.create_container = ctk.CTkScrollableFrame(self.filter_frame, fg_color="transparent", height=self._scale_value(300, 'y'))
        self.view_container = ctk.CTkScrollableFrame(self.filter_frame, fg_color="transparent", height=self._scale_value(300, 'y'))

        self.build_create_ui()
        self.create_container.place(x=0, y=0, relwidth=1.0) 

        # --- FIXED BOTTOM BUTTONS ---
        # 1. Generate Button (Shows on Create tab)
        self.gen_btn = ctk.CTkButton(
            self.filter_frame,
            text="Generate Report",
            font=tuple(custom_font_bold),
            fg_color="#2A2E3F",
            hover_color="#383C4E",
            command=self.generate_and_display_report,
            width=self._scale_value(230, 'x'),
            height=self._scale_value(40, 'y')
        )

        self.gen_btn.place(
            x=self._scale_value(10, 'x'),
            y=self._scale_value(320, 'y')
        )

        # 2. Master Delete Button (Created but hidden initially)
        self.del_btn = ctk.CTkButton(
            self.filter_frame,
            text="Delete",
            font=tuple(custom_font_bold),
            fg_color="#CC0000",
            hover_color="#FF4C4C",
            command=self.trigger_delete,
            width=self._scale_value(230, 'x'),
            height=self._scale_value(40, 'y')
        )

    def build_create_ui(self):
        """Builds the Date Range and Checkboxes inside the Create Container."""
        
        # --- Date Range Selection ---
        ctk.CTkLabel(self.create_container, text="Date Range:", font=tuple(custom_font_bold), text_color="white").pack(anchor="w", pady=(10, 5), padx=10)
        
        date_frame = ctk.CTkFrame(self.create_container, fg_color="transparent")
        date_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        # From selector
        from_label = ctk.CTkLabel(date_frame, text="From:", font=tuple(custom_font_regular), text_color="white")
        from_label.pack(side="left", padx=(0, 5))
        
        self.month_from_var = ctk.StringVar(value=self.months[0] if self.months else "")
        month_from_dropdown = ctk.CTkOptionMenu(
            date_frame, 
            values=self.months, 
            variable=self.month_from_var,
            font=("Arial", 14),
            dropdown_font=("Arial", 14),
            fg_color="#2A2E3F",
            text_color="#FFFFFF",
            button_color="#383C4E",
            button_hover_color="#50556b",
            dropdown_fg_color="#2A2E3F",
            dropdown_hover_color="#383C4E",
            dropdown_text_color="#FFFFFF"
        )
        month_from_dropdown.pack(side="left", padx=(0, 15), fill="x", expand=True)
        
        # To selector
        to_label = ctk.CTkLabel(date_frame, text="To:", font=tuple(custom_font_regular), text_color="white")
        to_label.pack(side="left", padx=(0, 5))
        
        self.month_to_var = ctk.StringVar(value=self.months[-1] if self.months else "")
        month_to_dropdown = ctk.CTkOptionMenu(
            date_frame, 
            values=self.months, 
            variable=self.month_to_var,
            font=("Arial", 14),
            dropdown_font=("Arial", 14),
            fg_color="#2A2E3F",
            text_color="#FFFFFF",
            button_color="#383C4E",
            button_hover_color="#50556b",
            dropdown_fg_color="#2A2E3F",
            dropdown_hover_color="#383C4E",
            dropdown_text_color="#FFFFFF"
        )
        month_to_dropdown.pack(side="left", fill="x", expand=True)

        # --- Disease Checklist ---
        ctk.CTkLabel(self.create_container, text="Select Diseases:", font=tuple(custom_font_bold), text_color="white").pack(anchor="w", pady=(0, 5), padx=10)
        disease_frame = ctk.CTkScrollableFrame(self.create_container, height=self._scale_value(65, 'y'), fg_color="#2A2E3F")
        disease_frame.pack(fill="x", pady=(0, 10), padx=10)

        if self.diseases:
            for disease in self.diseases:
                var = ctk.BooleanVar(value=True) 
                cb = ctk.CTkCheckBox(disease_frame, text=disease.replace("_", " "), variable=var, text_color="white")
                cb.pack(anchor="w", pady=3, padx=5)
                self.selected_diseases[disease] = var
        else:
            ctk.CTkLabel(disease_frame, text="No diseases found", text_color="gray").pack()

        # --- Pest Checklist ---
        ctk.CTkLabel(self.create_container, text="Select Pests:", font=tuple(custom_font_bold), text_color="white").pack(anchor="w", pady=(0, 5), padx=10)
        pest_frame = ctk.CTkScrollableFrame(self.create_container, height=self._scale_value(65, 'y'), fg_color="#2A2E3F")
        pest_frame.pack(fill="x", pady=(0, 15), padx=10)

        if self.pests:
            for pest in self.pests:
                var = ctk.BooleanVar(value=True) 
                cb = ctk.CTkCheckBox(pest_frame, text=pest.replace("_", " "), variable=var, text_color="white")
                cb.pack(anchor="w", pady=3, padx=5)
                self.selected_pests[pest] = var
        else:
            ctk.CTkLabel(pest_frame, text="No pests found", text_color="gray").pack()

    # --- TOGGLE LOGIC ---
    def show_create_view(self):
        self.current_view = "create"

        self.view_container.place_forget()

        if self.del_btn:
            self.del_btn.place_forget()

        self.create_container.place(x=0, y=0, relwidth=1.0)

        self.gen_btn.place(
            x=self._scale_value(10, 'x'),
            y=self._scale_value(320, 'y')
        )

        self.create_tab_btn.configure(fg_color="#50556b", hover_color="#50556b")
        self.view_tab_btn.configure(fg_color=LEFT_PANEL_COLOR, hover_color="#50556b")

    def show_view_list(self):
        self.current_view = "view"

        self.create_container.place_forget()

        if self.gen_btn:
            self.gen_btn.place_forget()

        self.view_container.place(x=0, y=0, relwidth=1.0)

        self.del_btn.place(
            x=self._scale_value(10, 'x'),
            y=self._scale_value(320, 'y')
        )

        self.view_tab_btn.configure(fg_color="#50556b", hover_color="#50556b")
        self.create_tab_btn.configure(fg_color=LEFT_PANEL_COLOR, hover_color="#50556b")

        self.refresh_reports_list()

    def refresh_reports_list(self):
        for widget in self.view_container.winfo_children():
            widget.destroy()

        reports_dir = "_reports_"
        os.makedirs(reports_dir, exist_ok=True)
        
        reports = [f for f in os.listdir(reports_dir) if f.endswith('.pdf')]
        reports.sort(reverse=True)

        if not reports:
            ctk.CTkLabel(self.view_container, text="No reports generated yet.", text_color="gray").pack(pady=20)
            return

        for report in reports:
            btn = ctk.CTkButton(
                self.view_container,
                text=report,
                anchor="w", 
                fg_color="#2A2E3F",
                hover_color="#3a3f57",
                command=lambda r=report: self.render_pdf_to_viewer(os.path.join(reports_dir, r))
            )
            btn.pack(fill="x", pady=2, padx=5)

    # --- DELETE LOGIC ---
    def trigger_delete(self):
        """Checks if a report is actively open before asking to delete."""
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
        popup.title("Delete Report")
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        popup.configure(fg_color="#202332")
        popup.transient(self.root)
        
        popup.after(50, lambda: (popup.lift(), popup.focus_force(), popup.grab_set()))

        label = ctk.CTkLabel(
            popup, 
            text=f"Delete '{report_filename}'?", 
            text_color="white", 
            font=("Arial", scale_val(12, 'y'), "bold")
        )
        label.pack(pady=scale_val(20, 'y'))

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=scale_val(20, 'x'))

        def on_delete():
            try:
                report_path = os.path.join("_reports_", report_filename)
                os.remove(report_path)
                
                if self.current_viewed_report == report_path:
                    for widget in self.viewer_frame.winfo_children():
                        widget.destroy()
                    self.viewer_placeholder = ctk.CTkLabel(self.viewer_frame, text="Select or generate a report to view.", text_color="gray")
                    self.viewer_placeholder.pack(pady=50)
                    self.current_viewed_report = None
                    
            except Exception as e:
                print(f"Error deleting report: {e}")
            
            popup.destroy()
            self.refresh_reports_list()

        del_btn = ctk.CTkButton(
            btn_frame, text="Delete", fg_color="#FF4C4C", hover_color="#CC0000", 
            width=scale_val(100, 'x'), command=on_delete
        )
        del_btn.pack(side="left", expand=True, padx=5)

        cancel_btn = ctk.CTkButton(
            btn_frame, text="Cancel", fg_color="#2A2E3F", hover_color="#383C4E", 
            width=scale_val(100, 'x'), command=popup.destroy
        )
        cancel_btn.pack(side="right", expand=True, padx=5)

    # --- PDF GENERATION LOGIC ---
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
                ctk.CTkLabel(self.viewer_frame, text="Error parsing date range", text_color="red").pack()
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
                ctk.CTkLabel(self.viewer_frame, text="No data found for selected filters", text_color="orange").pack(pady=20)
            return
        
        self.show_report_name_popup(filtered_data, month_from, month_to)

    def show_report_name_popup(self, filtered_data, month_from, month_to):
        def scale_val(value, axis='x'):
            factor = self.scale_x if axis == 'x' else self.scale_y
            return round(value * factor)

        ORIGINAL_POPUP_WIDTH = 350
        ORIGINAL_POPUP_HEIGHT = 200
        
        popup_width = scale_val(ORIGINAL_POPUP_WIDTH, 'x')
        popup_height = scale_val(ORIGINAL_POPUP_HEIGHT, 'y')

        BUTTON_WIDTH_RATIO = 0.8
        scaled_button_width = round(popup_width * BUTTON_WIDTH_RATIO)
        
        scaled_label_font_size = scale_val(12, 'y')
        scaled_label_font = ("Arial", scaled_label_font_size, "bold")
        
        scaled_button_height = scale_val(30, 'y')
        scaled_pady_10 = scale_val(10, 'y')
        scaled_pady_5 = scale_val(5, 'y')

        self.root.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        x = root_x + (root_width // 2) - (popup_width // 2)
        y = root_y + (root_height // 2) - (popup_height // 2)

        popup = ctk.CTkToplevel(self.root)
        popup.title("Name Your Report")
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        popup.configure(fg_color="#202332")
        popup.transient(self.root)

        popup.after(50, lambda: (
            popup.lift(),
            popup.focus_force(),
            popup.grab_set()
        ))

        label = ctk.CTkLabel(popup, text="Enter report name:", text_color="white", font=scaled_label_font)
        label.pack(pady=scaled_pady_10)

        entry = ctk.CTkEntry(
            popup,
            justify="center",
            fg_color="#333645",
            text_color="#FFFFFF",
            width=scaled_button_width,
            font=scaled_label_font,
            placeholder_text="e.g., Weekly Report"
        )
        entry.pack(pady=scaled_pady_5)

        def on_confirm(event=None):
            report_name = entry.get().strip()
            
            if not report_name:
                entry.delete(0, "end")
                entry.insert(0, "Name cannot be empty")
                entry.configure(text_color="#FF6B6B")
                return
            
            safe_name = re.sub(r'[<>:"/\\|?*]', '', report_name)
            safe_name = safe_name.replace(" ", "_")
            
            if not safe_name:
                entry.delete(0, "end")
                entry.insert(0, "Invalid name")
                entry.configure(text_color="#FF6B6B")
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
            print(f"✅ Report generated and saved to: {report_path}")
            
            popup.destroy()
            
            self.show_view_list()
            self.render_pdf_to_viewer(report_path)

        entry.bind("<Return>", on_confirm)

        confirm_btn = ctk.CTkButton(
            popup,
            text="Generate Report",
            command=on_confirm,
            fg_color="#2A2E3F",
            hover_color="#3a3f57",
            height=scaled_button_height,
            width=scaled_button_width,
            font=scaled_label_font
        )
        confirm_btn.pack(pady=scaled_pady_10)

        def on_cancel():
            popup.destroy()

        cancel_btn = ctk.CTkButton(
            popup,
            text="Cancel",
            command=on_cancel,
            fg_color="#2A2E3F",
            hover_color="#383C4E",
            height=scaled_button_height,
            width=scaled_button_width,
            font=scaled_label_font
        )
        cancel_btn.pack(pady=scaled_pady_5)

        popup.after(100, entry.focus_set)
        self.root.wait_window(popup)

    def create_pdf(self, filtered_data, output_path, month_from, month_to):
        pdf = FPDF()
        pdf.add_page()
        
        # HEADER
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
        
        # SPACING & DYNAMIC LINE
        pdf.ln(5) 
        current_y = pdf.get_y() 
        pdf.line(10, current_y, 200, current_y)  
        pdf.ln(5) 

        # SUMMARY
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Total Detections: {len(filtered_data)}", ln=True)
        pdf.ln(5)

        # DATA ENTRIES
        y_position = pdf.get_y() 
        for filename, item in filtered_data:
            if y_position > 220:
                pdf.add_page()
                y_position = 20

            # Text block 
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
            
            # Image block 
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
        # Save the absolute path of the currently viewed report
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
            ctk.CTkLabel(self.viewer_frame, text=f"Error rendering PDF:\n{e}", text_color="red").pack()

    def go_back_to_dashboard(self):
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard
        app = MyDashboard()
        app.run()

if __name__ == "__main__":
    app = ReportPage()
    app.root.mainloop()