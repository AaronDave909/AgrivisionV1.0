import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from shared_components import SharedComponents as SC, LEFT_PANEL_WIDTH
import os
import datetime 
from PIL import Image # Import Image

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

        df = pd.read_csv(csv_path, parse_dates=[['Date', 'Time']])
        if df.empty:
            print("Weather CSV is empty.")
            return None, None, None

        df = df.rename(columns={'Date_Time': 'Timestamp'}).set_index('Timestamp')
        
        latest_time = df.index.max()
        ten_mins_ago = latest_time - pd.Timedelta(minutes=10)
        recent_df = df[df.index >= ten_mins_ago]
        
        if recent_df.empty:
            print("No recent weather data in the last 10 minutes.")
            return None, None, None

        avg_temp = recent_df['Temperature'].mean()
        avg_hum = recent_df['Humidity'].mean()
        avg_pres = recent_df['Pressure'].mean()
        
        # Return None for any value that couldn't be calculated
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
    
    def __init__(self):
        super().__init__()
        
        self.is_running = True # Flag to control the update loop
        self.current_view = "all" # Default view is "all"
        
        # --- Standard Page Setup ---
        self.create_left_panel() 
        self.create_leaf_image() 
        self.create_title(text="Weather Analytics", x=119, y=0)
        self.undo_button(command=self.navigate_to_dashboard) # This is the inherited button

        # --- Button Setup (Unchanged) ---
        
        scaled_button_width = self._scale_value(100, 'x') # Wider
        scaled_button_height = self._scale_value(40, 'y') # Shorter
        scaled_img_size = (self._scale_value(30, 'x'), self._scale_value(30, 'y')) # Smaller icons
        scaled_hover_offset = self._scale_value(5, 'y')
        scaled_padding = self._scale_value(10, 'y') # Padding between buttons
        
        try:
            self.all_icon = ctk.CTkImage(light_image=Image.open("_image_assets/all_data.png"), size=scaled_img_size)
            self.temp_icon = ctk.CTkImage(light_image=Image.open("_image_assets/temperature.png"), size=scaled_img_size)
            self.hum_icon = ctk.CTkImage(light_image=Image.open("_image_assets/humidity.png"), size=scaled_img_size)
            self.pres_icon = ctk.CTkImage(light_image=Image.open("_image_assets/pressure.png"), size=scaled_img_size)
        except Exception as e:
            print(f"Error loading button icons: {e}. Please check _image_assets folder.")
            self.all_icon = self.temp_icon = self.hum_icon = self.pres_icon = None
        
        def create_hover_bindings(button, base_y, hover_offset):
            def on_enter(event): button.place_configure(y=base_y - hover_offset)
            def on_leave(event): button.place_configure(y=base_y)
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)

        y_all = self._scale_value(120, 'y')
        y_temp = y_all + scaled_button_height + scaled_padding
        y_hum = y_temp + scaled_button_height + scaled_padding
        y_pres = y_hum + scaled_button_height + scaled_padding
        x_pos = self._scale_value(LEFT_PANEL_WIDTH / 2, 'x')

        self.all_button = ctk.CTkButton(self.left_panel, text=" All Data", width=scaled_button_width, height=scaled_button_height, image=self.all_icon, command=lambda: self.show_view("all"), fg_color="#2A2E3F", hover_color="#2A2E3F", corner_radius=0, text_color="white", font=("Arial", 14), anchor="w")
        self.all_button.place(x=x_pos, y=y_all, anchor="center")
        create_hover_bindings(self.all_button, y_all, scaled_hover_offset)

        self.temp_button = ctk.CTkButton(self.left_panel, text=" Temperature", width=scaled_button_width, height=scaled_button_height, image=self.temp_icon, command=lambda: self.show_view("temp"), fg_color="#2A2E3F", hover_color="#2A2E3F", corner_radius=0, text_color="white", font=("Arial", 14), anchor="w")
        self.temp_button.place(x=x_pos, y=y_temp, anchor="center")
        create_hover_bindings(self.temp_button, y_temp, scaled_hover_offset)

        self.hum_button = ctk.CTkButton(self.left_panel, text=" Humidity", width=scaled_button_width, height=scaled_button_height, image=self.hum_icon, command=lambda: self.show_view("hum"), fg_color="#2A2E3F", hover_color="#2A2E3F", corner_radius=0, text_color="white", font=("Arial", 14), anchor="w")
        self.hum_button.place(x=x_pos, y=y_hum, anchor="center")
        create_hover_bindings(self.hum_button, y_hum, scaled_hover_offset)
        
        self.pres_button = ctk.CTkButton(self.left_panel, text=" Pressure", width=scaled_button_width, height=scaled_button_height, image=self.pres_icon, command=lambda: self.show_view("pres"), fg_color="#2A2E3F", hover_color="#2A2E3F", corner_radius=0, text_color="white", font=("Arial", 14), anchor="w")
        self.pres_button.place(x=x_pos, y=y_pres, anchor="center")
        create_hover_bindings(self.pres_button, y_pres, scaled_hover_offset)

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

        # Start the plot setup
        self.root.after(100, self.setup_plot)

    def setup_plot(self):
        """
        Creates *both* Matplotlib Figures (stacked and single) and Canvases.
        This function only runs one time.
        """
        try:
            plt.style.use('dark_background') 
            
            self.fig_stacked, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
            self.fig_stacked.patch.set_facecolor("#202332")
            
            self.fig_single, self.ax_single = plt.subplots(1, 1, figsize=(12, 8))
            self.fig_single.patch.set_facecolor("#202332")
            
            self.status_label.pack_forget()
            
            # --- Create a frame for the average labels ---
            self.avg_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
            self.avg_frame.pack(side=ctk.TOP, fill="x", padx=20, pady=(5, 10))

            font_style = ("Arial", 40, "bold")
            text_color = "#FFFFFF"
            
            # Create labels with placeholder text
            self.temp_avg_label = ctk.CTkLabel(self.avg_frame, text="Temperature Avg: -- °C", font=font_style, text_color=text_color)
            self.hum_avg_label = ctk.CTkLabel(self.avg_frame, text="Humidity Avg: -- %", font=font_style, text_color=text_color)
            self.pres_avg_label = ctk.CTkLabel(self.avg_frame, text="Pressure Avg: -- hPa", font=font_style, text_color=text_color)
            
            # Create Tide labels
            self.high_tide_label = ctk.CTkLabel(self.avg_frame, text="High Tide: N/A", font=font_style, text_color=text_color)
            self.low_tide_label = ctk.CTkLabel(self.avg_frame, text="Low Tide: N/A", font=font_style, text_color=text_color)
            # Do not pack them yet

            # --- Create Stacked Canvas ---
            self.canvas_stacked = FigureCanvasTkAgg(self.fig_stacked, master=self.chart_frame)
            self.canvas_stacked.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

            # --- Create Single Canvas (but hide it) ---
            self.canvas_single = FigureCanvasTkAgg(self.fig_single, master=self.chart_frame)
            self.canvas_single.get_tk_widget().pack_forget() # Hide this one
            
            self.show_view(self.current_view) 
            
            self._update_plot_data()

        except Exception as e:
            print(f"An error occurred during plot setup: {e}")
            self.status_label.configure(text=f"An error occurred during setup:\n{e}", text_color="red")
            self.status_label.pack(expand=True)

    # --- THIS METHOD IS NOW MODIFIED ---
    def show_view(self, view_name):
        """Swaps the visible chart canvas AND the average labels."""
        self.current_view = view_name
        
        # --- 1. Manage Chart Canvas Visibility ---
        if self.current_view == "all":
            self.canvas_single.get_tk_widget().pack_forget()
            self.canvas_stacked.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
        else:
            self.canvas_stacked.get_tk_widget().pack_forget()
            self.canvas_single.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
            
        # --- 2. Manage Average Label Visibility ---
        # First, hide all labels
        self.temp_avg_label.pack_forget()
        self.hum_avg_label.pack_forget()
        self.pres_avg_label.pack_forget()
        self.high_tide_label.pack_forget()
        self.low_tide_label.pack_forget()
        
        # Second, re-pack only the ones we want to see
        if self.current_view == "all":
            # --- MODIFIED: Only show tide placeholders ---
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

    def _update_plot_data(self, force_update=False):
        """
        Runs on a loop. Clears all axes, re-reads CSV, and redraws data on *both* charts.
        """
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
            df = pd.read_csv(self.CSV_FILE_PATH, parse_dates=[['Date', 'Time']])
            df = df.rename(columns={'Date_Time': 'Timestamp'}).set_index('Timestamp')
            
            # --- Calculate and display 10-minute averages ---
            try:
                if not df.empty:
                    latest_time = df.index.max()
                    ten_mins_ago = latest_time - pd.Timedelta(minutes=10)
                    recent_df = df[df.index >= ten_mins_ago]
                    
                    if not recent_df.empty:
                        avg_temp = recent_df['Temperature'].mean()
                        avg_hum = recent_df['Humidity'].mean()
                        avg_pres = recent_df['Pressure'].mean()
                        
                        self.temp_avg_label.configure(text=f"Feels like: {avg_temp:.1f} °C")
                        self.hum_avg_label.configure(text=f"Humidity Avg: {avg_hum:.1f} %")
                        self.pres_avg_label.configure(text=f"Pressure Avg: {avg_pres:.1f} hPa")
                    else:
                        self.temp_avg_label.configure(text="Temperature Avg: N/A")
                        self.hum_avg_label.configure(text="Humidity Avg: N/A")
                        self.pres_avg_label.configure(text="Pressure Avg: N/A")
                else:
                    raise ValueError("DataFrame is empty")
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
            
            self.ax1.plot(df.index, df['Temperature'], color='red')
            self.ax1.set_ylabel('Temperature (°C)', color='white')
            self.ax1.grid(True, linestyle='--', alpha=0.3)
            self.ax1.tick_params(axis='y', colors='white')
            self.ax1.tick_params(axis='x', colors='white')
            self.ax1.set_facecolor(ax_color)

            self.ax2.plot(df.index, df['Humidity'], color='blue')
            self.ax2.set_ylabel('Humidity (%)', color='white')
            self.ax2.grid(True, linestyle='--', alpha=0.3)
            self.ax2.tick_params(axis='y', colors='white')
            self.ax2.tick_params(axis='x', colors='white')
            self.ax2.set_facecolor(ax_color)

            self.ax3.plot(df.index, df['Pressure'], color='green')
            self.ax3.set_ylabel('Pressure (hPa)', color='white')
            self.ax3.grid(True, linestyle='--', alpha=0.3)
            self.ax3.tick_params(axis='y', colors='white')
            self.ax3.tick_params(axis='x', colors='white')
            self.ax3.set_facecolor(ax_color)

            self.ax3.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
            self.ax3.set_xlabel('Time', color='white')
            plt.setp(self.ax3.get_xticklabels(), rotation=45, ha="right", color='white')
            
            self.fig_stacked.suptitle('BME280 Sensor Data (All)', fontsize=16, color='white')
            self.fig_stacked.tight_layout(rect=[0, 0.03, 1, 0.95])

            # --- 4. Redraw SINGLE Plot (ax_single) based on current view ---
            title = 'Sensor Data'
            if self.current_view == "temp":
                title = "Temperature Over Time"
                self.ax_single.plot(df.index, df['Temperature'], color='red')
                self.ax_single.set_ylabel('Temperature (°C)', color='white')
            
            elif self.current_view == "hum":
                title = "Humidity Over Time"
                self.ax_single.plot(df.index, df['Humidity'], color='blue')
                self.ax_single.set_ylabel('Humidity (%)', color='white')
                
            elif self.current_view == "pres":
                title = "Pressure Over Time"
                self.ax_single.plot(df.index, df['Pressure'], color='green')
                self.ax_single.set_ylabel('Pressure (hPa)', color='white')
            
            else: # "all" view is active, but we should plot *something* in the hidden chart
                title = "Temperature Over Time"
                self.ax_single.plot(df.index, df['Temperature'], color='red')
                self.ax_single.set_ylabel('Temperature (°C)', color='white')
            
            # Apply formatting to the single chart
            self.ax_single.grid(True, linestyle='--', alpha=0.3)
            self.ax_single.tick_params(axis='y', colors='white')
            self.ax_single.tick_params(axis='x', colors='white')
            self.ax_single.set_facecolor(ax_color)
            self.ax_single.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))
            self.ax_single.set_xlabel('Time', color='white')
            plt.setp(self.ax_single.get_xticklabels(), rotation=45, ha="right", color='white')
            self.fig_single.suptitle(title, fontsize=16, color='white')
            self.fig_single.tight_layout(rect=[0, 0.03, 1, 0.95])
            
            # --- 5. Update both canvases ---
            self.canvas_stacked.draw()
            self.canvas_single.draw()
            
            if not force_update:
                print(f"Plot updated at {datetime.datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"An error occurred during plot update: {e}")
        
        # --- 6. Schedule the next update (if not a forced update) ---
        if self.is_running and not force_update: 
            self.root.after(self.UPDATE_INTERVAL, self._update_plot_data)

    def navigate_to_dashboard(self):
        """Stops the update loop and returns to dashboard."""
        print("Stopping plot update loop...")
        self.is_running = False # This is CRITICAL
        
        # Call the inherited go_back_to_dashboard
        super().go_back_to_dashboard()