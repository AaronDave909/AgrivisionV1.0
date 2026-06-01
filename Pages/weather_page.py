import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from language_manager import get_text
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH
import os
import datetime 
from PIL import Image
import json
from collections import defaultdict
import numpy as np
import matplotlib.colors as mcolors
from shared_components import (
    custom_font_bold, custom_font_title, custom_font_regular, 
    BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR, LEFT_PANEL_COLOR, BG_COLOR
)
import gc
import tkinter as tk
from tkcalendar import Calendar

# --- MODIFIED: Now returns 4 variables, including the latest date string ---
def get_latest_weather_averages(csv_path="Page_files/weather.csv"):
    try:
        if not os.path.exists(csv_path):
            return None, None, None, "No Data"
        df = pd.read_csv(csv_path)
        if df.empty or 'Date' not in df.columns or 'Time' not in df.columns:
            return None, None, None, "No Data"
            
        df['Time'] = df['Time'].astype(str)
        df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
        df = df.set_index('Timestamp')
        
        latest_time = df.index.max()
        latest_date_str = latest_time.strftime('%b %d')
        
        # Check if the latest data is actually from today
        if latest_time.date() != datetime.date.today():
            # If the data is old, return None for temp so the dashboard knows to show the date
            return None, None, None, latest_date_str

        ten_mins_ago = latest_time - pd.Timedelta(minutes=10)
        recent_df = df[df.index >= ten_mins_ago]
        
        if recent_df.empty:
            if not df.empty:
                last_temp = df['Temperature'].iloc[-1]
                return (last_temp if not pd.isna(last_temp) else None, None, None, latest_date_str)
            return None, None, None, latest_date_str

        avg_temp = recent_df['Temperature'].mean()
        avg_hum = recent_df['Humidity'].mean()
        avg_pres = recent_df['Pressure'].mean()
        
        return (
            avg_temp if not pd.isna(avg_temp) else None,
            avg_hum if not pd.isna(avg_hum) else None,
            avg_pres if not pd.isna(avg_pres) else None,
            latest_date_str
        )
    except Exception as e:
        print(f"--- {get_text('log_err_weather_csv')}: {e}")
        return None, None, None, "Error"

class WeatherPage(SC):
    CSV_FILE_PATH = "Page_files/weather.csv"
    GALLERY_JSON_PATH = "Page_files/gallery_files/gallery_data.json"
    UPDATE_INTERVAL = 10000 

    def on_month_selected(self, selected_item: str):
        self.selected_filter = selected_item
        self._update_plot_data(force_update=True)

    def on_sub_type_selected(self, choice):
        self._update_plot_data(force_update=True)

    def open_calendar(self):
        import datetime
        import pandas as pd
        import os

        if hasattr(self, 'cal_window') and self.cal_window.winfo_exists():
            self.cal_window.lift()
            return
            
        self.cal_window = ctk.CTkToplevel(self.root)
        self.cal_window.title(get_text("title_select_date"))
        self.cal_window.attributes("-topmost", True)
        self.cal_window.resizable(False, False)
        
        self.cal_window.transient(self.root)
        self.cal_window.after(50, lambda: (
            self.cal_window.lift(),
            self.cal_window.focus_force(),
            self.cal_window.grab_set()
        ))
        
        w, h = 450, 480 
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.cal_window.geometry(f"{w}x{h}+{x}+{y}")
        
        self.cal_window.configure(fg_color=self._get_color(BG_COLOR))
        
        bg_color = self._get_color(BG_COLOR)
        fg_color = self._get_color(TEXT_COLOR)
        sel_color = self._get_color(BUTTON_HOVER)
        header_bg = self._get_color(BUTTON_COLOR)
        
        no_data_color = "#FF6B6B"
        
        self.cal = Calendar(
            self.cal_window, 
            font="Arial 16",
            selectmode='day',
            year=datetime.date.today().year,
            month=datetime.date.today().month,
            day=datetime.date.today().day,
            date_pattern='yyyy-mm-dd',
            showweeknumbers=False, 
            
            background=header_bg,
            foreground=fg_color,
            bordercolor=header_bg,
            headersbackground=header_bg,
            headersforeground=fg_color,
            
            selectbackground=sel_color,
            selectforeground=fg_color,
            
            normalbackground=bg_color,
            normalforeground=no_data_color,
            
            weekendbackground=bg_color,
            weekendforeground=no_data_color,
            
            othermonthforeground="#555555",
            othermonthbackground=bg_color,
            othermonthweforeground="#555555",
            othermonthwebackground=bg_color,
        )
        self.cal.pack(pady=15, padx=15, fill="both", expand=True)
        
        self.cal.tag_config("has_data", foreground=fg_color, background=bg_color)
        
        try:
            csv_path = getattr(self, 'CSV_FILE_PATH', "Page_files/weather.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                if not df.empty and 'Date' in df.columns:
                    for d_str in df['Date'].dropna().unique():
                        try:
                            valid_date = datetime.datetime.strptime(str(d_str), '%Y-%m-%d').date()
                            self.cal.calevent_create(valid_date, "Data Available", "has_data")
                        except ValueError:
                            pass
        except Exception as e:
            print(f"--- {get_text('log_err_calendar_dates')}: {e}")

        select_btn = ctk.CTkButton(
            self.cal_window, 
            text=get_text("btn_confirm_date"),
            command=self.confirm_date,
            font=("Arial", 20, "bold"),
            height=50,  
            fg_color=self._get_color(BUTTON_COLOR),
            hover_color=self._get_color(BUTTON_HOVER),
            text_color=self._get_color(TEXT_COLOR)
        )
        select_btn.pack(pady=(0, 15))

    def confirm_date(self):
        picked_date = self.cal.selection_get().strftime('%Y-%m-%d')
        
        if picked_date == datetime.date.today().strftime('%Y-%m-%d'):
            self.selected_filter = "Today"
        else:
            self.selected_filter = picked_date
        
        # Update the Date Filter Button text
        date_text = get_text("lbl_filter_date").replace("{date}", str(self.selected_filter))
        self.weather_date_btn.configure(text=date_text)
        self._update_plot_data(force_update=True)
        self.cal_window.destroy()

    def _update_season_indicator(self):
        try:
            today = datetime.date.today()
            current_month = today.month 
            season = ""
            sub_text = ""
            color = self._get_color(TEXT_COLOR) 

            if current_month in [11, 12, 1, 2]:
                season = get_text("lbl_dry_cool")
                sub_text = get_text("sub_dry_cool")
                color = self._get_color(("#0077B6", "#A9DFFF"))
            elif current_month in [3, 4, 5]:
                season = get_text("lbl_dry_hot")
                sub_text = get_text("sub_dry_hot")
                color = self._get_color(("#D95D00", "#FFD1A9"))
            elif current_month in [6, 7, 8, 9, 10]:
                season = get_text("lbl_wet_season")
                sub_text = get_text("sub_wet_season")
                color = self._get_color(("#5C6B73", "#C8D3D5"))

            self.season_label.configure(text=season, text_color=color)
            self.season_sub_label.configure(text=sub_text, text_color=color)
            
        except Exception as e:
            # Localized terminal log
            print(f"--- {get_text('log_err_season')}: {e}")
            self.season_label.configure(text=get_text("lbl_season_error"), text_color="red")
            self.season_sub_label.configure(text="")
    
    def _get_available_json_months(self):
        all_months = set()
        final_options = ["All Detections"]

        try:
            if not os.path.exists(self.GALLERY_JSON_PATH):
                return final_options 
            with open(self.GALLERY_JSON_PATH, 'r') as f:
                data = json.load(f)

            for item_data in data.values():
                timestamp_str = item_data.get("timestamp")
                if not timestamp_str: continue
                try:
                    item_date = datetime.datetime.strptime(timestamp_str, '%b %d, %Y %I:%M %p')
                    all_months.add((item_date.year, item_date.month))
                except ValueError:
                    continue
            
            if not all_months: return final_options 
            sorted_months = sorted(list(all_months), reverse=True)
            formatted_months = [datetime.date(year, month, 1).strftime('%B %Y') for year, month in sorted_months]
            final_options.extend(formatted_months)
            return final_options
        except Exception as e:
            print(f"Error scanning JSON for months: {e}")
            return final_options 
    
    def _load_and_process_json_data(self, selected_filter_str: str):
        disease_counts = defaultdict(int)
        deficiency_counts = defaultdict(int)
        pest_counts = defaultdict(int)
        
        filter_by_month = True
        if selected_filter_str == "All Detections":
            filter_by_month = False
        else:
            try:
                target_date = datetime.datetime.strptime(selected_filter_str, '%B %Y')
                target_month = target_date.month
                target_year = target_date.year
            except ValueError:
                return disease_counts, deficiency_counts, pest_counts 
            
        try:
            if not os.path.exists(self.GALLERY_JSON_PATH): return disease_counts, deficiency_counts, pest_counts
            with open(self.GALLERY_JSON_PATH, 'r') as f:
                data = json.load(f)

            for item_data in data.values():
                timestamp_str = item_data.get("timestamp")
                if not timestamp_str: continue
                try:
                    item_date = datetime.datetime.strptime(timestamp_str, '%b %d, %Y %I:%M %p')
                except ValueError:
                    continue

                process_this_item = False
                if not filter_by_month:
                    process_this_item = True
                else:
                    if item_date.month == target_month and item_date.year == target_year:
                        process_this_item = True

                if process_this_item:
                    count = int(item_data.get("count", 0))
                    raw_name = item_data.get("disease", "") or item_data.get("pest_name", "") or item_data.get("pest", "")
                    if not raw_name or raw_name.lower() == "healthy" or raw_name == "No Disease Detected":
                        continue
                        
                    individual_names = [self._format_name(n.strip()) for n in raw_name.split(',')]
                    is_pest_entry = "pest" in item_data or "pest_name" in item_data
                    
                    for name in individual_names:
                        if is_pest_entry:
                            if "droplet" not in name.lower() and count > 0:
                                pest_counts[name] += count
                        else:
                            if count > 0:
                                if "Deficiency" in name:
                                    deficiency_counts[name] += count
                                else:
                                    disease_counts[name] += count
            return disease_counts, deficiency_counts, pest_counts
        except Exception as e:
            print(f"Error processing JSON: {e}")
            return disease_counts, deficiency_counts, pest_counts

    def _format_name(self, name_str):
        if not name_str: return ""
        name_str = name_str.replace("_", " ").title()
        replacements = {
            "N Deficiency": "Nitrogen Deficiency",
            "P Deficiency": "Phosphorus Deficiency",
            "K Deficiency": "Potassium Deficiency",
            "Ca Deficiency": "Calcium Deficiency",
            "Mg Deficiency": "Magnesium Deficiency",
            "Downy Mildew On Lettuce": "Downy Mildew",
            "Powdery Mildew On Lettuce": "Powdery Mildew",
            "Bacterial": "Bacterial Leaf Spot"
        }
        for old, new in replacements.items():
            name_str = name_str.replace(old, new)
        return name_str.strip()

    def on_dropdown_open(self, event=None):
        self.root.after(50, self.lift_dropdown_menu)

    def lift_dropdown_menu(self):
        try:
            if hasattr(self.disease_month_menu, '_dropdown_menu') and self.disease_month_menu._dropdown_menu:
                self.disease_month_menu._dropdown_menu.lift()
            if hasattr(self.sub_type_selector, '_dropdown_menu') and self.sub_type_selector._dropdown_menu:
                self.sub_type_selector._dropdown_menu.lift()
        except Exception as e:
            pass

    def _get_most_recent_csv_date(self):
        try:
            if not os.path.exists(self.CSV_FILE_PATH):
                return "Today"
            df = pd.read_csv(self.CSV_FILE_PATH)
            if df.empty or 'Date' not in df.columns:
                return "Today"
            
            latest_date_str = df['Date'].iloc[-1]
            
            if str(latest_date_str) == datetime.date.today().strftime('%Y-%m-%d'):
                return "Today"
                
            return str(latest_date_str)
        except Exception as e:
            print(f"Error finding most recent date: {e}")
            return "Today"

    def __init__(self):
        super().__init__()
        
        self.is_running = True
        self.current_view = "all" 
        
        self.selected_filter = self._get_most_recent_csv_date()
        self.after_id = None
        
        self.create_left_panel() 
        self.create_leaf_image() 
        self.create_title(text=get_text("title_analytics"), x=119, y=0)
        self.create_battery_indicator(x=15, y=100)

        self.date_filter_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.date_filter_frame.place(relx=0.98, y=self._scale_value(25, 'y'), anchor="ne")
        
        self.selector_row_frame = ctk.CTkFrame(self.date_filter_frame, fg_color="transparent")
        self.selector_row_frame.pack(side="top", anchor="e", pady=(0, 5)) 

        self.filter_label = ctk.CTkLabel(
            self.selector_row_frame, 
            text=get_text("title_select_date"),
            font=("Arial", self._scale_value(14, 'y')),
            text_color=self._get_color(TEXT_COLOR)
        )
        self.filter_label.pack(side="left", padx=(5, 5))

        menu_bg = self._get_color(BUTTON_COLOR)
        menu_text = self._get_color(TEXT_COLOR)
        menu_hover = self._get_color(BUTTON_HOVER)

        # Determine the initial text safely
        display_date = self.selected_filter if self.selected_filter else "--"
        initial_btn_text = get_text("lbl_filter_date").replace("{date}", str(display_date))

        self.weather_date_btn = ctk.CTkButton(
            self.selector_row_frame,
            text=initial_btn_text, # Use the pre-calculated string
            command=self.open_calendar,
            font=("Arial", self._scale_value(14, 'y')),
            fg_color=menu_bg,
            text_color=menu_text,
            hover_color=menu_hover,
            width=self._scale_value(140, 'x')
        )
        self.weather_date_btn.pack(side="left", padx=(0, 10))

        self.disease_month_menu = ctk.CTkOptionMenu(
            self.selector_row_frame,
            values=["All Detections"], 
            command=self.on_month_selected,
            font=("Arial", self._scale_value(14, 'y')),
            dropdown_font=("Arial", self._scale_value(20, 'y')),
            fg_color=menu_bg,
            text_color=menu_text,
            button_color=menu_hover,
            button_hover_color=self._get_color(("#C1C3C8", "#50556b")), 
            dropdown_fg_color=menu_bg,          
            dropdown_hover_color=menu_hover,    
            dropdown_text_color=menu_text 
        )
        if hasattr(self.disease_month_menu, '_button'):
            self.disease_month_menu._button.bind("<Button-1>", self.on_dropdown_open, add="+")

        self.sub_selector_row_frame = ctk.CTkFrame(self.date_filter_frame, fg_color="transparent")
        
        self.sub_type_label = ctk.CTkLabel(
            self.sub_selector_row_frame, 
            text=get_text("lbl_sub_type"),
            font=("Arial", self._scale_value(14, 'y')),
            text_color=self._get_color(TEXT_COLOR)
        )
        self.sub_type_label.pack(side="left", padx=(5, 5))

        self.sub_type_var = ctk.StringVar(value="Diseases")
        self.sub_type_selector = ctk.CTkOptionMenu(
            self.sub_selector_row_frame,
            values=["Diseases", "Deficiencies"],
            variable=self.sub_type_var,
            command=self.on_sub_type_selected,
            font=("Arial", self._scale_value(14, 'y')),
            dropdown_font=("Arial", self._scale_value(20, 'y')),
            fg_color=menu_bg, text_color=menu_text, button_color=menu_hover,
            button_hover_color=self._get_color(("#C1C3C8", "#50556b")), 
            dropdown_fg_color=menu_bg, dropdown_hover_color=menu_hover, dropdown_text_color=menu_text 
        )
        self.sub_type_selector.pack(side="left", padx=(0, 10))
        if hasattr(self.sub_type_selector, '_button'):
            self.sub_type_selector._button.bind("<Button-1>", self.on_dropdown_open, add="+")

        self.season_label = ctk.CTkLabel(self.date_filter_frame, text="", font=("Arial", 12, "bold"), text_color=self._get_color(TEXT_COLOR))
        self.season_label.pack(side="top", anchor="e", padx=(0, 10)) 
        self.season_sub_label = ctk.CTkLabel(self.date_filter_frame, text="", font=("Arial", 12), text_color=self._get_color(TEXT_COLOR))
        self.season_sub_label.pack(side="top", anchor="e", padx=(0, 10))

        scaled_button_width = self._scale_value(100, 'x')
        scaled_button_height = self._scale_value(40, 'y')
        scaled_img_size = (self._scale_value(30, 'x'), self._scale_value(30, 'y'))
        scaled_padding = self._scale_value(10, 'y')
        
        try:
            def load_dual_icon(image_path):
                img_white = Image.open(image_path).convert("RGBA")
                img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])
                return ctk.CTkImage(light_image=img_dark, dark_image=img_white, size=scaled_img_size)

            self.all_icon = load_dual_icon("_image_assets/all_data.png")
            self.temp_icon = load_dual_icon("_image_assets/temperature.png")
            self.hum_icon = load_dual_icon("_image_assets/humidity.png")
            self.pres_icon = load_dual_icon("_image_assets/pressure.png")
            self.disease_icon = load_dual_icon("_image_assets/disease_icon.png") 
            self.pest_icon = load_dual_icon("_image_assets/pest_icon.png")
            self.undo_icon = load_dual_icon("_image_assets/Undo.png")
        except Exception as e:
            print(f"Error loading button icons: {e}")
            self.all_icon = self.temp_icon = self.hum_icon = self.pres_icon = self.disease_icon = self.pest_icon = self.undo_icon = None
        
        y_all = self._scale_value(150, 'y')
        y_temp = y_all + scaled_button_height + scaled_padding
        y_hum = y_temp + scaled_button_height + scaled_padding
        y_pres = y_hum + scaled_button_height + scaled_padding
        y_disease = y_pres + scaled_button_height + scaled_padding
        y_pest = y_disease + scaled_button_height + scaled_padding
        y_undo = y_pest + scaled_button_height + scaled_padding
        
        x_pos = self._scale_value(LEFT_PANEL_WIDTH / 2, 'x')
        btn_font = ("Arial", 12) 
        btn_anchor = "w"
        btn_fg = self._get_color(LEFT_PANEL_COLOR)
        btn_hover = self._get_color(BUTTON_HOVER)
        btn_text = self._get_color(TEXT_COLOR)

        self.all_button = ctk.CTkButton(self.left_panel, text=get_text("btn_all_data"), width=scaled_button_width, height=scaled_button_height, image=self.all_icon, command=lambda: self.show_view("all"), fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.all_button.place(x=x_pos, y=y_all, anchor="center")
        self.temp_button = ctk.CTkButton(self.left_panel, text=get_text("btn_temp"), width=scaled_button_width, height=scaled_button_height, image=self.temp_icon, command=lambda: self.show_view("temp"), fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.temp_button.place(x=x_pos, y=y_temp, anchor="center")
        self.hum_button = ctk.CTkButton(self.left_panel, text=get_text("btn_hum"), width=scaled_button_width, height=scaled_button_height, image=self.hum_icon, command=lambda: self.show_view("hum"), fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.hum_button.place(x=x_pos, y=y_hum, anchor="center")
        self.pres_button = ctk.CTkButton(self.left_panel, text=get_text("btn_pres"), width=scaled_button_width, height=scaled_button_height, image=self.pres_icon, command=lambda: self.show_view("pres"), fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.pres_button.place(x=x_pos, y=y_pres, anchor="center")
        self.disease_button = ctk.CTkButton(self.left_panel, text=get_text("btn_disease"), width=scaled_button_width, height=scaled_button_height, image=self.disease_icon, command=lambda: self.show_view("disease"), fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.disease_button.place(x=x_pos, y=y_disease, anchor="center")
        self.pest_button = ctk.CTkButton(self.left_panel, text=get_text("btn_pest"), width=scaled_button_width, height=scaled_button_height, image=self.pest_icon, command=lambda: self.show_view("pest"), fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.pest_button.place(x=x_pos, y=y_pest, anchor="center")
        self.undo_button = ctk.CTkButton(self.left_panel, text=get_text("btn_undo"), width=scaled_button_width, height=scaled_button_height, image=self.undo_icon, command=self.navigate_to_dashboard, fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.undo_button.place(x=x_pos, y=y_undo, anchor="center")

        self.chart_buttons = [self.all_button, self.temp_button, self.hum_button, self.pres_button, self.disease_button, self.pest_button]

        chart_frame_x = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        chart_frame_y = self._scale_value(60, 'y') 
        
        self.chart_frame = ctk.CTkFrame(self.root, fg_color=self._get_color(BG_COLOR))
        self.chart_frame.place(
            x=chart_frame_x, y=chart_frame_y,
            relwidth=1.0 - (chart_frame_x / self.root.winfo_width()),
            relheight=1.0 - (chart_frame_y / self.root.winfo_height())
        )

        self.status_label = ctk.CTkLabel(self.chart_frame, text="Initializing plot...", font=("Arial", 18), text_color=self._get_color(TEXT_COLOR))
        self.status_label.pack(expand=True)

        self.fig_stacked, self.ax1, self.ax2, self.ax3 = None, None, None, None
        self.canvas_stacked = None
        self.fig_single, self.ax_single = None, None
        self.canvas_single = None
        
        self.avg_frame = None
        self.temp_avg_label = None
        self.hum_avg_label = None
        self.pres_avg_label = None
        self.high_tide_label = None
        self.low_tide_label = None
        self.disease_total_label = None
        self.pest_total_label = None
        
        self._update_season_indicator()
        self.date_filter_frame.lift()
        self.root.after(100, self.setup_plot)

    def setup_plot(self):
        try:
            bg_hex = self._get_color(BG_COLOR)
            text_hex = self._get_color(TEXT_COLOR)
            
            self.fig_stacked, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
            self.fig_stacked.patch.set_facecolor(bg_hex)
            self.fig_stacked.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.15)
            
            self.fig_single, self.ax_single = plt.subplots(1, 1, figsize=(12, 8))
            self.fig_single.patch.set_facecolor(bg_hex)
            self.fig_single.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.15)
            
            self.status_label.pack_forget()
            
            self.avg_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
            self.avg_frame.pack(side=ctk.TOP, fill="x", padx=20, pady=(5, 10))

            font_style = ("Arial", 20, "bold")
            self.temp_avg_label = ctk.CTkLabel(self.avg_frame, text=get_text("lbl_temp_avg"), font=font_style, text_color=text_hex)
            self.hum_avg_label = ctk.CTkLabel(self.avg_frame, text=get_text("lbl_hum_avg"), font=font_style, text_color=text_hex)
            self.pres_avg_label = ctk.CTkLabel(self.avg_frame, text=get_text("lbl_pres_avg"), font=font_style, text_color=text_hex)
            self.high_tide_label = ctk.CTkLabel(self.avg_frame, text=get_text("lbl_high_tide"), font=font_style, text_color=BG_COLOR)
            self.low_tide_label = ctk.CTkLabel(self.avg_frame, text=get_text("lbl_low_tide"), font=font_style, text_color=BG_COLOR)
            self.disease_total_label = ctk.CTkLabel(self.avg_frame, text=get_text("lbl_disease_total"), font=font_style, text_color=text_hex)
            self.pest_total_label = ctk.CTkLabel(self.avg_frame, text=get_text("lbl_pest_total"), font=font_style, text_color=text_hex)

            self.canvas_stacked = FigureCanvasTkAgg(self.fig_stacked, master=self.chart_frame)
            self.canvas_stacked.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

            self.canvas_single = FigureCanvasTkAgg(self.fig_single, master=self.chart_frame)
            self.canvas_single.get_tk_widget().pack_forget()
            
            self.show_view(self.current_view) 
            self._update_plot_data()

            self.date_filter_frame.lift()

        except Exception as e:
            print(f"An error occurred during plot setup: {e}")
            self.status_label.configure(text=f"An error occurred during setup:\n{e}", text_color="red")
            self.status_label.pack(expand=True)

    def show_view(self, view_name):
        if not self.canvas_stacked or not self.canvas_single or not self.temp_avg_label:
            return

        default_color = self._get_color(LEFT_PANEL_COLOR)   
        selected_color = self._get_color(BG_COLOR)  
        
        for button in self.chart_buttons:
            button.configure(fg_color=default_color)
            
        if view_name == "all": self.all_button.configure(fg_color=selected_color)
        elif view_name == "temp": self.temp_button.configure(fg_color=selected_color)
        elif view_name == "hum": self.hum_button.configure(fg_color=selected_color)
        elif view_name == "pres": self.pres_button.configure(fg_color=selected_color)
        elif view_name == "disease": self.disease_button.configure(fg_color=selected_color)
        elif view_name == "pest": self.pest_button.configure(fg_color=selected_color)

        self.current_view = view_name
        
        if self.current_view == "all":
            self.canvas_single.get_tk_widget().pack_forget()
            self.canvas_stacked.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        else:
            self.canvas_stacked.get_tk_widget().pack_forget()
            self.canvas_single.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
            
        self.temp_avg_label.pack_forget()
        self.hum_avg_label.pack_forget()
        self.pres_avg_label.pack_forget()
        self.high_tide_label.pack_forget()
        self.low_tide_label.pack_forget()
        self.disease_total_label.pack_forget()
        self.pest_total_label.pack_forget()
        
        if self.current_view == "all":
            self.high_tide_label.pack(side=ctk.LEFT, padx=10)
            self.low_tide_label.pack(side=ctk.LEFT, padx=10)
        elif self.current_view == "temp":
            self.temp_avg_label.pack(side=ctk.LEFT, padx=10)
        elif self.current_view == "hum":
            self.hum_avg_label.pack(side=ctk.LEFT, padx=10)
        elif self.current_view == "pres":
            self.pres_avg_label.pack(side=ctk.LEFT, padx=10)
        elif self.current_view == "disease":
            self.disease_total_label.pack(side=ctk.LEFT, padx=10)
        elif self.current_view == "pest":
            self.pest_total_label.pack(side=ctk.LEFT, padx=10)
            
        if self.current_view in ["disease", "pest"]:
            self.season_label.pack_forget()
            self.season_sub_label.pack_forget()
            self.weather_date_btn.pack_forget()
            
            self.filter_label.configure(text=get_text("lbl_select_month"))
            self.disease_month_menu.pack(side="left", padx=(0, 10))
            
            available_months = self._get_available_json_months()
            self.disease_month_menu.configure(values=available_months)
            
            new_selection = available_months[0] if available_months else "All Detections"
            self.disease_month_menu.set(new_selection)
            self.selected_filter = new_selection

            if self.current_view == "disease":
                self.sub_selector_row_frame.pack(side="top", anchor="e", pady=(0, 5), after=self.selector_row_frame)
            else:
                self.sub_selector_row_frame.pack_forget()
            
            if self.is_running:
                self.is_running = False
                if self.after_id:
                    self.root.after_cancel(self.after_id)
                    self.after_id = None
        else: 
            self.sub_selector_row_frame.pack_forget()
            self.disease_month_menu.pack_forget()
            
            self.season_label.pack(side="top", anchor="e", padx=(0, 10))
            self.season_sub_label.pack(side="top", anchor="e", padx=(0, 10))
            
            self.filter_label.configure(text=get_text("title_select_date"))
            self.weather_date_btn.pack(side="left", padx=(0, 10))
            
            # Reset the filter to the most recent date in the CSV
            is_gallery_filter = "Detection" in str(self.selected_filter) or any(month in str(self.selected_filter) for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
            
            if is_gallery_filter:
                self.selected_filter = self._get_most_recent_csv_date()
            
            # Update the button text to reflect the reset date
            display_date = str(self.selected_filter) if self.selected_filter else "--"
            new_text = get_text("lbl_filter_date").replace("{date}", display_date)
            self.weather_date_btn.configure(text=new_text)
            
            if not self.is_running:
                self.is_running = True
                self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)

        if self.canvas_stacked: 
            self.root.after(10, self._update_plot_data, True) 

        self.date_filter_frame.lift()

    def _set_dynamic_ylim(self, ax, data_series):
        if data_series.empty:
            ax.set_ylim(0, 1)
            return
        min_val = data_series.min()
        max_val = data_series.max()
        data_range = max_val - min_val
        padding = data_range * 0.1
        if padding < 0.5: padding = 0.5
        ax.set_ylim(min_val - padding, max_val + padding)

    def _apply_gradient(self, ax, x_data, y_data, color_hex):
        try:
            fill = ax.fill_between(x_data, y_data, color='none', zorder=2)
            clip_path = fill.get_paths()[0]
            x_data_num = mdates.date2num(x_data)
            xmin, xmax = x_data_num[0], x_data_num[-1]
            ymin, ymax = ax.get_ylim()

            line_color_rgb = mcolors.to_rgb(color_hex)
            colors = [(*line_color_rgb, 0.4), (*line_color_rgb, 0.0)]
            cmap = mcolors.LinearSegmentedColormap.from_list('my_gradient', colors, N=256)
            
            gradient = np.linspace(1, 0, 256).reshape(-1, 1)
            gradient_img = np.repeat(gradient, 2, axis=1)
            
            img = ax.imshow(gradient_img, cmap=cmap, aspect='auto', origin='lower', 
                            extent=[xmin, xmax, ymin, ymax], zorder=1)
            img.set_clip_path(clip_path, transform=ax.transData)
        except Exception as e:
            pass

    def _update_plot_data(self, force_update=False):
        should_auto_update = (self.selected_filter == "Today")
        
        if not force_update and not should_auto_update:
            return 
            
        try:
            ax_bg = self._get_color(BUTTON_COLOR)
            text_hex = self._get_color(TEXT_COLOR)
            
            if self.ax1: self.ax1.clear()
            if self.ax2: self.ax2.clear()
            if self.ax3: self.ax3.clear()
            if self.ax_single: self.ax_single.clear()

            if self.current_view in ["all", "temp", "hum", "pres"]:
                if not os.path.exists(self.CSV_FILE_PATH):
                    # Localized UI Error Message
                    error_msg = get_text("err_file_not_found").replace("{path}", self.CSV_FILE_PATH)

                    self.status_label.configure(
                        text=error_msg, 
                        text_color="red"
                    )
                    if not self.canvas_stacked: self.status_label.pack(expand=True)
                    if not force_update and should_auto_update: self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)
                    return
                
                self.status_label.pack_forget()
                df_full = pd.read_csv(self.CSV_FILE_PATH)
                
                if df_full.empty or 'Date' not in df_full.columns or 'Time' not in df_full.columns:
                     if self.canvas_stacked: self.canvas_stacked.draw()
                     if self.canvas_single: self.canvas_single.draw()
                     if self.is_running and not force_update and should_auto_update: 
                         self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)
                     return
                
                df_full['Time'] = df_full['Time'].astype(str)
                df_full['Timestamp'] = pd.to_datetime(df_full['Date'] + ' ' + df_full['Time'])
                df = df_full.set_index('Timestamp')
                
                try:
                    if self.selected_filter == "Today":
                        target_date = datetime.date.today()
                        avg_label_prefix = get_text("lbl_feels_like")
                    else:
                        target_date = datetime.datetime.strptime(self.selected_filter, '%Y-%m-%d').date()
                        avg_label_prefix = get_text("lbl_day_avg")
                    
                    filtered_df = df[df.index.date == target_date]
                except Exception as e:
                    target_date = datetime.date.today()
                    filtered_df = df[df.index.date == target_date]
                    avg_label_prefix = get_text("lbl_feels_like")
                
                is_empty_data = filtered_df.empty
                display_color = "red" if is_empty_data else text_hex

                try:
                    avg_temp, avg_hum, avg_pres = np.nan, np.nan, np.nan
                    if not is_empty_data:
                        # Decide which subset of data to average
                        if self.selected_filter == "Today":
                            latest_time = filtered_df.index.max()
                            ten_mins_ago = latest_time - pd.Timedelta(minutes=10)
                            # Filter for the last 10 minutes of recorded data
                            target_for_avg = filtered_df[filtered_df.index >= ten_mins_ago]
                            
                            # Fallback: if no data in last 10 mins, use the whole day's data
                            if target_for_avg.empty:
                                target_for_avg = filtered_df
                        else:
                            # For past dates, always average the entire day
                            target_for_avg = filtered_df

                        # Calculate means, ensuring we handle non-numeric data safely
                        avg_temp = pd.to_numeric(target_for_avg['Temperature'], errors='coerce').mean()
                        avg_hum = pd.to_numeric(target_for_avg['Humidity'], errors='coerce').mean()
                        avg_pres = pd.to_numeric(target_for_avg['Pressure'], errors='coerce').mean()

                    # 1. Temperature Logic
                    t_val = f"{avg_temp:.1f}" if not pd.isna(avg_temp) else get_text("lbl_avg_na")
                    self.temp_avg_label.configure(
                        text=get_text("lbl_avg_temp").replace("{val}", t_val),
                        text_color=display_color
                    )

                    # 2. Humidity Logic
                    h_val = f"{avg_hum:.1f}" if not pd.isna(avg_hum) else get_text("lbl_avg_na")
                    self.hum_avg_label.configure(
                        text=get_text("lbl_avg_hum").replace("{val}", h_val),
                        text_color=display_color
                    )

                    # 3. Pressure Logic
                    p_val = f"{avg_pres:.1f}" if not pd.isna(avg_pres) else get_text("lbl_avg_na")
                    self.pres_avg_label.configure(
                        text=get_text("lbl_avg_pres").replace("{val}", p_val),
                        text_color=display_color
                    )

                except Exception as e:
                    err_txt = get_text("lbl_avg_error")
                    self.temp_avg_label.configure(text=f"Temp: {err_txt}", text_color="red")
                    self.hum_avg_label.configure(text=f"Hum: {err_txt}", text_color="red")
                    print(f"--- {get_text('log_err_averages')}: {e}")
                
                if not filtered_df.empty:
                    self.ax1.plot(filtered_df.index, filtered_df['Temperature'], color='#E74C3C', zorder=3, linewidth=2.5)
                    self._set_dynamic_ylim(self.ax1, filtered_df['Temperature'])
                    self._apply_gradient(self.ax1, filtered_df.index, filtered_df['Temperature'], '#E74C3C')

                    self.ax2.plot(filtered_df.index, filtered_df['Humidity'], color='#3498DB', zorder=3, linewidth=2.5)
                    self._set_dynamic_ylim(self.ax2, filtered_df['Humidity'])
                    self._apply_gradient(self.ax2, filtered_df.index, filtered_df['Humidity'], '#3498DB')
                    
                    self.ax3.plot(filtered_df.index, filtered_df['Pressure'], color='#2ECC71', zorder=3, linewidth=2.5)
                    self._set_dynamic_ylim(self.ax3, filtered_df['Pressure'])
                    self._apply_gradient(self.ax3, filtered_df.index, filtered_df['Pressure'], '#2ECC71')
                
                self.ax1.set_ylabel('Temperature (°C)', color=text_hex, labelpad=15); self.ax1.grid(True, linestyle='--', alpha=0.3, color='gray'); self.ax1.tick_params(axis='y', colors=text_hex); self.ax1.tick_params(axis='x', colors=text_hex); self.ax1.set_facecolor(ax_bg)
                self.ax2.set_ylabel('Humidity (%)', color=text_hex, labelpad=15); self.ax2.grid(True, linestyle='--', alpha=0.3, color='gray'); self.ax2.tick_params(axis='y', colors=text_hex); self.ax2.tick_params(axis='x', colors=text_hex); self.ax2.set_facecolor(ax_bg)
                self.ax3.set_ylabel('Pressure (hPa)', color=text_hex, labelpad=15); self.ax3.grid(True, linestyle='--', alpha=0.3, color='gray'); self.ax3.tick_params(axis='y', colors=text_hex); self.ax3.tick_params(axis='x', colors=text_hex); self.ax3.set_facecolor(ax_bg)
                
                for ax in [self.ax1, self.ax2, self.ax3]:
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['bottom'].set_color(text_hex)
                    ax.spines['left'].set_color(text_hex)

                self.ax3.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p')); self.ax3.set_xlabel('Time', color=text_hex); plt.setp(self.ax3.get_xticklabels(), rotation=0, ha="center", color=text_hex)
                self.fig_stacked.suptitle(f"BME280 Sensor Data ({self.selected_filter})", fontsize=14, color=text_hex)
                
                title = get_text("title_sensor_data")
                if not filtered_df.empty:
                    if self.current_view == "temp":
                        title = f"Temperature ({self.selected_filter})"; self.ax_single.set_ylabel('Temperature (°C)', color=text_hex, labelpad=15)
                        self.ax_single.plot(filtered_df.index, filtered_df['Temperature'], color='#E74C3C', zorder=3, linewidth=2.5)
                        self._set_dynamic_ylim(self.ax_single, filtered_df['Temperature']); self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Temperature'], '#E74C3C')
                    elif self.current_view == "hum":
                        title = f"Humidity ({self.selected_filter})"; self.ax_single.set_ylabel('Humidity (%)', color=text_hex, labelpad=15)
                        self.ax_single.plot(filtered_df.index, filtered_df['Humidity'], color='#3498DB', zorder=3, linewidth=2.5)
                        self._set_dynamic_ylim(self.ax_single, filtered_df['Humidity']); self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Humidity'], '#3498DB')
                    elif self.current_view == "pres":
                        title = f"Pressure ({self.selected_filter})"; self.ax_single.set_ylabel('Pressure (hPa)', color=text_hex, labelpad=15)
                        self.ax_single.plot(filtered_df.index, filtered_df['Pressure'], color='#2ECC71', zorder=3, linewidth=2.5)
                        self._set_dynamic_ylim(self.ax_single, filtered_df['Pressure']); self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Pressure'], '#2ECC71')
                
                self.ax_single.grid(True, linestyle='--', alpha=0.3, color='gray'); self.ax_single.tick_params(axis='y', colors=text_hex); self.ax_single.tick_params(axis='x', colors=text_hex); self.ax_single.set_facecolor(ax_bg)
                self.ax_single.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p')); self.ax_single.set_xlabel('Time', color=text_hex); plt.setp(self.ax_single.get_xticklabels(), rotation=0, ha="center", color=text_hex)
                
                self.ax_single.spines['top'].set_visible(False)
                self.ax_single.spines['right'].set_visible(False)
                self.ax_single.spines['bottom'].set_color(text_hex)
                self.ax_single.spines['left'].set_color(text_hex)
                self.ax_single.set_title("") 
                self.fig_single.suptitle(title, fontsize=14, color=text_hex)

            else:
                self.status_label.pack_forget()
                disease_counts, deficiency_counts, pest_counts = self._load_and_process_json_data(self.selected_filter)
                
                data_to_plot = {}
                title = ""
                color = "gray"
                
                if self.current_view == "disease":
                    sub_type = self.sub_type_var.get()
                    if sub_type == "Deficiencies":
                        data_to_plot = deficiency_counts
                        # Dynamic Title and Label for Deficiencies
                        title = get_text("lbl_title_deficiency").replace("{filter}", str(self.selected_filter))
                        color = '#F1C40F' 
                        total = sum(deficiency_counts.values())
                        
                        total_text = get_text("lbl_total_deficiency").replace("{val}", str(total))
                        self.disease_total_label.configure(text=total_text)
                    else:
                        data_to_plot = disease_counts
                        # Dynamic Title and Label for Diseases
                        title = get_text("lbl_title_disease").replace("{filter}", str(self.selected_filter))
                        color = '#9B59B6'
                        total = sum(disease_counts.values())
                        
                        total_text = get_text("lbl_total_disease").replace("{val}", str(total))
                        self.disease_total_label.configure(text=total_text)
                
                elif self.current_view == "pest":
                    data_to_plot = pest_counts
                    # Dynamic Title and Label for Pests
                    title = get_text("lbl_title_pest").replace("{filter}", str(self.selected_filter))
                    color = '#F39C12'
                    total = sum(pest_counts.values())
                    
                    total_text = get_text("lbl_total_pest").replace("{val}", str(total))
                    self.pest_total_label.configure(text=total_text)

                if data_to_plot:
                    is_deficiency_view = (self.current_view == "disease" and self.sub_type_var.get() == "Deficiencies")
                    
                    if is_deficiency_view:
                        labels = [label.replace(" ", "\n") for label in data_to_plot.keys()]
                        bar_width = 0.4
                    else:
                        labels = list(data_to_plot.keys())
                        bar_width = 0.8

                    counts = list(data_to_plot.values())
                    max_count = max(counts) if counts else 0
                    
                    if max_count > 0:
                        self.ax_single.set_ylim(bottom=0, top=max_count * 1.15)
                    else:
                        self.ax_single.set_ylim(bottom=0, top=1)
                    
                    self.ax_single.bar(labels, counts, color=color, width=bar_width)
                    
                    for i, count in enumerate(counts):
                        self.ax_single.text(i, count + (max_count * 0.01), str(count), 
                                            ha='center', va='bottom', color=text_hex, fontsize=12)

                elif self.selected_filter == "All Detections" and not data_to_plot:
                    self.ax_single.text(0.5, 0.5, get_text("lbl_no_detections"), ha='center', va='center', color='red', fontsize=18, transform=self.ax_single.transAxes)
                    self.ax_single.set_ylim(bottom=0, top=1) 
                
                elif self.selected_filter != "All Detections" and not data_to_plot: 
                     self.ax_single.text(0.5, 0.5, get_text("lbl_no_detections_month"), ha='center', va='center', color='red', fontsize=18, transform=self.ax_single.transAxes)
                     self.ax_single.set_ylim(bottom=0, top=1) 

                self.ax_single.set_ylabel(get_text("lbl_total_count"), color=text_hex, labelpad=15)
                self.ax_single.set_title("") 
                self.fig_single.suptitle(title, fontsize=14, color=text_hex) 

                self.ax_single.grid(True, linestyle='--', alpha=0.3, axis='y', color='gray')
                self.ax_single.tick_params(axis='y', colors=text_hex)
                self.ax_single.tick_params(axis='x', colors=text_hex)
                self.ax_single.set_facecolor(ax_bg)

                self.ax_single.spines['top'].set_visible(False)
                self.ax_single.spines['right'].set_visible(False)
                self.ax_single.spines['bottom'].set_color(text_hex)
                self.ax_single.spines['left'].set_color(text_hex)
                
                plt.setp(self.ax_single.get_xticklabels(), rotation=0, ha="center", color=text_hex, fontsize=10)

            if self.canvas_stacked: self.canvas_stacked.draw()
            if self.canvas_single: self.canvas_single.draw()
            
            self.date_filter_frame.lift()
            
        except Exception as e:
            print(f"--- {get_text('log_err_plot_update')}: {e}")
        
        if self.is_running and not force_update and should_auto_update: 
            self.after_id = self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)

    def navigate_to_dashboard(self):
        self.is_running = False
        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
            
        # --- FIX: Kill Matplotlib figures to free X11 memory for the dashboard! ---
        if hasattr(self, 'fig_stacked') and self.fig_stacked:
            plt.close(self.fig_stacked)
        if hasattr(self, 'fig_single') and self.fig_single:
            plt.close(self.fig_single)
        gc.collect()

        self.root.after(150, super().go_back_to_dashboard)

if __name__ == "__main__":
    app = WeatherPage()
    app.root.mainloop()
