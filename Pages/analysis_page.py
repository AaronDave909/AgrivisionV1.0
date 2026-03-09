import customtkinter as ctk
from PIL import Image
import cv2
import os
from ultralytics import YOLO
import datetime
import json
import math
import pandas as pd

# IMPORT ALL COLOR CONSTANTS FROM SHARED COMPONENTS
from shared_components import (
    SharedComponents as SC, LEFT_PANEL_WIDTH, 
    BG_COLOR, LEFT_PANEL_COLOR, BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR,
    custom_font_bold, custom_font_title, custom_font_regular
)

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


# Helper function to format names
def _format_name(name_str):
    """Converts snake_case names into formatted Title Case."""
    if name_str == "Downy_mildew_on_lettuce":
        return "Downy Mildew"
    if name_str == "Powdery_mildew_on_lettuce":
        return "Powdery Mildew"
    
    # General rule for all others (pests and diseases)
    return name_str.replace("_", " ").title()


class AnalysisPage(SC):
    CAPTURE_SIZE = 480
    ORIGINAL_LEFT_PANEL_WIDTH = LEFT_PANEL_WIDTH

    def __init__(self, image_path, view_only=False):
        super().__init__()

        self.image_path = image_path
        self.view_only = view_only
        self.analysis_data_dict = {} 
        self.annotated_image_data = None
        self.gallery_path = "Page_files/gallery_files"
        self.single_json_path = os.path.join(self.gallery_path, "gallery_data.json")
        os.makedirs(self.gallery_path, exist_ok=True)

        self.display_w = self._scale_value(self.CAPTURE_SIZE, 'x')
        self.display_h = self._scale_value(self.CAPTURE_SIZE, 'y')

        # --- UI Setup ---
        self.create_left_panel()
        self.create_leaf_image()
        self._create_info_panel() # Create info panel first

        if self.view_only:
            self.undo_button(command=self.return_to_gallery)
            self.trash_button(command=self.delete_gallery_entry, y_offset=195)
            initial_text = "Loading..."
        else:
            self.original_image_path = image_path 
            self.save_button(x=53.5, y=480 / 2, command=self.save_annotated_image)
            self.trash_button(command=self.trash_image)
            initial_text = "Analyzing..."

        self.image_label = ctk.CTkLabel(
            self.root, text=initial_text, font=("Arial", 20),
            fg_color=self._get_color(BG_COLOR), # Adjusted for Light/Dark Mode
            text_color=self._get_color(TEXT_COLOR),
            width=self.display_w, height=self.display_h
        )

        self.root.after(100, self._setup_display)

    def _load_master_json(self):
        """Loads the master JSON file. Returns an empty dict if it doesn't exist."""
        try:
            if os.path.exists(self.single_json_path):
                with open(self.single_json_path, 'r') as f:
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
            else:
                return {} 
        except (json.JSONDecodeError, Exception) as e:
            print(f"--- ERROR reading master JSON or file is empty: {e}. Returning empty dict.")
            return {}

    def _save_master_json(self, data):
        """Saves the provided dictionary to the master JSON file."""
        try:
            with open(self.single_json_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"--- ERROR writing master JSON: {e}")

    def _setup_display(self):
        """Places the UI elements and then runs the correct process."""
        self._place_ui_elements()
        
        if self.view_only:
            self.load_and_display_data()
        else:
            self.run_yolo_analysis()

    def _create_info_panel(self):
        """Creates the frame and labels for displaying analysis results."""
        info_panel_w = self._scale_value(190, 'x')
        info_panel_h = self._scale_value(480, 'y')

        # Using LEFT_PANEL_COLOR for the right background creates nice symmetry
        self.info_frame = ctk.CTkScrollableFrame(
            self.root, 
            width=info_panel_w, 
            height=info_panel_h, 
            fg_color=self._get_color(BG_COLOR) 
        )
        
        # --- UI STYLING: Reusable Underlined Title Font ---
        title_font = ctk.CTkFont(size=16, weight="bold", underline=True)

        # ==========================================
        # CONTAINER 1: Analysis Results
        # ==========================================
        self.results_frame = ctk.CTkFrame(
            self.info_frame, 
            fg_color=self._get_color(BUTTON_COLOR), 
            corner_radius=8
        )
        self.results_frame.pack(fill="x", padx=10, pady=(10, 10))

        title = ctk.CTkLabel(self.results_frame, text="Analysis Results", font=title_font, text_color=self._get_color(TEXT_COLOR))
        title.pack(pady=(10, 5), padx=10)

        # Helper function to create uniform label pairs inside a parent frame
        def create_info_row(parent, label_text):
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
            
            label_widget = ctk.CTkLabel(row_frame, text=f"{label_text}:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self._get_color(TEXT_COLOR), anchor="w")
            label_widget.pack(side="left", padx=(10, 2))
            
            value_label = ctk.CTkLabel(row_frame, text="---", font=ctk.CTkFont(size=12), anchor="w", text_color=self._get_color(TEXT_COLOR))
            value_label.pack(side="left", expand=True, fill="x", padx=2)
            
            row_frame.pack(fill="x", pady=4)
            return label_widget, value_label

        self.main_info_label, self.main_value_label = create_info_row(self.results_frame, "Detection") 
        _, self.accuracy_label = create_info_row(self.results_frame, "Accuracy")
        _, self.count_label = create_info_row(self.results_frame, "Detections")
        _, self.datetime_label = create_info_row(self.results_frame, "Timestamp")
        
        # Add slight padding at the bottom of the container
        ctk.CTkFrame(self.results_frame, fg_color="transparent", height=5).pack()

        # ==========================================
        # CONTAINER 2: Description (Hidden by default)
        # ==========================================
        self.desc_frame = ctk.CTkFrame(self.info_frame, fg_color=self._get_color(BUTTON_COLOR), corner_radius=8)
        
        desc_title = ctk.CTkLabel(self.desc_frame, text="Description", font=title_font, text_color=self._get_color(TEXT_COLOR))
        desc_title.pack(pady=(10, 5), padx=10)
        
        self.description_label = ctk.CTkLabel(
            self.desc_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#66BB6A", # Keep Green for healthy text
            wraplength=self._scale_value(140, 'x'), 
            justify="left",
            anchor="w"
        )
        self.description_label.pack(pady=(0, 10), padx=15, fill="x")

        # ==========================================
        # CONTAINER 3: Risk Assessment (Hidden by default)
        # ==========================================
        self.risk_frame = ctk.CTkFrame(self.info_frame, fg_color=self._get_color(BUTTON_COLOR), corner_radius=8)

        risk_title = ctk.CTkLabel(self.risk_frame, text="Risk Assessment", font=title_font, text_color=self._get_color(TEXT_COLOR))
        risk_title.pack(pady=(10, 8), padx=10)
        
        self.risk_labels = {}
        diseases = [
            ("powdery", "Powdery Mildew", "#FFA500"),
            ("downy", "Downy Mildew", "#FF6B6B"),
            ("bls", "Bacterial Leaf Spot", "#FF1744"),
            ("lmv", "Lettuce Mosaic Virus", "#D32F2F")
        ]
        
        for key, name, color in diseases:
            label = ctk.CTkLabel(self.risk_frame, text=f"{name}: --", font=ctk.CTkFont(size=10), text_color=color)
            label.pack(anchor="w", padx=12, pady=2)
            self.risk_labels[key] = label
            
        # Add slight padding at the bottom of the risk container
        ctk.CTkFrame(self.risk_frame, fg_color="transparent", height=5).pack()

    def _place_ui_elements(self):
        """Calculates and places the image label and the info panel."""
        self.root.update_idletasks()
        
        x_pos_image = self._scale_value(self.ORIGINAL_LEFT_PANEL_WIDTH, 'x')
        self.image_label.place(x=x_pos_image, y=0, anchor="nw")
        
        x_pos_info = x_pos_image + self.display_w
        self.info_frame.place(x=x_pos_info, y=0, anchor="nw")

    def save_button(self, x, y, command=None):
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_width = self._scale_value(90, 'x')
        scaled_height = self._scale_value(90, 'y')
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_hover_offset = self._scale_value(5, 'y')

        # Automatically recolor for dark/light mode
        image_path = "_image_assets/save.png"
        img_white = Image.open(image_path).convert("RGBA")
        img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])
        save_photo = ctk.CTkImage(light_image=img_dark, dark_image=img_white, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root, text="", width=scaled_width, height=scaled_height,
            image=save_photo, compound="top", command=command, 
            fg_color=self._get_color(LEFT_PANEL_COLOR), 
            hover_color=self._get_color(BUTTON_HOVER)
        )
        btn.place(x=scaled_x, y=scaled_y, anchor="center")

        def on_enter(event): btn.place_configure(y=scaled_y - scaled_hover_offset) 
        def on_leave(event): btn.place_configure(y=scaled_y) 

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def trash_button(self, command=None, y_offset=None):
        scaled_img_size = (self._scale_value(80, 'x'), self._scale_value(80, 'y'))
        scaled_width = self._scale_value(80, 'x')
        scaled_height = self._scale_value(80, 'y')
        x, y = 5, 380

        if y_offset is not None:
            y = y_offset
        
        scaled_x = self._scale_value(x, 'x')
        scaled_y = self._scale_value(y, 'y')
        scaled_hover_offset = self._scale_value(5, 'y')

        # Automatically recolor for dark/light mode
        image_path = "_image_assets/trash.png"
        img_white = Image.open(image_path).convert("RGBA")
        img_dark = self._recolor_icon(image_path, hex_color=TEXT_COLOR[0])
        trash_photo = ctk.CTkImage(light_image=img_dark, dark_image=img_white, size=scaled_img_size)
        
        btn = ctk.CTkButton(
            self.root, text="", width=scaled_width, height=scaled_height,
            image=trash_photo, compound="top", command=command,
            fg_color=self._get_color(LEFT_PANEL_COLOR), 
            hover_color=self._get_color(BUTTON_HOVER), 
            corner_radius=0
        )
        btn.place(x=scaled_x, y=scaled_y)
        btn.image = trash_photo

        def on_enter(event): btn.place_configure(y=scaled_y - scaled_hover_offset)
        def on_leave(event): btn.place_configure(y=scaled_y)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def run_yolo_analysis(self):
        try:
            model_path = "Page_files/yolov11_models/diseases.pt"
            model = YOLO(model_path)
            results = model(self.original_image_path)

            self.annotated_image_data = results[0].plot()
            self.display_image(self.annotated_image_data)

            self.update_info_panel(results)

        except Exception as e:
            print(f"--- ERROR during YOLO analysis: {e}")
            self.image_label.configure(text=f"Error analyzing image.", text_color="red")
            self.main_value_label.configure(text="Analysis Failed")
            self.accuracy_label.configure(text="---")
            self.count_label.configure(text="---")

    def update_info_panel(self, results):
        """Extracts data from YOLO results and populates the panel."""
        now = datetime.datetime.now()
        timestamp = now.strftime("%b %d, %Y %I:%M %p")

        if results and len(results[0].boxes) > 0:
            top_detection = results[0].boxes[0]
            detection_name = results[0].names[int(top_detection.cls)]
            accuracy = f"{top_detection.conf.item()*100:.2f}%"
            detection_count = str(len(results[0].boxes))
            is_healthy = False
        else:
            detection_name = "Healthy"
            accuracy = "N/A"
            detection_count = "0"
            is_healthy = True
            
        self.analysis_data_dict = {
            "disease": detection_name, 
            "accuracy": accuracy,
            "count": detection_count,
            "timestamp": timestamp,
            "is_healthy": is_healthy
        }
        
        self.populate_info_panel(self.analysis_data_dict)

    def get_latest_weather_data(self):
        """Reads the latest temperature and humidity from weather.csv."""
        try:
            csv_path = "Page_files/weather.csv"
            if not os.path.exists(csv_path):
                return None, None
            
            df = pd.read_csv(csv_path)
            if df.empty or 'Temperature' not in df.columns or 'Humidity' not in df.columns:
                return None, None
            
            latest_temp = df['Temperature'].iloc[-1]
            latest_humidity = df['Humidity'].iloc[-1]
            return latest_temp, latest_humidity
        except Exception as e:
            print(f"Error reading weather data: {e}")
            return None, None

    def populate_info_panel(self, data_dict):
        """Populates the info panel labels from a given data dictionary."""
        
        if "disease" in data_dict:
            self.main_info_label.configure(text="Disease:")
            name = data_dict.get("disease", "---")
        elif "pest" in data_dict:
            self.main_info_label.configure(text="Pest:")
            name = data_dict.get("pest", "---")
        else:
            self.main_info_label.configure(text="Detection:")
            name = "Unknown"
            
        self.main_value_label.configure(text=_format_name(name))
        
        self.accuracy_label.configure(text=data_dict.get("accuracy", "---"))
        self.count_label.configure(text=data_dict.get("count", "---"))
        
        # Format the timestamp strictly to fit the card visually
        timestamp = data_dict.get("timestamp", "---")
        if len(timestamp) > 12:
            pass 
        self.datetime_label.configure(text=timestamp)
        
        # Handle healthy classification with UI cards
        is_healthy = data_dict.get("is_healthy", False)
        
        if is_healthy:
            # Show the Description Card
            self.desc_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Formatted Bullet Points
            bullet_points = (
                "â€¢ No visual signs of disease.\n"
                "â€¢ Leaf structures are intact.\n"
                "â€¢ Plant appears completely healthy."
            )
            self.description_label.configure(text=bullet_points)
            
            # Show the Risk Assessment Card
            if not self.risk_frame.winfo_ismapped():
                self.risk_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Get current weather data and calculate risks
            temp, humidity = self.get_latest_weather_data()
            
            if temp is not None and humidity is not None:
                # Calculate risks
                powdery = classify_risk(powdery_mildew_risk(temp, humidity))
                downy = classify_risk(downy_mildew_risk(temp, humidity))
                bls = classify_risk(bls_risk(temp, humidity))
                lmv = classify_risk(lmv_risk(temp, humidity))
                
                def get_color(level):
                    return "#FF1744" if level == "HIGH" else "#FFA500" if level == "MODERATE" else "#66BB6A"
                
                self.risk_labels["powdery"].configure(
                    text=f"Powdery Mildew: {powdery[0]}% ({powdery[1]})",
                    text_color=get_color(powdery[1])
                )
                self.risk_labels["downy"].configure(
                    text=f"Downy Mildew: {downy[0]}% ({downy[1]})",
                    text_color=get_color(downy[1])
                )
                self.risk_labels["bls"].configure(
                    text=f"Bacterial Leaf Spot: {bls[0]}% ({bls[1]})",
                    text_color=get_color(bls[1])
                )
                self.risk_labels["lmv"].configure(
                    text=f"Lettuce Mosaic Virus: {lmv[0]}% ({lmv[1]})",
                    text_color=get_color(lmv[1])
                )
            else:
                # Show placeholder if weather data unavailable
                names = {
                    "powdery": "Powdery Mildew",
                    "downy": "Downy Mildew",
                    "bls": "Bacterial Leaf Spot",
                    "lmv": "Lettuce Mosaic Virus"
                }

                for key in self.risk_labels:
                    self.risk_labels[key].configure(text=f"{names[key]}: Data unavailable")
        else:
            # Hide Description and Risk frames entirely for diseased plants
            self.desc_frame.pack_forget()
            self.risk_frame.pack_forget()
        
        self.root.update_idletasks()

    def load_and_display_data(self):
        """Loads annotated image and analysis JSON from gallery paths."""
        try:
            image_filename = os.path.basename(self.image_path)
            
            if not os.path.exists(self.image_path):
                print(f"--- ERROR: Missing image file.")
                self.image_label.configure(text="Error: File not found.", text_color="red")
                return

            self.annotated_image_data = cv2.imread(self.image_path)
            self.display_image(self.annotated_image_data)

            master_data = self._load_master_json()
            image_specific_data = master_data.get(image_filename)

            if image_specific_data:
                # Determine if this is a healthy classification
                disease_name = image_specific_data.get("disease", "")
                is_healthy = disease_name.lower() == "healthy" or disease_name == "No Disease Detected"
                image_specific_data["is_healthy"] = is_healthy
                self.populate_info_panel(image_specific_data)
            else:
                print(f"--- ERROR: No data found for {image_filename} in {self.single_json_path}")
                self.populate_info_panel({}) 

        except Exception as e:
            print(f"--- ERROR loading gallery data: {e}")
            self.image_label.configure(text="Error loading data.", text_color="red")


    def display_image(self, image_data_bgr):
        image_rgb = cv2.cvtColor(image_data_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        pil_img_resized = pil_image.resize((self.display_w, self.display_h), Image.Resampling.BILINEAR)
        ctk_image = ctk.CTkImage(light_image=pil_img_resized, size=(self.display_w, self.display_h))
        self.image_label.configure(image=ctk_image, text="")
        self.image_label.image = ctk_image

    def save_annotated_image(self):
        if self.annotated_image_data is not None:
            filename = os.path.basename(self.original_image_path)
            base_filename = os.path.splitext(filename)[0]
            
            image_filename = f"{base_filename}.jpg"
            save_path_img = os.path.join(self.gallery_path, image_filename)

            try:
                cv2.imwrite(save_path_img, self.annotated_image_data)
                print(f"â Annotated image saved to: {save_path_img}")
                
                master_data = self._load_master_json()
                master_data[image_filename] = self.analysis_data_dict
                self._save_master_json(master_data)
                print(f"â Analysis data saved to: {self.single_json_path}")

                os.remove(self.original_image_path)
                self.return_to_capture()

            except Exception as e:
                print(f"--- ERROR saving files: {e}")

    def trash_image(self):
        if os.path.exists(self.original_image_path):
            os.remove(self.original_image_path)
            print(f"ðï¸ Image trashed: {self.original_image_path}")
        self.return_to_capture()

    def return_to_capture(self):
        self.root.destroy()
        from Pages.capture import CapturePage
        capture_app = CapturePage()
        capture_app.root.mainloop()

    def delete_gallery_entry(self):
        """Deletes the .jpg and its entry from the master .json file."""
        try:
            image_filename = os.path.basename(self.image_path)
            
            # 1. Delete the image file
            if os.path.exists(self.image_path):
                os.remove(self.image_path)
                print(f"ðï¸ Deleted image: {self.image_path}")
            
            # 2. Load the master dictionary
            master_data = self._load_master_json()
            
            # 3. Remove the entry for this image
            if image_filename in master_data:
                del master_data[image_filename]
                print(f"ðï¸ Deleted data for {image_filename} from {self.single_json_path}")
                # 4. Save the modified master dictionary
                self._save_master_json(master_data)
            else:
                print(f"â ï¸ Warning: No data found for {image_filename} in master JSON.")
                
        except Exception as e:
            # FIX 1: Replaced Unicode character with basic ASCII string
            print(f"--- ERROR deleting files: {e}")
        
        # FIX 2: Call return_to_gallery without destroying immediately in this context
        self.root.after(0, self.return_to_gallery) 

    def return_to_gallery(self):
        self.root.destroy()
        from Pages.gallery import GalleryPage 
        gallery_app = GalleryPage()
        gallery_app.root.mainloop()

# --- To run this page directly for testing (if needed) ---
if __name__ == "__main__":
    app = AnalysisPage("test_image.jpg", view_only=True)
    app.root.mainloop()
