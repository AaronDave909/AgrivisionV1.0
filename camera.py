import cv2
import datetime
import os
from PIL import Image, ImageTk

# Assumes:
# - self.save_path = os.path.join("Page_files", "gallery_files")
# - self.disease_result, self.captured_image_path, self.cap, self.running, self.current_frame exist
# - self.disease_detector(image_path) exists externally

# -------------------------
# 🎥 1. OPEN CAMERA
# -------------------------
def open_camera(self):
    """Starts the webcam and begins live feed updates."""
    self.cap = cv2.VideoCapture(0)
    if not self.cap.isOpened():
        print("❌ Could not open camera.")
        return

    self.running = True
    self.capture_btn.configure(state="normal")
    self.update_frame()

def update_frame(self):
    """Updates the live camera preview frame."""
    if self.running and self.cap:
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
    if self.running:
        self.after(10, self.update_frame)

# -------------------------
# 📸 2. CAPTURE SCREEN
# -------------------------
def capture_image(self):
    """Captures a frame and saves it temporarily."""
    if self.current_frame is not None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        temp_filename = f"temp_capture_{timestamp}.jpg"
        temp_path = os.path.join(self.save_path, temp_filename)
        cv2.imwrite(temp_path, self.current_frame)
        self.captured_image_path = temp_path
        print(f"✅ Image captured: {temp_path}")
        self.run_analysis()

# -------------------------
# 🧠 3. RUN ANALYSIS
# -------------------------
def run_analysis(self):
    """Runs the external disease analysis function on the captured image."""
    if self.captured_image_path:
        print("🧠 Running disease analysis...")
        self.disease_result = self.disease_detector(self.captured_image_path)
        print(f"Analysis Result: {self.disease_result}")
        self.open_review_window()

# -------------------------
# 🖼️ 4. OPEN REVIEW WINDOW
# -------------------------
def open_review_window(self):
    """Opens the image review window (user decides to save or discard)."""
    # stop camera feed
    self.running = False
    if self.cap:
        self.cap.release()
        self.cap = None

    # clear main camera UI (you’ll replace this with your GUI logic)
    for widget in self.winfo_children():
        widget.destroy()

    # display captured image preview
    img = Image.open(self.captured_image_path)
    img.thumbnail((600, 400))
    imgtk = ImageTk.PhotoImage(img)

    self.review_label = ctk.CTkLabel(self, image=imgtk, text="")
    self.review_label.image = imgtk
    self.review_label.pack(pady=20)

    disease_text = self.disease_result if self.disease_result else "No disease detected"
    self.info_label = ctk.CTkLabel(self, text=f"Analysis Result: {disease_text}")
    self.info_label.pack(pady=10)

    # Buttons should call self.save_image() or self.discard_image()
    # You’ll define those button widgets in your GUI layer.

# -------------------------
# 💾 4.1 SAVE IMAGE
# -------------------------
def save_image(self):
    """Saves analyzed image to gallery with disease code in filename."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    disease_code = self.disease_result if self.disease_result else "NONE"
    filename = f"{timestamp}_{disease_code}.jpg"
    final_path = os.path.join(self.save_path, filename)
    os.rename(self.captured_image_path, final_path)
    print(f"✅ Image saved: {final_path}")
    self.back_to_camera()

# -------------------------
# 🗑 4.2 DISCARD IMAGE
# -------------------------
def discard_image(self):
    """Deletes temporary capture and returns to camera view."""
    if self.captured_image_path and os.path.exists(self.captured_image_path):
        os.remove(self.captured_image_path)
        print("🗑 Temporary image discarded.")
    self.back_to_camera()

# -------------------------
# 🔙 5. BACK TO CAMERA
# -------------------------
def back_to_camera(self):
    """Resets UI to camera preview state."""
    self.running = False
    if self.cap:
        self.cap.release()
        self.cap = None
    # rebuild your capture window here
    self.build_main_window()
