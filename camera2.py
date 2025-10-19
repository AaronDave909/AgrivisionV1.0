import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import datetime
import os

def disease_detector(image_path):
    # This function returns a code like 'ABC', 'XYZ', or None
    return "ABC"  # For testing purposes

class CameraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Camera Capture System")
        self.geometry("900x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Directory setup
        self.save_path = os.path.join("Page_files", "gallery_files")

        # Camera attributes
        self.cap = None
        self.running = False
        self.current_frame = None
        self.captured_image_path = None
        self.disease_result = None

        # UI setup
        self.build_main_window()


    def build_main_window(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.video_label = ctk.CTkLabel(self, text="")
        self.video_label.pack(pady=20, expand=True)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(btn_frame, text="📷 Open Camera", command=self.open_camera)
        self.start_btn.grid(row=0, column=0, padx=10)

        self.capture_btn = ctk.CTkButton(btn_frame, text="📸 Capture", command=self.capture_image, state="disabled")
        self.capture_btn.grid(row=0, column=1, padx=10)

        self.back_btn = ctk.CTkButton(btn_frame, text="⬅ Back", command=self.back_to_camera)
        self.back_btn.grid(row=0, column=2, padx=10)

    def open_camera(self):
        self.cap = cv2.VideoCapture(1)
        if not self.cap.isOpened():
            print("❌ Could not open camera.")
            return

        self.running = True
        self.capture_btn.configure(state="normal")
        self.update_frame()

    def update_frame(self):
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

    def capture_image(self):
        if self.current_frame is not None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
            temp_filename = f"temp_capture_{timestamp}.jpg"
            temp_path = os.path.join(self.save_path, temp_filename)
            cv2.imwrite(temp_path, self.current_frame)
            self.captured_image_path = temp_path
            print(f"✅ Image captured: {temp_path}")
            self.run_analysis()

    def run_analysis(self):
        if self.captured_image_path:
            print("🧠 Running disease analysis...")
            self.disease_result = disease_detector(self.captured_image_path)
            print(f"Analysis Result: {self.disease_result}")
            self.open_review_window()

    # -------------------------
    # 🖼️ REVIEW WINDOW
    # -------------------------
    def open_review_window(self):
        # Stop camera view
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

        for widget in self.winfo_children():
            widget.destroy()

        img = Image.open(self.captured_image_path)
        img.thumbnail((600, 400))
        imgtk = ImageTk.PhotoImage(img)

        preview_label = ctk.CTkLabel(self, image=imgtk, text="")
        preview_label.image = imgtk
        preview_label.pack(pady=20)

        disease_text = self.disease_result if self.disease_result else "No disease detected"
        info_label = ctk.CTkLabel(self, text=f"Analysis Result: {disease_text}")
        info_label.pack(pady=10)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        save_btn = ctk.CTkButton(btn_frame, text="💾 Save", command=self.save_image)
        save_btn.grid(row=0, column=0, padx=10)

        discard_btn = ctk.CTkButton(btn_frame, text="🗑 Discard", command=self.discard_image)
        discard_btn.grid(row=0, column=1, padx=10)

    # -------------------------
    # 💾 SAVE IMAGE
    # -------------------------
    def save_image(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        disease_code = self.disease_result if self.disease_result else "NONE"
        filename = f"{timestamp}_{disease_code}.jpg"
        final_path = os.path.join(self.save_path, filename)

        os.rename(self.captured_image_path, final_path)
        print(f"✅ Image saved: {final_path}")
        self.back_to_camera()

    # -------------------------
    # 🗑 DISCARD IMAGE
    # -------------------------
    def discard_image(self):
        if self.captured_image_path and os.path.exists(self.captured_image_path):
            os.remove(self.captured_image_path)
            print("🗑 Temporary image discarded.")
        self.back_to_camera()

    # -------------------------
    # 🔙 BACK TO CAMERA
    # -------------------------
    def back_to_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.build_main_window()

if __name__ == "__main__":
    app = CameraApp()
    app.mainloop()
