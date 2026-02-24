import multiprocessing
import cv2
import time
import os

# --- Real Dashboard Import ---
# Using the import path provided by the user
from Pages.main_dashboard import MyDashboard

def play_splash(video_path, stop_event):
    """
    Plays a video file in a fullscreen, topmost window.
    Stops when the video ends or the `stop_event` is set (by the main app).
    
    Args:
        video_path (str): The file path to the video.
        stop_event (multiprocessing.Event): An event to signal when to stop.
    """
    # Check if the video file exists
    if not os.path.exists(video_path):
        print(f"Splash Error: Video file not found at {video_path}")
        return

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Splash Error: Could not open video file {video_path}")
            return

        # Create a window that adapts to the video size and stays on top
        window_name = "Splash Screen"
        
        # Use cv2.WINDOW_NORMAL first, then set properties
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # --- IMPORTANT CHANGE: Set the window to cover the entire screen (fullscreen) ---
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        # This property helps keep the window on top
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)


        while cap.isOpened():
            # Check if the main app has signaled to stop
            if stop_event.is_set():
                print("Splash: Emergency stop signal received. Closing video.")
                break

            ret, frame = cap.read()
            if not ret:
                # This executes when the video naturally finishes playing
                print("Splash: Video finished naturally. Closing.")
                break

            cv2.imshow(window_name, frame)
            
            # Wait for 25ms (this controls the video framerate)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                print("Splash: 'q' key pressed. Closing.")
                break

        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Splash Error: An exception occurred: {e}")
    finally:
        # Ensure all OpenCV windows are closed
        cv2.destroyAllWindows()


# --- Main Execution ---
if __name__ == "__main__":
    # Set the path to your video file
    video_file = "_image_assets/Agrivision_Final_Animation.mp4"

    # 1. Setup the signal mechanism
    stop_splash_event = multiprocessing.Event()

    # 2. Start the video process
    splash_process = multiprocessing.Process(
        target=play_splash, 
        args=(video_file, stop_splash_event)
    )
    
    print("Main: Starting splash screen process...")
    splash_process.start()

    # 3. Load your main application (This is the time-consuming step)
    print("Main: Loading main application...")
    # NOTE: The video is playing right now while MyDashboard() executes.
    try:
        app = MyDashboard()
        print("Main: Application loaded.")
    except Exception as e:
        print(f"Main Error: Failed to load MyDashboard: {e}")
        # Ensure video is stopped even if app loading fails
        stop_splash_event.set()
        splash_process.join()
        exit(1) # Exit the program if the app failed to load

    # 4. Once the app is loaded, we now wait for the video to naturally finish.
    print("Main: Application finished loading, waiting for video to complete...")
    
    # 5. Wait for the splash screen process to finish closing its window (i.e., video finishes playing)
    splash_process.join()
    print("Main: Splash screen closed (video completed).")

    # 6. Run the main application UI
    print("Main: Running main application UI.")
    app.run()