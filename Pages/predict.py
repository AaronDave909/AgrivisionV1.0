from PIL import Image
import customtkinter as ctk
import math
import pandas as pd
import os
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
from shared_components import SharedComponents as SC, BUTTON_HOVER, BUTTON_COLOR, custom_font_title, LEFT_PANEL_WIDTH, LEFT_PANEL_COLOR # Import scaled font

# ===============================
# Disease Risk Calculation Functions
# ===============================
def gaussian_temp(T, T_opt, sigma):
    """Gaussian temperature response function"""
    return math.exp(-((T - T_opt) ** 2) / (2 * (sigma ** 2)))


def logistic_humidity(RH, k, RH_mid):
    """Logistic humidity response function"""
    return 1 / (1 + math.exp(-k * (RH - RH_mid)))


def powdery_mildew_risk(T, RH):
    """Calculate Powdery Mildew risk"""
    temp_risk = gaussian_temp(T, T_opt=22, sigma=4)
    humidity_risk = logistic_humidity(RH, k=0.18, RH_mid=85)
    return temp_risk * humidity_risk


def downy_mildew_risk(T, RH):
    """Calculate Downy Mildew risk"""
    temp_risk = gaussian_temp(T, T_opt=19, sigma=3.5)
    humidity_risk = logistic_humidity(RH, k=0.25, RH_mid=90)
    return temp_risk * humidity_risk


def bls_risk(T, RH):
    """Calculate Bacterial Leaf Spot risk"""
    temp_risk = gaussian_temp(T, T_opt=25, sigma=4)
    humidity_risk = logistic_humidity(RH, k=0.45, RH_mid=88)
    return temp_risk * humidity_risk


def lmv_risk(T, RH):
    """Calculate Lettuce Mosaic Virus risk"""
    temp_risk = gaussian_temp(T, T_opt=25, sigma=5)
    humidity_factor = logistic_humidity(RH, k=0.15, RH_mid=55)
    return temp_risk * humidity_factor


def classify_risk(risk):
    """Convert risk value to percentage and classification level"""
    percent = risk * 100

    if percent < 40:
        level = "LOW"
    elif percent < 70:
        level = "MODERATE"
    else:
        level = "HIGH"

    return round(percent, 2), level


class PredictPage(SC):
    CSV_FILE_PATH = "Page_files/weather.csv"
    UPDATE_INTERVAL = 10000  # 10 seconds for demo (change to 600000 for 10 minutes)

    def __init__(self):
        super().__init__()

        self.is_running = True
        self.current_view = "manual"  # "manual" or "auto"
        self.after_id = None
        
        self.create_left_panel()
        self.create_leaf_image()

        self.scale_x_val = lambda val: self._scale_value(val, 'x')
        self.scale_y_val = lambda val: self._scale_value(val, 'y')

        # Title
        self.title_label = ctk.CTkLabel(self.root, text="Environmental Risk Index", font=tuple(custom_font_title))
        self.title_label.place(x=self.scale_x_val(115), y=self.scale_y_val(8))

        # --- Left Panel Buttons ---
        scaled_button_width = self._scale_value(100, 'x')
        scaled_button_height = self._scale_value(40, 'y')
        scaled_padding = self._scale_value(10, 'y')
        scaled_img_size = (self._scale_value(30, 'x'), self._scale_value(30, 'y'))

        try:
            self.undo_icon = ctk.CTkImage(light_image=Image.open("_image_assets/Undo.png"), size=scaled_img_size)
       
        except Exception as e:
            print(f"Error loading button icons: {e}. Please check _image_assets folder.")
            self.all_icon = self.temp_icon = self.hum_icon = self.pres_icon = self.disease_icon = self.pest_icon = self.undo_icon = None
        
        x_pos = self._scale_value(LEFT_PANEL_WIDTH / 2, 'x')
        y_manual = self._scale_value(200, 'y')
        y_auto = y_manual + scaled_button_height + scaled_padding
        y_return = y_auto + scaled_button_height + scaled_padding
        
        btn_font = ("Arial", 10)
        
        self.manual_button = ctk.CTkButton(
            self.left_panel, text="Manual Input",
            width=scaled_button_width, height=scaled_button_height,
            command=lambda: self.show_view("manual"),
            fg_color=LEFT_PANEL_COLOR, hover_color="#50556b",
            corner_radius=5, text_color="white", font=btn_font
        )
        self.manual_button.place(x=x_pos, y=y_manual, anchor="center")
        
        self.auto_button = ctk.CTkButton(
            self.left_panel, text="Auto Weather",
            width=scaled_button_width, height=scaled_button_height,
            command=lambda: self.show_view("auto"),
            fg_color=LEFT_PANEL_COLOR, hover_color="#50556b",
            corner_radius=5, text_color="white", font=btn_font
        )
        self.auto_button.place(x=x_pos, y=y_auto, anchor="center")
        
        self.return_button = ctk.CTkButton(
                                            self.left_panel, text="Return",
                                            width=scaled_button_width, height=scaled_button_height,
                                            image=self.undo_icon, command=self.go_back_to_dashboard,
                                            fg_color=LEFT_PANEL_COLOR, hover_color="#50556b",
                                            corner_radius=5, text_color="white", font=btn_font, anchor="w"
        )
        self.return_button.place(x=x_pos, y=y_return, anchor="center")

        # --- Main Content Area ---
        left_offset = self._scale_value(LEFT_PANEL_WIDTH, 'x')
        top_offset = self._scale_value(50, 'y')
        
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.place(
            x=left_offset,
            y=top_offset,
            relwidth=0.85,
            relheight=0.8
        )

        # --- Manual Input View ---
        self.manual_frame = ctk.CTkScrollableFrame(self.main_container, 
                                                   fg_color=LEFT_PANEL_COLOR, 
                                                   width=self._scale_value(430, 'x'),
                                                   height=self._scale_value(200, 'y'),
                                                   corner_radius=8)
        self.manual_frame.pack(fill="y", pady=100, expand=False)
        
        # Input Frame for Temperature and Humidity
        input_frame = ctk.CTkFrame(self.manual_frame, fg_color="#383C4E", corner_radius=8)
        input_frame.pack(fill="x", pady=(0, 15), padx=10)

        input_label = ctk.CTkLabel(input_frame, text="Input Environmental Data", font=("Arial", 12, "bold"))
        input_label.pack(anchor="w", padx=12, pady=(10, 8))

        # Temperature Input
        temp_label = ctk.CTkLabel(input_frame, text="Temperature (°C):", font=("Arial", 11))
        temp_label.pack(anchor="w", padx=12, pady=(0, 3))
        
        self.temp_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., 22.5")
        self.temp_entry.pack(anchor="w", padx=12, pady=(0, 10), fill="x")

        # Humidity Input
        humidity_label = ctk.CTkLabel(input_frame, text="Relative Humidity (%):", font=("Arial", 11))
        humidity_label.pack(anchor="w", padx=12, pady=(0, 3))
        
        self.humidity_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., 75")
        self.humidity_entry.pack(anchor="w", padx=12, pady=(0, 12), fill="x")

        # Calculate Button
        calc_button = ctk.CTkButton(input_frame, text="Calculate Risk", fg_color=BUTTON_HOVER, hover_color=BUTTON_HOVER, command=self.calculate_risks)
        calc_button.pack(anchor="w", padx=12, pady=(0, 12), fill="x")

        # Results Frame
        results_frame = ctk.CTkFrame(self.manual_frame, fg_color="#383C4E", corner_radius=8)
        results_frame.pack(fill="x", pady=(0, 10), padx=10)

        results_label = ctk.CTkLabel(results_frame, text="Risk Assessment Results", font=("Arial", 12, "bold"))
        results_label.pack(anchor="w", padx=12, pady=(10, 8))

        # Disease risk labels
        self.powdery_label = ctk.CTkLabel(results_frame, text="Powdery Mildew: --", font=("Arial", 11), text_color="#FFA500")
        self.powdery_label.pack(anchor="w", padx=12, pady=3, fill="x")

        self.downy_label = ctk.CTkLabel(results_frame, text="Downy Mildew: --", font=("Arial", 11), text_color="#FF6B6B")
        self.downy_label.pack(anchor="w", padx=12, pady=3, fill="x")

        self.bls_label = ctk.CTkLabel(results_frame, text="⚠ Bacterial Leaf Spot: --", font=("Arial", 11), text_color="#FF1744")
        self.bls_label.pack(anchor="w", padx=12, pady=3, fill="x")

        self.lmv_label = ctk.CTkLabel(results_frame, text="⚠ Lettuce Mosaic Virus: --", font=("Arial", 11), text_color="#D32F2F")
        self.lmv_label.pack(anchor="w", padx=12, pady=3, fill="x")

        # Status message
        self.status_label = ctk.CTkLabel(results_frame, text="Enter values and click Calculate", font=("Arial", 10), text_color="#888888")
        self.status_label.pack(anchor="w", padx=12, pady=(12, 12), fill="x")

        # --- Auto Weather View (Chart) ---
        self.auto_frame = ctk.CTkFrame(self.main_container, fg_color=LEFT_PANEL_COLOR, corner_radius=8)
        
        # Matplotlib objects
        self.fig = None
        self.ax_temp = None
        self.ax_hum = None
        self.canvas = None
        
        # Auto mode labels
        self.auto_temp_label = None
        self.auto_hum_label = None
        self.auto_risk_labels = {}
        
        # Show manual view by default
        self.show_view("manual")
        
        # Start auto-update loop
        self.root.after(1000, self.update_auto_data)

    def show_view(self, view_name):
        """Switch between manual input and auto weather views"""
        self.current_view = view_name
        
        if view_name == "manual":
            self.manual_button.configure(fg_color=BUTTON_HOVER)
            self.auto_button.configure(fg_color=LEFT_PANEL_COLOR)
            self.manual_frame.pack(fill="y", expand=False, pady=10)
            if self.auto_frame.winfo_exists():
                self.auto_frame.pack_forget()
        else:  # auto
            self.auto_button.configure(fg_color=BUTTON_HOVER)
            self.manual_button.configure(fg_color=LEFT_PANEL_COLOR)
            self.manual_frame.pack_forget()
            self.auto_frame.pack(fill="y", expand=False)
            if self.canvas is None:
                self.setup_plot()

    def setup_plot(self):
        """Initialize matplotlib figures for temperature and humidity"""
        # Remove old canvas if exists
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        # Create figure with 2 subplots
        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor=LEFT_PANEL_COLOR)
        self.ax_temp = self.fig.add_subplot(121)
        self.ax_hum = self.fig.add_subplot(122)
        
        # Style the plots
        for ax in [self.ax_temp, self.ax_hum]:
            ax.set_facecolor("#383C4E")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('white')
            ax.spines['bottom'].set_color('white')
            ax.tick_params(colors='white', labelsize=9)
        
        self.ax_temp.set_title("Temperature (°C)", color='white', fontsize=11, fontweight='bold')
        self.ax_hum.set_title("Humidity (%)", color='white', fontsize=11, fontweight='bold')
        
        self.fig.tight_layout()
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.auto_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create info frame below chart
        info_frame = ctk.CTkFrame(self.auto_frame, fg_color="#383C4E", corner_radius=8)
        info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        info_label = ctk.CTkLabel(info_frame, text="Current Values & Risk Index", font=("Arial", 11, "bold"))
        info_label.pack(anchor="w", padx=12, pady=(10, 8))
        
        # Current values
        self.auto_temp_label = ctk.CTkLabel(info_frame, text="Latest Temp: -- °C", font=("Arial", 10))
        self.auto_temp_label.pack(anchor="w", padx=12, pady=2)
        
        self.auto_hum_label = ctk.CTkLabel(info_frame, text="Latest Humidity: -- %", font=("Arial", 10))
        self.auto_hum_label.pack(anchor="w", padx=12, pady=2)
        
        # Risk labels
        self.auto_risk_labels = {}
        diseases = [
            ("powdery", "Powdery Mildew", "#FFA500"),
            ("downy", "Downy Mildew", "#FF6B6B"),
            ("bls", "⚠ Bacterial Leaf Spot", "#FF1744"),
            ("lmv", "⚠ Lettuce Mosaic Virus", "#D32F2F")
        ]
        
        for key, name, color in diseases:
            label = ctk.CTkLabel(info_frame, text=f"{name}: --", font=("Arial", 10), text_color=color)
            label.pack(anchor="w", padx=12, pady=2)
            self.auto_risk_labels[key] = label
        
        ctk.CTkLabel(info_frame, text="(Auto-updating every 10 seconds)", font=("Arial", 8), text_color="#888888").pack(anchor="w", padx=12, pady=(8, 10))

    def update_auto_data(self):
        """Read CSV and update plots periodically"""
        if not self.is_running or self.current_view != "auto":
            self.after_id = self.root.after(self.UPDATE_INTERVAL, self.update_auto_data)
            return
        
        try:
            if not os.path.exists(self.CSV_FILE_PATH):
                return
            
            df = pd.read_csv(self.CSV_FILE_PATH)
            if df.empty or 'Date' not in df.columns or 'Time' not in df.columns:
                return
            
            df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            
            latest_date = df['Timestamp'].dt.date.max()
            df_today = df[df['Timestamp'].dt.date == latest_date].copy()
            
            if df_today.empty:
                return
            
            # Update plots
            self._update_plot_data(df_today)
            
        except Exception as e:
            print(f"Error updating auto data: {e}")
        
        # Reschedule
        self.after_id = self.root.after(self.UPDATE_INTERVAL, self.update_auto_data)

    def _update_plot_data(self, df_tail):
        """Update matplotlib plots with Auto-Zoom and Gradient Fills"""
        if self.canvas is None:
            return
        
        timestamps = df_tail['Timestamp'].tolist()
        temps = df_tail['Temperature'].tolist()
        hums = df_tail['Humidity'].tolist()
        
        if not timestamps:
            return
        
        # 1. Update Latest Value Labels
        latest_temp, latest_hum = temps[-1], hums[-1]
        self.auto_temp_label.configure(text=f"Latest Temp: {latest_temp:.1f} °C")
        self.auto_hum_label.configure(text=f"Latest Humidity: {latest_hum:.1f} %")
        
        # 2. Risk Calculations (Keep existing logic)
        powdery = classify_risk(powdery_mildew_risk(latest_temp, latest_hum))
        downy = classify_risk(downy_mildew_risk(latest_temp, latest_hum))
        bls = classify_risk(bls_risk(latest_temp, latest_hum))
        lmv = classify_risk(lmv_risk(latest_temp, latest_hum))
        
        def get_color(level):
            return "#FF1744" if level == "HIGH" else "#FFA500" if level == "MODERATE" else "#66BB6A"
        
        self.auto_risk_labels["powdery"].configure(text=f"Powdery Mildew: {powdery[0]}% ({powdery[1]})", text_color=get_color(powdery[1]))
        self.auto_risk_labels["downy"].configure(text=f"Downy Mildew: {downy[0]}% ({downy[1]})", text_color=get_color(downy[1]))
        self.auto_risk_labels["bls"].configure(text=f"⚠ Bacterial Leaf Spot: {bls[0]}% ({bls[1]})", text_color=get_color(bls[1]))
        self.auto_risk_labels["lmv"].configure(text=f"⚠ Lettuce Mosaic Virus: {lmv[0]}% ({lmv[1]})", text_color=get_color(lmv[1]))
        
        # 3. Update Plots
        self.ax_temp.clear()
        self.ax_hum.clear()

        def apply_gradient_plot(ax, x, y, title, color_hex):
            """Apply line plot with gradient fill (from weather_page.py)"""
            try:
                val_max, val_min = max(y), min(y)
                padding = (val_max - val_min) * 0.15 if val_max != val_min else 1.0
                
                # 1. Plot the main line
                ax.plot(x, y, color=color_hex, linewidth=2, zorder=3)
                
                # 2. Create gradient fill using fill_between
                fill = ax.fill_between(x, y, color='none', zorder=2)
                clip_path = fill.get_paths()[0]
                
                # 3. Get axis bounds
                x_num = mdates.date2num(x)
                xmin, xmax = x_num[0], x_num[-1]
                ymin, ymax = val_min - padding, val_max + padding
                
                # 4. Create colormap with transparency
                line_color_rgb = mcolors.to_rgb(color_hex)
                colors = [(*line_color_rgb, 0.4), (*line_color_rgb, 0.0)]
                cmap = mcolors.LinearSegmentedColormap.from_list('gradient', colors, N=256)
                
                # 5. Create gradient image
                gradient = np.linspace(1, 0, 256).reshape(-1, 1)
                gradient_img = np.repeat(gradient, 2, axis=1)
                
                # 6. Apply gradient with clipping
                img = ax.imshow(gradient_img, cmap=cmap, aspect='auto', origin='lower',
                               extent=[xmin, xmax, ymin, ymax], zorder=1)
                img.set_clip_path(clip_path, transform=ax.transData)
                
                # 7. Set dynamic limits
                ax.set_ylim(ymin, ymax)
                ax.set_xlim(xmin, xmax)
                
                # 8. Styling
                ax.set_title(title, color='white', fontsize=11, fontweight='bold')
                ax.set_facecolor("#383C4E")
                ax.grid(True, linestyle='--', alpha=0.1, color='gray')
                
                # X-Axis ticks
                latest_time = x[-1]
                noon_time = latest_time.replace(hour=12, minute=0, second=0, microsecond=0)
                ticks = sorted(list(set([x[0], latest_time] + ([noon_time] if x[0] <= noon_time <= latest_time else []))))
                
                ax.xaxis.set_major_locator(ticker.FixedLocator([mdates.date2num(t) for t in ticks]))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                
                # Spines
                for spine in ax.spines.values():
                    spine.set_color('white')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.tick_params(colors='white', labelsize=8)
                
            except Exception as e:
                print(f"Gradient plotting error: {e}")
                # Fallback: just plot the line without gradient
                ax.plot(x, y, color=color_hex, linewidth=2)
                ax.set_title(title, color='white', fontsize=11, fontweight='bold')
                ax.set_facecolor("#383C4E")

        # Apply the Gradient View
        apply_gradient_plot(self.ax_temp, timestamps, temps, "Temperature Profile", '#FF5733')
        apply_gradient_plot(self.ax_hum, timestamps, hums, "Humidity Profile", '#4A90E2')

        self.fig.autofmt_xdate(rotation=0, ha='center')
        self.fig.tight_layout()
        self.canvas.draw()

    def calculate_risks(self):
        """Calculate disease risks based on user input"""
        try:
            temperature = float(self.temp_entry.get())
            humidity = float(self.humidity_entry.get())

            # Validate ranges
            if temperature < -50 or temperature > 60:
                self.status_label.configure(text="Temperature should be -50 to 60°C", text_color="#FF6B6B")
                return
            if humidity < 0 or humidity > 100:
                self.status_label.configure(text="Humidity should be 0-100%", text_color="#FF6B6B")
                return

            # Calculate risks
            powdery = classify_risk(powdery_mildew_risk(temperature, humidity))
            downy = classify_risk(downy_mildew_risk(temperature, humidity))
            bls = classify_risk(bls_risk(temperature, humidity))
            lmv = classify_risk(lmv_risk(temperature, humidity))

            # Determine color based on risk level
            def get_color(level):
                if level == "HIGH":
                    return "#FF1744"
                elif level == "MODERATE":
                    return "#FFA500"
                else:
                    return "#66BB6A"

            # Update labels
            self.powdery_label.configure(
                text=f"Powdery Mildew: {powdery[0]}% ({powdery[1]})",
                text_color=get_color(powdery[1])
            )
            self.downy_label.configure(
                text=f"Downy Mildew: {downy[0]}% ({downy[1]})",
                text_color=get_color(downy[1])
            )
            self.bls_label.configure(
                text=f"⚠ Bacterial Leaf Spot: {bls[0]}% ({bls[1]})",
                text_color=get_color(bls[1])
            )
            self.lmv_label.configure(
                text=f"⚠  Mosaic Virus: {lmv[0]}% ({lmv[1]})",
                text_color=get_color(lmv[1])
            )
            self.status_label.configure(
                text=f"✓ Calculated at T={temperature}°C, RH={humidity}%",
                text_color="#66BB6A"
            )

        except ValueError:
            self.status_label.configure(text="Please enter valid numbers", text_color="#FF6B6B")

    def go_back_to_dashboard(self):
        """Navigate back to the main dashboard"""
        self.is_running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.root.destroy()
        from Pages.main_dashboard import MyDashboard
        dashboard = MyDashboard()
        dashboard.root.mainloop()


