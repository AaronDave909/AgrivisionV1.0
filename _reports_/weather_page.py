import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH
import os
import datetime 
from PIL import Image

# --- ADDED IMPORTS ---
import json
from collections import defaultdict
import numpy as np
import matplotlib.colors as mcolors
from shared_components import (
    custom_font_bold, custom_font_title, custom_font_regular, 
    BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR, LEFT_PANEL_COLOR, BG_COLOR
)
# ---------------------

def get_latest_weather_averages(csv_path="Page_files/weather.csv"):
    """
    Reads the weather CSV and calculates the 10-minute average 
    for Temp, Humidity, and Pressure.
    Returns: (avg_temp, avg_hum, avg_pres)
    """
    try:
        if not os.path.exists(csv_path):
            print(f"Weather CSV not found at: {csv_path}")
            return None, None, None

        df = pd.read_csv(csv_path)
        if df.empty:
            print("Weather CSV is empty.")
            return None, None, None
        
        if 'Date' not in df.columns or 'Time' not in df.columns:
            print("CSV is missing 'Date' or 'Time' columns.")
            return None, None, None
            
        df['Time'] = df['Time'].astype(str)
        df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
        df = df.set_index('Timestamp')
        
        latest_time = df.index.max()
        ten_mins_ago = latest_time - pd.Timedelta(minutes=10)
        recent_df = df[df.index >= ten_mins_ago]
        
        if recent_df.empty:
            print("No recent weather data in the last 10 minutes.")
            if not df.empty:
                last_temp = df['Temperature'].iloc[-1]
                return (last_temp if not pd.isna(last_temp) else None, None, None)
            return None, None, None

        avg_temp = recent_df['Temperature'].mean()
        avg_hum = recent_df['Humidity'].mean()
        avg_pres = recent_df['Pressure'].mean()
        
        return (
            avg_temp if not pd.isna(avg_temp) else None,
            avg_hum if not pd.isna(avg_hum) else None,
            avg_pres if not pd.isna(avg_pres) else None
        )

    except Exception as e:
        print(f"Error reading or processing weather CSV: {e}")
        return None, None, None

class WeatherPage(SC):
    
    CSV_FILE_PATH = "Page_files/weather.csv"
    GALLERY_JSON_PATH = "Page_files/gallery_files/gallery_data.json"
    UPDATE_INTERVAL = 10000 

    def on_filter_selected(self, selected_item: str):
        """
        Called when an item is selected from the filter dropdown.
        This item can be a date (e.g., "Today") or a month (e.g., "November 2025").
        """
        self.selected_filter = selected_item
        
        self._update_plot_data(force_update=True)

    def _update_weather_date_selector(self, df_full: pd.DataFrame):
        """Updates the filter dropdown with available DATES for weather."""
        
        if self.filter_selector is None or self.current_view not in ["all", "temp", "hum", "pres"]:
            return
        
        self.filter_selector.configure(state="normal") 

        try:
            if df_full.empty or 'Date' not in df_full.columns:
                self.filter_selector.configure(values=["Today"])
                self.filter_selector.set("Today")
                return

            df_full['Date_Only'] = pd.to_datetime(df_full['Date']).dt.date
            today = datetime.date.today()
            unique_dates = sorted(df_full['Date_Only'].unique(), reverse=True)
            
            dropdown_options = []
            
            if today in unique_dates:
                dropdown_options.append("Today")
                past_dates = [d.strftime('%Y-%m-%d') for d in unique_dates if d != today]
                dropdown_options.extend(past_dates)
            else:
                dropdown_options = [d.strftime('%Y-%m-%d') for d in unique_dates]

            current_selection = self.selected_filter
            self.filter_selector.configure(values=dropdown_options)
            
            if current_selection in dropdown_options:
                self.filter_selector.set(current_selection)
            elif dropdown_options:
                self.filter_selector.set(dropdown_options[0])
                self.selected_filter = dropdown_options[0]
            else:
                self.filter_selector.configure(values=["Today"])
                self.filter_selector.set("Today")
                self.selected_filter = "Today"

        except Exception as e:
            print(f"Error updating date selector: {e}")
            self.filter_selector.configure(values=["Today"])
            self.filter_selector.set("Today")
            
    def _update_season_indicator(self):
        """
        Checks today's date and updates the season labels
        based on Philippine climate patterns.
        """
        try:
            today = datetime.date.today()
            current_month = today.month 

            season = ""
            sub_text = ""
            color = self._get_color(TEXT_COLOR) 

            if current_month in [11, 12, 1, 2]: # November - February
                season = "Dry Season (Cool)"
                sub_text = "Expect rainy and hot sunny days!"
                color = self._get_color(("#0077B6", "#A9DFFF")) # Dark Blue / Light Blue
            elif current_month in [3, 4, 5]: # March - May
                season = "Dry Season (Hot)"
                sub_text = "Expect extreme hot temperatures!"
                color = self._get_color(("#D95D00", "#FFD1A9")) # Dark Orange / Light Orange
            elif current_month in [6, 7, 8, 9, 10]: # June - October
                season = "Wet Season"
                sub_text = "Expect frequent or heavy rains!"
                color = self._get_color(("#5C6B73", "#C8D3D5")) # Dark Gray / Light Gray-Blue

            self.season_label.configure(text=season, text_color=color)
            self.season_sub_label.configure(text=sub_text, text_color=color)
        
        except Exception as e:
            print(f"Error updating season indicator: {e}")
            self.season_label.configure(text="Season: Error", text_color="red")
            self.season_sub_label.configure(text="")
    
    def _get_available_json_months(self):
        """
        Scans the entire gallery_data.json to find all unique months
        that have data.
        Returns: A list of strings, e.g., ["All Detections", "November 2025", ...]
        """
        all_months = set()
        
        final_options = ["All Detections"]

        try:
            if not os.path.exists(self.GALLERY_JSON_PATH):
                print(f"Warning: {self.GALLERY_JSON_PATH} not found. Only 'All Detections' will be available.")
                return final_options 

            with open(self.GALLERY_JSON_PATH, 'r') as f:
                data = json.load(f)

            for item_data in data.values():
                timestamp_str = item_data.get("timestamp")
                if not timestamp_str:
                    continue
                
                try:
                    item_date = datetime.datetime.strptime(timestamp_str, '%b %d, %Y %I:%M %p')
                    all_months.add((item_date.year, item_date.month))
                except ValueError:
                    continue
            
            if not all_months:
                return final_options 

            sorted_months = sorted(list(all_months), reverse=True)
            
            formatted_months = [
                datetime.date(year, month, 1).strftime('%B %Y') 
                for year, month in sorted_months
            ]
            
            final_options.extend(formatted_months)
            return final_options

        except Exception as e:
            print(f"Error scanning JSON for months: {e}")
            return final_options 
    
    def _load_and_process_json_data(self, selected_filter_str: str):
        """
        Loads gallery_data.json and counts diseases/pests for the
        *specified filter* (either "All Detections" or a specific month).
        """
        disease_counts = defaultdict(int)
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
                print(f"Error: Could not parse month string '{selected_filter_str}'")
                return disease_counts, pest_counts 
            
        try:
            if not os.path.exists(self.GALLERY_JSON_PATH):
                print(f"Error: {self.GALLERY_JSON_PATH} not found.")
                return disease_counts, pest_counts

            with open(self.GALLERY_JSON_PATH, 'r') as f:
                data = json.load(f)

            for item_data in data.values():
                timestamp_str = item_data.get("timestamp")
                if not timestamp_str:
                    continue
                
                try:
                    item_date = datetime.datetime.strptime(timestamp_str, '%b %d, %Y %I:%M %p')
                except ValueError:
                    print(f"Could not parse timestamp: {timestamp_str}")
                    continue

                process_this_item = False
                
                if not filter_by_month:
                    process_this_item = True
                else:
                    if item_date.month == target_month and item_date.year == target_year:
                        process_this_item = True

                if process_this_item:
                    count = int(item_data.get("count", 0))
                    
                    if "disease" in item_data:
                        disease_name = item_data["disease"]
                        if disease_name != "No Disease Detected" and count > 0:
                            formatted_name = self._format_name(disease_name)
                            disease_counts[formatted_name] += count
                            
                    elif "pest" in item_data:
                        pest_name = item_data["pest"]
                        if count > 0 and "droplet" not in pest_name.lower():
                            formatted_name = self._format_name(pest_name)
                            pest_counts[formatted_name] += count
            
            return disease_counts, pest_counts

        except Exception as e:
            print(f"Error processing {self.GALLERY_JSON_PATH}: {e}")
            return disease_counts, pest_counts

    def _format_name(self, name_str):
        """Converts snake_case names into formatted Title Case."""
        if name_str == "Downy_mildew_on_lettuce":
            return "Downy Mildew"
        if name_str == "Powdery_mildew_on_lettuce":
            return "Powdery Mildew"
        
        # General rule for all others (pests and diseases)
        return name_str.replace("_", " ").title()

    # --- NEW: Function to lift the dropdown menu ---
    def on_dropdown_open(self, event=None):
        """
        Called when the filter dropdown button is clicked.
        Waits 50ms for the menu to be created, then lifts it
        to the top of the stacking order.
        """
        self.root.after(50, self.lift_dropdown_menu)

    # --- NEW: Helper function to lift the menu ---
    def lift_dropdown_menu(self):
        try:
            if self.filter_selector._dropdown_menu:
                self.filter_selector._dropdown_menu.lift()
        except AttributeError:
            pass
        except Exception as e:
            print(f"Error lifting dropdown: {e}")

    def __init__(self):
        super().__init__()
        
        self.is_running = True
        self.current_view = "all" 
        
        self.selected_filter = "Today" 
        self.filter_selector = None      
        self.filter_label = None         
        self.after_id = None
        
        # --- Standard Page Setup ---
        self.create_left_panel() 
        self.create_leaf_image() 
        self.create_title(text="Farm Analytics", x=119, y=0)
        self.create_battery_indicator(x=15, y=100)

        # --- Filter Frame (Top-Right) ---
        self.date_filter_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.date_filter_frame.place(
            relx=0.98, 
            y=self._scale_value(25, 'y'), 
            anchor="ne" 
        )
        
        selector_row_frame = ctk.CTkFrame(self.date_filter_frame, fg_color="transparent")
        selector_row_frame.pack(side="top", anchor="e", pady=(0, 5)) 

        self.filter_label = ctk.CTkLabel(
            selector_row_frame, 
            text="Select Date:",
            font=("Arial", self._scale_value(14, 'y')),
            text_color=self._get_color(TEXT_COLOR)
        )
        self.filter_label.pack(side="left", padx=(5, 5))

        menu_bg = self._get_color(BUTTON_COLOR)
        menu_text = self._get_color(TEXT_COLOR)
        menu_hover = self._get_color(BUTTON_HOVER)

        self.filter_selector = ctk.CTkOptionMenu(
            selector_row_frame,
            values=["Today"], 
            command=self.on_filter_selected,
            font=("Arial", self._scale_value(14, 'y')),
            dropdown_font=("Arial", self._scale_value(20, 'y')),
            fg_color=self._get_color(BUTTON_COLOR),
            text_color=self._get_color(TEXT_COLOR),
            button_color=self._get_color(BUTTON_HOVER),
            button_hover_color=self._get_color(("#C1C3C8", "#50556b")), 
            
            dropdown_fg_color=menu_bg,          
            dropdown_hover_color=menu_hover,    
            dropdown_text_color=menu_text 
        )
        self.filter_selector.set("Today")
        self.filter_selector.pack(side="left", padx=(0, 10))

        if hasattr(self.filter_selector, '_button'):
            self.filter_selector._button.bind("<Button-1>", self.on_dropdown_open, add="+")

        # --- Season Indicator Labels ---
        self.season_label = ctk.CTkLabel(
            self.date_filter_frame, 
            text="", 
            font=("Arial", 12, "bold"), 
            text_color=self._get_color(TEXT_COLOR) 
        )
        self.season_label.pack(side="top", anchor="e", padx=(0, 10)) 

        self.season_sub_label = ctk.CTkLabel(
            self.date_filter_frame, 
            text="", 
            font=("Arial", 12), 
            text_color=self._get_color(TEXT_COLOR) 
        )
        self.season_sub_label.pack(side="top", anchor="e", padx=(0, 10))

        # --- Button Setup ---
        
        scaled_button_width = self._scale_value(100, 'x')
        scaled_button_height = self._scale_value(40, 'y')
        scaled_img_size = (self._scale_value(30, 'x'), self._scale_value(30, 'y'))
        scaled_padding = self._scale_value(10, 'y')
        
        try:
            # FIX: Properly set up recolored dual-mode icons
            def load_dual_icon(image_path):
                img_white = Image.open(image_path).convert("RGBA")
                img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])
                return ctk.CTkImage(
                    light_image=img_dark, 
                    dark_image=img_white, 
                    size=scaled_img_size
                )

            self.all_icon = load_dual_icon("_image_assets/all_data.png")
            self.temp_icon = load_dual_icon("_image_assets/temperature.png")
            self.hum_icon = load_dual_icon("_image_assets/humidity.png")
            self.pres_icon = load_dual_icon("_image_assets/pressure.png")
            self.disease_icon = load_dual_icon("_image_assets/disease_icon.png") 
            self.pest_icon = load_dual_icon("_image_assets/pest_icon.png")
            self.undo_icon = load_dual_icon("_image_assets/Undo.png")
       
        except Exception as e:
            print(f"Error loading button icons: {e}. Please check _image_assets folder.")
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

        self.all_button = ctk.CTkButton(self.left_panel, text=" All Data", width=scaled_button_width, height=scaled_button_height, image=self.all_icon, command=lambda: self.show_view("all"), 
                                        fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, 
                                        text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.all_button.place(x=x_pos, y=y_all, anchor="center")

        self.temp_button = ctk.CTkButton(self.left_panel, text=" Temperature", 
                                         width=scaled_button_width, height=scaled_button_height, 
                                         image=self.temp_icon, command=lambda: self.show_view("temp"), 
                                         fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, 
                                         text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.temp_button.place(x=x_pos, y=y_temp, anchor="center")

        self.hum_button = ctk.CTkButton(self.left_panel, text=" Humidity", 
                                        width=scaled_button_width, height=scaled_button_height, 
                                        image=self.hum_icon, command=lambda: self.show_view("hum"), 
                                        fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, 
                                        text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.hum_button.place(x=x_pos, y=y_hum, anchor="center")
        
        self.pres_button = ctk.CTkButton(self.left_panel, text=" Pressure", 
                                         width=scaled_button_width, height=scaled_button_height, 
                                         image=self.pres_icon, command=lambda: self.show_view("pres"), 
                                         fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, 
                                         text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.pres_button.place(x=x_pos, y=y_pres, anchor="center")

        self.disease_button = ctk.CTkButton(self.left_panel, text=" Diseases", 
                                         width=scaled_button_width, height=scaled_button_height, 
                                         image=self.disease_icon, command=lambda: self.show_view("disease"), 
                                         fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, 
                                         text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.disease_button.place(x=x_pos, y=y_disease, anchor="center")
        
        self.pest_button = ctk.CTkButton(self.left_panel, text=" Pests", 
                                         width=scaled_button_width, height=scaled_button_height, 
                                         image=self.pest_icon, command=lambda: self.show_view("pest"), 
                                         fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, 
                                         text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.pest_button.place(x=x_pos, y=y_pest, anchor="center")
        
        self.undo_button = ctk.CTkButton(self.left_panel, text=" Return", 
                                         width=scaled_button_width, height=scaled_button_height, 
                                         image=self.undo_icon, command=self.navigate_to_dashboard, 
                                         fg_color=btn_fg, hover_color=btn_hover, corner_radius=5, 
                                         text_color=btn_text, font=btn_font, anchor=btn_anchor)
        self.undo_button.place(x=x_pos, y=y_undo, anchor="center")

        self.chart_buttons = [
            self.all_button, self.temp_button, self.hum_button, self.pres_button,
            self.disease_button, self.pest_button
        ]

        # --- Chart Frame ---
        chart_frame_x = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        chart_frame_y = self._scale_value(60, 'y') 
        
        self.chart_frame = ctk.CTkFrame(self.root, fg_color=self._get_color(BG_COLOR))
        self.chart_frame.place(
            x=chart_frame_x, 
            y=chart_frame_y,
            relwidth=1.0 - (chart_frame_x / self.root.winfo_width()),
            relheight=1.0 - (chart_frame_y / self.root.winfo_height())
        )

        self.status_label = ctk.CTkLabel(self.chart_frame, text="Initializing plot...",
                                          font=("Arial", 18), text_color=self._get_color(TEXT_COLOR))
        self.status_label.pack(expand=True)

        # --- Matplotlib Objects ---
        self.fig_stacked = None
        self.ax1, self.ax2, self.ax3 = None, None, None
        self.canvas_stacked = None
        
        self.fig_single = None
        self.ax_single = None
        self.canvas_single = None
        
        # --- Average Label Objects ---
        self.avg_frame = None
        self.temp_avg_label = None
        self.hum_avg_label = None
        self.pres_avg_label = None
        self.high_tide_label = None
        self.low_tide_label = None
        self.disease_total_label = None
        self.pest_total_label = None
        
        self._update_season_indicator()
        self.date_filter_frame.lift() # Initial lift
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
            
            self.temp_avg_label = ctk.CTkLabel(self.avg_frame, text="Temperature Avg: -- °C", font=font_style, text_color=text_hex)
            self.hum_avg_label = ctk.CTkLabel(self.avg_frame, text="Humidity Avg: -- %", font=font_style, text_color=text_hex)
            self.pres_avg_label = ctk.CTkLabel(self.avg_frame, text="Pressure Avg: -- hPa", font=font_style, text_color=text_hex)
            self.high_tide_label = ctk.CTkLabel(self.avg_frame, text="High Tide: N/A", font=font_style, text_color=text_hex)
            self.low_tide_label = ctk.CTkLabel(self.avg_frame, text="Low Tide: N/A", font=font_style, text_color=text_hex)
            self.disease_total_label = ctk.CTkLabel(self.avg_frame, text="Total Detections: --", font=font_style, text_color=text_hex)
            self.pest_total_label = ctk.CTkLabel(self.avg_frame, text="Total Detections: --", font=font_style, text_color=text_hex)

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
        # --- 0. SAFETY LOCK (GHOST FIX) ---
        if not self.canvas_stacked or not self.canvas_single or not self.temp_avg_label:
            print("⏳ Plots are still loading, ignoring click...")
            return

        default_color = self._get_color(LEFT_PANEL_COLOR)   
        selected_color = self._get_color(BG_COLOR)  
        
        # 1. Reset all chart buttons
        for button in self.chart_buttons:
            button.configure(fg_color=default_color)
            
        # 2. Set the clicked button
        if view_name == "all":
            self.all_button.configure(fg_color=selected_color)
        elif view_name == "temp":
            self.temp_button.configure(fg_color=selected_color)
        elif view_name == "hum":
            self.hum_button.configure(fg_color=selected_color)
        elif view_name == "pres":
            self.pres_button.configure(fg_color=selected_color)
        elif view_name == "disease":
            self.disease_button.configure(fg_color=selected_color)
        elif view_name == "pest":
            self.pest_button.configure(fg_color=selected_color)

        self.current_view = view_name
        
        # 3. Manage Chart Canvas Visibility
        if self.current_view == "all":
            self.canvas_single.get_tk_widget().pack_forget()
            self.canvas_stacked.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        else:
            self.canvas_stacked.get_tk_widget().pack_forget()
            self.canvas_single.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
            
        # 4. Manage Average/Total/Season Label Visibility
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
            
        # 5. Manage Filter Dropdown and Season Labels
        if self.current_view in ["disease", "pest"]:
            self.season_label.pack_forget()
            self.season_sub_label.pack_forget()
            
            self.filter_label.configure(text="Select Month:")
            available_months = self._get_available_json_months()
            self.filter_selector.configure(values=available_months, state="normal")
            
            new_selection = available_months[0] 
            self.filter_selector.set(new_selection)
            self.selected_filter = new_selection
            
            if self.is_running:
                print("Stopping live updates for Disease/Pest view.")
                self.is_running = False
                if self.after_id:
                    self.root.after_cancel(self.after_id)
                    self.after_id = None
        else: 
            self.season_label.pack(side="top", anchor="e", padx=(0, 10))
            self.season_sub_label.pack(side="top", anchor="e", padx=(0, 10))

            self.filter_label.configure(text="Select Date:")
            self.filter_selector.configure(state="normal") 
            self.selected_filter = "Today"
            self.filter_selector.set("Today") 
            
            if not self.is_running:
                print("Restarting live updates for Weather view.")
                self.is_running = True
                self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)

        # 6. Force an immediate update
        if self.canvas_stacked: 
            self.root.after(10, self._update_plot_data, True) 

        # --- Lift the frame after view switch ---
        self.date_filter_frame.lift()

    def _set_dynamic_ylim(self, ax, data_series):
        """Calculates and sets dynamic Y-limits with padding."""
        if data_series.empty:
            ax.set_ylim(0, 1)
            return
        
        min_val = data_series.min()
        max_val = data_series.max()
        
        data_range = max_val - min_val
        padding = data_range * 0.1
        
        if padding < 0.5:
            padding = 0.5
            
        ax.set_ylim(min_val - padding, max_val + padding)

    def _apply_gradient(self, ax, x_data, y_data, color_hex):
        """Applies a vertical gradient fill underneath a line plot."""
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
            print(f"Failed to create gradient: {e}")

    def _update_plot_data(self, force_update=False):
        if not force_update and not self.is_running:
            if self.current_view not in ["disease", "pest"]: 
                return 
            
        try:
            ax_bg = self._get_color(BUTTON_COLOR)
            text_hex = self._get_color(TEXT_COLOR)
            
            if self.ax1: self.ax1.clear()
            if self.ax2: self.ax2.clear()
            if self.ax3: self.ax3.clear()
            if self.ax_single: self.ax_single.clear()

            # --- A) PLOT WEATHER DATA (Line Charts) ---
            if self.current_view in ["all", "temp", "hum", "pres"]:
                
                if not os.path.exists(self.CSV_FILE_PATH):
                    self.status_label.configure(text=f"Error: File not found.\n{self.CSV_FILE_PATH}", text_color="red")
                    if not self.canvas_stacked: self.status_label.pack(expand=True)
                    if not force_update: self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)
                    return
                
                self.status_label.pack_forget()
                df_full = pd.read_csv(self.CSV_FILE_PATH)
                
                self._update_weather_date_selector(df_full.copy())
                
                if df_full.empty or 'Date' not in df_full.columns or 'Time' not in df_full.columns:
                     if self.canvas_stacked: self.canvas_stacked.draw()
                     if self.canvas_single: self.canvas_single.draw()
                     if self.is_running and not force_update: 
                         self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)
                     return
                
                df_full['Time'] = df_full['Time'].astype(str)
                df_full['Timestamp'] = pd.to_datetime(df_full['Date'] + ' ' + df_full['Time'])
                df = df_full.set_index('Timestamp')
                
                try:
                    if self.selected_filter == "Today":
                        target_date = datetime.date.today()
                        avg_label_prefix = "Feels like: "
                    else:
                        target_date = datetime.datetime.strptime(self.selected_filter, '%Y-%m-%d').date()
                        avg_label_prefix = "Day Avg: "
                    filtered_df = df[df.index.date == target_date]
                except Exception as e:
                    print(f"Error filtering date: {e}. Defaulting to today.")
                    target_date = datetime.date.today()
                    filtered_df = df[df.index.date == target_date]
                    avg_label_prefix = "Feels like: "
                
                try:
                    avg_temp, avg_hum, avg_pres = np.nan, np.nan, np.nan
                    if not filtered_df.empty:
                        if self.selected_filter == "Today":
                            latest_time = filtered_df.index.max()
                            ten_mins_ago = latest_time - pd.Timedelta(minutes=10)
                            recent_df = filtered_df[filtered_df.index >= ten_mins_ago]
                            if not recent_df.empty:
                                avg_temp = recent_df['Temperature'].mean()
                                avg_hum = recent_df['Humidity'].mean()
                                avg_pres = recent_df['Pressure'].mean()
                        else:
                            avg_temp = filtered_df['Temperature'].mean()
                            avg_hum = filtered_df['Humidity'].mean()
                            avg_pres = filtered_df['Pressure'].mean()

                    self.temp_avg_label.configure(text=f"{avg_label_prefix}{avg_temp:.1f} °C" if not pd.isna(avg_temp) else "Temperature Avg: N/A")
                    self.hum_avg_label.configure(text=f"Humidity Avg: {avg_hum:.1f} %" if not pd.isna(avg_hum) else "Humidity Avg: N/A")
                
                except Exception as e:
                    print(f"Error calculating averages: {e}")
                    self.temp_avg_label.configure(text="Temperature Avg: Error")
                    self.hum_avg_label.configure(text="Humidity Avg: Error")
                
                if not filtered_df.empty:
                    self.ax1.plot(filtered_df.index, filtered_df['Temperature'], color='#E74C3C', zorder=3)
                    self._set_dynamic_ylim(self.ax1, filtered_df['Temperature'])
                    self._apply_gradient(self.ax1, filtered_df.index, filtered_df['Temperature'], '#E74C3C')

                    self.ax2.plot(filtered_df.index, filtered_df['Humidity'], color='#3498DB', zorder=3)
                    self._set_dynamic_ylim(self.ax2, filtered_df['Humidity'])
                    self._apply_gradient(self.ax2, filtered_df.index, filtered_df['Humidity'], '#3498DB')
                    
                    self.ax3.plot(filtered_df.index, filtered_df['Pressure'], color='#2ECC71', zorder=3)
                    self._set_dynamic_ylim(self.ax3, filtered_df['Pressure'])
                    self._apply_gradient(self.ax3, filtered_df.index, filtered_df['Pressure'], '#2ECC71')
                
                # --- Update Axis Colors to text_hex instead of 'white' ---
                self.ax1.set_ylabel('Temperature (°C)', color=text_hex, labelpad=15); self.ax1.grid(True, linestyle='--', alpha=0.3, color='gray'); self.ax1.tick_params(axis='y', colors=text_hex); self.ax1.tick_params(axis='x', colors=text_hex); self.ax1.set_facecolor(ax_bg)
                self.ax2.set_ylabel('Humidity (%)', color=text_hex, labelpad=15); self.ax2.grid(True, linestyle='--', alpha=0.3, color='gray'); self.ax2.tick_params(axis='y', colors=text_hex); self.ax2.tick_params(axis='x', colors=text_hex); self.ax2.set_facecolor(ax_bg)
                self.ax3.set_ylabel('Pressure (hPa)', color=text_hex, labelpad=15); self.ax3.grid(True, linestyle='--', alpha=0.3, color='gray'); self.ax3.tick_params(axis='y', colors=text_hex); self.ax3.tick_params(axis='x', colors=text_hex); self.ax3.set_facecolor(ax_bg)
                
                # Hide top/right spines, color bottom/left spines dynamically
                for ax in [self.ax1, self.ax2, self.ax3]:
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['bottom'].set_color(text_hex)
                    ax.spines['left'].set_color(text_hex)

                self.ax3.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p')); self.ax3.set_xlabel('Time', color=text_hex); plt.setp(self.ax3.get_xticklabels(), rotation=0, ha="center", color=text_hex)
                self.fig_stacked.suptitle(f"BME280 Sensor Data ({self.selected_filter})", fontsize=14, color=text_hex)
                
                title = 'Sensor Data'
                if not filtered_df.empty:
                    if self.current_view == "temp":
                        title = f"Temperature ({self.selected_filter})"; self.ax_single.set_ylabel('Temperature (°C)', color=text_hex, labelpad=15)
                        self.ax_single.plot(filtered_df.index, filtered_df['Temperature'], color='#E74C3C', zorder=3)
                        self._set_dynamic_ylim(self.ax_single, filtered_df['Temperature']); self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Temperature'], '#E74C3C')
                    elif self.current_view == "hum":
                        title = f"Humidity ({self.selected_filter})"; self.ax_single.set_ylabel('Humidity (%)', color=text_hex, labelpad=15)
                        self.ax_single.plot(filtered_df.index, filtered_df['Humidity'], color='#3498DB', zorder=3)
                        self._set_dynamic_ylim(self.ax_single, filtered_df['Humidity']); self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Humidity'], '#3498DB')
                    elif self.current_view == "pres":
                        title = f"Pressure ({self.selected_filter})"; self.ax_single.set_ylabel('Pressure (hPa)', color=text_hex, labelpad=15)
                        self.ax_single.plot(filtered_df.index, filtered_df['Pressure'], color='#2ECC71', zorder=3)
                        self._set_dynamic_ylim(self.ax_single, filtered_df['Pressure']); self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Pressure'], '#2ECC71')
                
                self.ax_single.grid(True, linestyle='--', alpha=0.3, color='gray'); self.ax_single.tick_params(axis='y', colors=text_hex); self.ax_single.tick_params(axis='x', colors=text_hex); self.ax_single.set_facecolor(ax_bg)
                self.ax_single.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p')); self.ax_single.set_xlabel('Time', color=text_hex); plt.setp(self.ax_single.get_xticklabels(), rotation=0, ha="center", color=text_hex)
                
                # Single chart spine fix
                self.ax_single.spines['top'].set_visible(False)
                self.ax_single.spines['right'].set_visible(False)
                self.ax_single.spines['bottom'].set_color(text_hex)
                self.ax_single.spines['left'].set_color(text_hex)

                self.ax_single.set_title("") 
                self.fig_single.suptitle(title, fontsize=14, color=text_hex)

            # --- B) PLOT DISEASE/PEST DATA (Bar Charts) ---
            else:
                self.status_label.pack_forget()
                self._update_weather_date_selector(pd.DataFrame()) 
                
                disease_counts, pest_counts = self._load_and_process_json_data(self.selected_filter)
                
                data_to_plot = {}
                title = ""
                color = "gray"
                
                if self.current_view == "disease":
                    data_to_plot = disease_counts
                    title = f"Disease Detections ({self.selected_filter})"
                    color = '#9B59B6'
                    total = sum(disease_counts.values())
                    self.disease_total_label.configure(text=f"Total Detections: {total}")
                
                elif self.current_view == "pest":
                    data_to_plot = pest_counts
                    title = f"Pest Detections ({self.selected_filter})"
                    color = '#F39C12'
                    total = sum(pest_counts.values())
                    self.pest_total_label.configure(text=f"Total Detections: {total}")

                if data_to_plot:
                    labels = list(data_to_plot.keys())
                    counts = list(data_to_plot.values())

                    max_count = max(counts) if counts else 0
                    if max_count > 0:
                        self.ax_single.set_ylim(bottom=0, top=max_count * 1.15)
                    else:
                        self.ax_single.set_ylim(bottom=0, top=1)
                    
                    self.ax_single.bar(labels, counts, color=color)
                    
                    for i, count in enumerate(counts):
                        self.ax_single.text(i, count + (max_count * 0.01), str(count), 
                                            ha='center', va='bottom',
                                            color=text_hex, fontsize=12)

                elif self.selected_filter == "All Detections" and not data_to_plot:
                    self.ax_single.text(0.5, 0.5, "No Detections Recorded Yet", ha='center', va='center', color=text_hex, fontsize=16, transform=self.ax_single.transAxes)
                    self.ax_single.set_ylim(bottom=0, top=1) 
                
                elif self.selected_filter != "All Detections": 
                     self.ax_single.text(0.5, 0.5, "No Detections for this month", ha='center', va='center', color=text_hex, fontsize=16, transform=self.ax_single.transAxes)
                     self.ax_single.set_ylim(bottom=0, top=1) 


                self.ax_single.set_ylabel('Total Count', color=text_hex, labelpad=15)
                
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

            # --- 6. Update both canvases ---
            if self.canvas_stacked: self.canvas_stacked.draw()
            if self.canvas_single: self.canvas_single.draw()
            
            # --- Lift frame after plots are drawn ---
            self.date_filter_frame.lift()
            
            if not force_update and self.is_running:
                print(f"Plot updated at {datetime.datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"An error occurred during plot update: {e}")
            import traceback
            traceback.print_exc()
        
        # --- 7. Schedule the next update (only if in a running state) ---
        if self.is_running and not force_update: 
            self.after_id = self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)

    def navigate_to_dashboard(self):
        print("Stopping plot update loop...")
        self.is_running = False

        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        
        self.root.after(150, super().go_back_to_dashboard)

# --- To run this page directly for testing ---
if __name__ == "__main__":
    app = WeatherPage()
    app.root.mainloop()
