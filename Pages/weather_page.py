import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH
import os
import datetime 
from PIL import Image

# --- ADDED IMPORTS FOR GRADIENT ---
import numpy as np
import matplotlib.colors as mcolors
# ------------------------------------

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
    UPDATE_INTERVAL = 10000 # 10 seconds

    def on_date_selected(self, selected_date: str):
        self.selected_date = selected_date
        
        if selected_date == "Today":
            if not self.is_running:
                print("Restarting live update loop...")
                self.is_running = True
                self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)
        else:
            if self.is_running:
                print(f"Stopping live updates. Showing data for {selected_date}.")
                self.is_running = False
                if self.after_id:
                    self.root.after_cancel(self.after_id)
                    self.after_id = None
        
        self._update_plot_data(force_update=True)

    def _update_date_selector(self, df_full: pd.DataFrame):
        if self.date_selector is None:
            return

        try:
            if df_full.empty or 'Date' not in df_full.columns:
                self.date_selector.configure(values=["Today"])
                self.date_selector.set("Today")
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

            current_selection = self.selected_date
            self.date_selector.configure(values=dropdown_options)
            
            if current_selection in dropdown_options:
                self.date_selector.set(current_selection)
            elif dropdown_options:
                self.date_selector.set(dropdown_options[0])
                self.selected_date = dropdown_options[0]
            else:
                self.date_selector.configure(values=["Today"])
                self.date_selector.set("Today")
                self.selected_date = "Today"

        except Exception as e:
            print(f"Error updating date selector: {e}")
            self.date_selector.configure(values=["Today"])
            self.date_selector.set("Today")
            
    # --- NEW: Method to check current date and update season labels ---
    def _update_season_indicator(self):
        """
        Checks today's date and updates the season labels
        based on Philippine climate patterns.
        """
        try:
            today = datetime.date.today()
            current_month = today.month # 1 (Jan) to 12 (Dec)

            season = ""
            sub_text = ""
            color = "#FFFFFF" # Default white

            if current_month in [11, 12, 1, 2]: # November - February
                season = "Dry Season (Cool)"
                sub_text = "Expect rainy and hot sunny days!"
                color = "#A9DFFF" # Light blue
            elif current_month in [3, 4, 5]: # March - May
                season = "Dry Season (Hot)"
                sub_text = "Expect extreme hot temperatures!"
                color = "#FFD1A9" # Light orange
            elif current_month in [6, 7, 8, 9, 10]: # June - October
                season = "Wet Season"
                sub_text = "Expect frequent or heavy rains!"
                color = "#C8D3D5" # Light gray-blue

            self.season_label.configure(text=season, text_color=color)
            self.season_sub_label.configure(text=sub_text, text_color=color)
        
        except Exception as e:
            print(f"Error updating season indicator: {e}")
            self.season_label.configure(text="Season: Error", text_color="red")
            self.season_sub_label.configure(text="")
    
    def __init__(self):
        super().__init__()
        
        self.is_running = True
        self.current_view = "all" 
        
        self.selected_date = "Today"
        self.date_selector = None
        self.after_id = None
        
        # --- Standard Page Setup ---
        self.create_left_panel() 
        self.create_leaf_image() 
        self.create_title(text="Weather Analytics", x=119, y=0)
        self.undo_button(command=self.navigate_to_dashboard)

        # --- MODIFIED: Create Date Filter Frame (Top-Right) ---
        self.date_filter_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.date_filter_frame.place(
            relx=0.98, 
            y=self._scale_value(25, 'y'), 
            anchor="ne" # Top-right anchor
        )
        
        # --- NEW: Create a sub-frame for the date selector row ---
        selector_row_frame = ctk.CTkFrame(self.date_filter_frame, fg_color="transparent")
        selector_row_frame.pack(side="top", anchor="e", pady=(0, 5)) # anchor="e" to right-align

        date_label = ctk.CTkLabel(
            selector_row_frame, 
            text="Select Date:",
            font=("Arial", self._scale_value(14, 'y')),
            text_color="white"
        )
        date_label.pack(side="left", padx=(5, 5))

        self.date_selector = ctk.CTkOptionMenu(
            selector_row_frame,
            values=["Today"], 
            command=self.on_date_selected,
            font=("Arial", self._scale_value(14, 'y')),
            dropdown_font=("Arial", self._scale_value(20, 'y')),
            fg_color="#2A2E3F",
            text_color="#FFFFFF",
            button_color="#383C4E",
            button_hover_color="#50556b",
            dropdown_fg_color="#2A2E3F",
            dropdown_hover_color="#383C4E",
            dropdown_text_color="#FFFFFF"
        )
        self.date_selector.set("Today")
        self.date_selector.pack(side="left", padx=(0, 10))

        # --- MODIFIED: Add Season Indicator Labels with strict font size ---
        self.season_label = ctk.CTkLabel(
            self.date_filter_frame, # Parent is the main filter frame
            text="", # Will be set by _update_season_indicator
            font=("Arial", 12, "bold"), # MODIFIED: Set to strict size 12
            text_color="white" 
        )
        self.season_label.pack(side="top", anchor="e", padx=(0, 10)) 

        self.season_sub_label = ctk.CTkLabel(
            self.date_filter_frame, # Parent is the main filter frame
            text="", # Will be set by _update_season_indicator
            font=("Arial", 12), # MODIFIED: Set to strict size 12
            text_color="white" 
        )
        self.season_sub_label.pack(side="top", anchor="e", padx=(0, 10))
        # -----------------------------------------------

        # --- Button Setup (Unchanged) ---
        
        scaled_button_width = self._scale_value(100, 'x')
        scaled_button_height = self._scale_value(40, 'y')
        scaled_img_size = (self._scale_value(30, 'x'), self._scale_value(30, 'y'))
        scaled_hover_offset = self._scale_value(5, 'y')
        scaled_padding = self._scale_value(10, 'y')
        
        try:
            self.all_icon = ctk.CTkImage(light_image=Image.open("_image_assets/all_data.png"), size=scaled_img_size)
            self.temp_icon = ctk.CTkImage(light_image=Image.open("_image_assets/temperature.png"), size=scaled_img_size)
            self.hum_icon = ctk.CTkImage(light_image=Image.open("_image_assets/humidity.png"), size=scaled_img_size)
            self.pres_icon = ctk.CTkImage(light_image=Image.open("_image_assets/pressure.png"), size=scaled_img_size)
        except Exception as e:
            print(f"Error loading button icons: {e}. Please check _image_assets folder.")
            self.all_icon = self.temp_icon = self.hum_icon = self.pres_icon = None
        

        y_all = self._scale_value(150, 'y')
        y_temp = y_all + scaled_button_height + scaled_padding
        y_hum = y_temp + scaled_button_height + scaled_padding
        y_pres = y_hum + scaled_button_height + scaled_padding
        x_pos = self._scale_value(LEFT_PANEL_WIDTH / 2, 'x')

        self.all_button = ctk.CTkButton(self.left_panel, text=" All Data", width=scaled_button_width, height=scaled_button_height, image=self.all_icon, command=lambda: self.show_view("all"), 
                                        fg_color="#2A2E3F", hover_color="#50556b", corner_radius=5, 
                                        text_color="white", font=("Arial", 14), anchor="w")
        self.all_button.place(x=x_pos, y=y_all, anchor="center")

        self.temp_button = ctk.CTkButton(self.left_panel, text=" Temperature", 
                                         width=scaled_button_width, height=scaled_button_height, 
                                         image=self.temp_icon, command=lambda: self.show_view("temp"), 
                                         fg_color="#2A2E3F", hover_color="#50556b", corner_radius=5, 
                                         text_color="white", font=("Arial", 14), anchor="w")
        self.temp_button.place(x=x_pos, y=y_temp, anchor="center")

        self.hum_button = ctk.CTkButton(self.left_panel, text=" Humidity", 
                                        width=scaled_button_width, height=scaled_button_height, 
                                        image=self.hum_icon, command=lambda: self.show_view("hum"), 
                                        fg_color="#2A2E3F", hover_color="#50556b", corner_radius=5, 
                                        text_color="white", font=("Arial", 14), anchor="w")
        self.hum_button.place(x=x_pos, y=y_hum, anchor="center")
        
        self.pres_button = ctk.CTkButton(self.left_panel, text=" Pressure", 
                                         width=scaled_button_width, height=scaled_button_height, 
                                         image=self.pres_icon, command=lambda: self.show_view("pres"), 
                                         fg_color="#2A2E3F", hover_color="#50556b", corner_radius=5, 
                                         text_color="white", font=("Arial", 14), anchor="w")
        self.pres_button.place(x=x_pos, y=y_pres, anchor="center")

        self.chart_buttons = [self.all_button, self.temp_button, self.hum_button, self.pres_button]

        # --- Chart Frame (Unchanged) ---
        chart_frame_x = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        chart_frame_y = self._scale_value(60, 'y') 
        
        self.chart_frame = ctk.CTkFrame(self.root, fg_color="#202332")
        self.chart_frame.place(
            x=chart_frame_x, 
            y=chart_frame_y,
            relwidth=1.0 - (chart_frame_x / self.root.winfo_width()),
            relheight=1.0 - (chart_frame_y / self.root.winfo_height())
        )

        self.status_label = ctk.CTkLabel(self.chart_frame, text="Initializing plot...",
                                          font=("Arial", 18))
        self.status_label.pack(expand=True)

        # --- Matplotlib Objects (Unchanged) ---
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
        
        # --- Tide Label Objects ---
        self.high_tide_label = None
        self.low_tide_label = None
        
        # --- NEW: Call the season indicator method ---
        self._update_season_indicator()
        
        # --- MODIFIED: Lift the filter frame to the front ---
        self.date_filter_frame.lift()

        # Start the plot setup
        self.root.after(100, self.setup_plot)

    def setup_plot(self):
        try:
            plt.style.use('dark_background') 
            
            self.fig_stacked, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
            self.fig_stacked.patch.set_facecolor("#202332")
            
            self.fig_stacked.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.15)
            
            self.fig_single, self.ax_single = plt.subplots(1, 1, figsize=(12, 8))
            self.fig_single.patch.set_facecolor("#202332")

            self.fig_single.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.15)
            
            self.status_label.pack_forget()
            
            # --- Create a frame for the average labels ---
            self.avg_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
            self.avg_frame.pack(side=ctk.TOP, fill="x", padx=20, pady=(5, 10))

            font_style = ("Arial", 20, "bold")
            text_color = "#FFFFFF"
            
            # Create labels with placeholder text
            self.temp_avg_label = ctk.CTkLabel(self.avg_frame, text="Temperature Avg: -- °C", font=font_style, text_color=text_color)
            self.hum_avg_label = ctk.CTkLabel(self.avg_frame, text="Humidity Avg: -- %", font=font_style, text_color=text_color)
            self.pres_avg_label = ctk.CTkLabel(self.avg_frame, text="Pressure Avg: -- hPa", font=font_style, text_color=text_color)
            
            # Create Tide labels
            self.high_tide_label = ctk.CTkLabel(self.avg_frame, text="High Tide: N/A", font=font_style, text_color=text_color)
            self.low_tide_label = ctk.CTkLabel(self.avg_frame, text="Low Tide: N/A", font=font_style, text_color=text_color)

            # --- Create Stacked Canvas ---
            self.canvas_stacked = FigureCanvasTkAgg(self.fig_stacked, master=self.chart_frame)
            self.canvas_stacked.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

            # --- Create Single Canvas (but hide it) ---
            self.canvas_single = FigureCanvasTkAgg(self.fig_single, master=self.chart_frame)
            self.canvas_single.get_tk_widget().pack_forget()
            
            self.show_view(self.current_view) 
            
            self._update_plot_data()

        except Exception as e:
            print(f"An error occurred during plot setup: {e}")
            self.status_label.configure(text=f"An error occurred during setup:\n{e}", text_color="red")
            self.status_label.pack(expand=True)

    def show_view(self, view_name):
        default_color = "#2A2E3F"   # Unselected button color
        selected_color = "#202332"  # Selected button color (matches chart bg)
        
        # 1. Reset all buttons to the default color
        for button in self.chart_buttons:
            button.configure(fg_color=default_color)
            
        # 2. Set the clicked button to the selected color
        if view_name == "all":
            self.all_button.configure(fg_color=selected_color)
        elif view_name == "temp":
            self.temp_button.configure(fg_color=selected_color)
        elif view_name == "hum":
            self.hum_button.configure(fg_color=selected_color)
        elif view_name == "pres":
            self.pres_button.configure(fg_color=selected_color)

        self.current_view = view_name
        
        # --- 1. Manage Chart Canvas Visibility ---
        if self.current_view == "all":
            self.canvas_single.get_tk_widget().pack_forget()
            self.canvas_stacked.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        else:
            self.canvas_stacked.get_tk_widget().pack_forget()
            self.canvas_single.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
            
        # --- 2. Manage Average Label Visibility ---
        self.temp_avg_label.pack_forget()
        self.hum_avg_label.pack_forget()
        self.pres_avg_label.pack_forget()
        self.high_tide_label.pack_forget()
        self.low_tide_label.pack_forget()
        
        if self.current_view == "all":
            self.high_tide_label.pack(side=ctk.LEFT, padx=10)
            self.low_tide_label.pack(side=ctk.LEFT, padx=10)
            
        elif self.current_view == "temp":
            self.temp_avg_label.pack(side=ctk.LEFT, padx=10)
            
        elif self.current_view == "hum":
            self.hum_avg_label.pack(side=ctk.LEFT, padx=10)
            
        elif self.current_view == "pres":
            self.pres_avg_label.pack(side=ctk.LEFT, padx=10)
            
        # --- 3. Force an immediate update ---
        if self.canvas_stacked: 
            self.root.after(10, self._update_plot_data, True) 

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
            return 
            
        try:
            # --- 1. Load Data ---
            if not os.path.exists(self.CSV_FILE_PATH):
                self.status_label.configure(text=f"Error: File not found.\n{self.CSV_FILE_PATH}", text_color="red")
                if not self.canvas_stacked:
                    self.status_label.pack(expand=True)
                if not force_update:
                    self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)
                return
            
            self.status_label.pack_forget()
            
            df_full = pd.read_csv(self.CSV_FILE_PATH)
            
            self._update_date_selector(df_full.copy())
            
            if df_full.empty or 'Date' not in df_full.columns or 'Time' not in df_full.columns:
                 self.ax1.clear()
                 self.ax2.clear()
                 self.ax3.clear()
                 self.ax_single.clear()
                 self.canvas_stacked.draw()
                 self.canvas_single.draw()
                 if self.is_running and not force_update: 
                     self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)
                 return
            
            df_full['Time'] = df_full['Time'].astype(str)
            df_full['Timestamp'] = pd.to_datetime(df_full['Date'] + ' ' + df_full['Time'])
            df = df_full.set_index('Timestamp')
            
            # --- NEW: Filter the DataFrame based on the date selector ---
            try:
                if self.selected_date == "Today":
                    target_date = datetime.date.today()
                    avg_label_prefix = "Feels like: "
                else:
                    target_date = datetime.datetime.strptime(self.selected_date, '%Y-%m-%d').date()
                    avg_label_prefix = "Day Avg: "
                
                filtered_df = df[df.index.date == target_date]
            
            except Exception as e:
                print(f"Error filtering date: {e}. Defaulting to today.")
                target_date = datetime.date.today()
                filtered_df = df[df.index.date == target_date]
                avg_label_prefix = "Feels like: "
            
            # --- MODIFIED: Calculate and display averages based on view ---
            try:
                avg_temp = np.nan
                avg_hum = np.nan
                avg_pres = np.nan

                if not filtered_df.empty:
                    if self.selected_date == "Today":
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
                self.pres_avg_label.configure(text=f"Pressure Avg: {avg_pres:.1f} hPa" if not pd.isna(avg_pres) else "Pressure Avg: N/A")
            
            except Exception as e:
                print(f"Error calculating averages: {e}")
                self.temp_avg_label.configure(text="Temperature Avg: Error")
                self.hum_avg_label.configure(text="Humidity Avg: Error")
                self.pres_avg_label.configure(text="Pressure Avg: Error")
            
            # --- 2. Clear all 4 axes ---
            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            self.ax_single.clear()

            # --- 3. Redraw STACKED Plot (ax1, ax2, ax3) ---
            ax_color = "#2A2E3F"
            
            # --- Plot Temp ---
            self.ax1.plot(filtered_df.index, filtered_df['Temperature'], color='red', zorder=3)
            self.ax1.set_ylabel('Temperature (°C)', color='white', labelpad=15)
            self.ax1.grid(True, linestyle='--', alpha=0.3)
            self.ax1.tick_params(axis='y', colors='white')
            self.ax1.tick_params(axis='x', colors='white')
            self.ax1.set_facecolor(ax_color)
            if not filtered_df.empty:
                self._set_dynamic_ylim(self.ax1, filtered_df['Temperature'])
                self._apply_gradient(self.ax1, filtered_df.index, filtered_df['Temperature'], 'red')

            # --- Plot Humidity ---
            self.ax2.plot(filtered_df.index, filtered_df['Humidity'], color='blue', zorder=3)
            self.ax2.set_ylabel('Humidity (%)', color='white', labelpad=15)
            self.ax2.grid(True, linestyle='--', alpha=0.3)
            self.ax2.tick_params(axis='y', colors='white')
            self.ax2.tick_params(axis='x', colors='white')
            self.ax2.set_facecolor(ax_color)
            if not filtered_df.empty:
                self._set_dynamic_ylim(self.ax2, filtered_df['Humidity'])
                self._apply_gradient(self.ax2, filtered_df.index, filtered_df['Humidity'], 'blue')

            # --- Plot Pressure ---
            self.ax3.plot(filtered_df.index, filtered_df['Pressure'], color='green', zorder=3)
            self.ax3.set_ylabel('Pressure (hPa)', color='white', labelpad=15)
            self.ax3.grid(True, linestyle='--', alpha=0.3)
            self.ax3.tick_params(axis='y', colors='white')
            self.ax3.tick_params(axis='x', colors='white')
            self.ax3.set_facecolor(ax_color)
            if not filtered_df.empty:
                self._set_dynamic_ylim(self.ax3, filtered_df['Pressure'])
                self._apply_gradient(self.ax3, filtered_df.index, filtered_df['Pressure'], 'green')

            self.ax3.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
            self.ax3.set_xlabel('Time', color='white')
            plt.setp(self.ax3.get_xticklabels(), rotation=0, ha="center", color='white')
            
            self.fig_stacked.suptitle(f"BME280 Sensor Data ({self.selected_date})", fontsize=14, color='white')
            
            # --- 4. Redraw SINGLE Plot (ax_single) based on current view ---
            title = 'Sensor Data'
            if self.current_view == "temp":
                title = f"Temperature ({self.selected_date})"
                self.ax_single.plot(filtered_df.index, filtered_df['Temperature'], color='red', zorder=3)
                self.ax_single.set_ylabel('Temperature (°C)', color='white', labelpad=15)
                if not filtered_df.empty:
                    self._set_dynamic_ylim(self.ax_single, filtered_df['Temperature'])
                    self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Temperature'], 'red')
            
            elif self.current_view == "hum":
                title = f"Humidity ({self.selected_date})"
                self.ax_single.plot(filtered_df.index, filtered_df['Humidity'], color='blue', zorder=3)
                self.ax_single.set_ylabel('Humidity (%)', color='white', labelpad=15)
                if not filtered_df.empty:
                    self._set_dynamic_ylim(self.ax_single, filtered_df['Humidity'])
                    self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Humidity'], 'blue')
                
            elif self.current_view == "pres":
                title = f"Pressure ({self.selected_date})"
                self.ax_single.plot(filtered_df.index, filtered_df['Pressure'], color='green', zorder=3)
                # --- FIX: Changed 1S5 to 15 ---
                self.ax_single.set_ylabel('Pressure (hPa)', color='white', labelpad=15)
                if not filtered_df.empty:
                    self._set_dynamic_ylim(self.ax_single, filtered_df['Pressure'])
                    self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Pressure'], 'green')
            
            else: # "all" view
                title = f"Temperature ({self.selected_date})"
                self.ax_single.plot(filtered_df.index, filtered_df['Temperature'], color='red', zorder=3)
                self.ax_single.set_ylabel('Temperature (°C)', color='white', labelpad=15)
                if not filtered_df.empty:
                    self._set_dynamic_ylim(self.ax_single, filtered_df['Temperature'])
                    # --- FIX: Changed self.ax_single._apply_gradient to self._apply_gradient ---
                    self._apply_gradient(self.ax_single, filtered_df.index, filtered_df['Temperature'], 'red')
            
            # Apply formatting to the single chart
            self.ax_single.grid(True, linestyle='--', alpha=0.3)
            self.ax_single.tick_params(axis='y', colors='white')
            self.ax_single.tick_params(axis='x', colors='white')
            self.ax_single.set_facecolor(ax_color)
            self.ax_single.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
            self.ax_single.set_xlabel('Time', color='white')
            plt.setp(self.ax_single.get_xticklabels(), rotation=0, ha="center", color='white')
            self.fig_single.suptitle(title, fontsize=14, color='white')
            
            # --- 5. Update both canvases ---
            self.canvas_stacked.draw()
            self.canvas_single.draw()
            
            if not force_update and self.is_running:
                print(f"Plot updated at {datetime.datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"An error occurred during plot update: {e}")
            import traceback
            traceback.print_exc()
        
        # --- 6. Schedule the next update (if not a forced update AND is_running) ---
        if self.is_running and not force_update: 
            self.after_id = self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)

    def navigate_to_dashboard(self):
        print("Stopping plot update loop...")
        self.is_running = False

        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        super().go_back_to_dashboard()