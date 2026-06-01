from flask import Flask, request, send_from_directory
import datetime
import os

# --- Configuration ---
CSV_FILE_PATH = "/home/red/AgrivisionV1.0/Page_files/weather.csv" # The file to save data to
CSV_HEADER = "Date,Time,Temperature,Humidity,Pressure\n"
REPORTS_DIR = "/home/red/AgrivisionV1.0/_reports_"
# ---------------------

app = Flask(__name__)

def log_to_csv(data_line):
    """Appends a line of data to the CSV file, creating it with a header if needed."""
    
    # Check if the file exists
    file_exists = os.path.isfile(CSV_FILE_PATH)
    
    # Open the file in 'a' (append) mode
    # 'with' handles closing the file automatically
    with open(CSV_FILE_PATH, 'a') as f:
        # If the file didn't exist, write the header first
        if not file_exists:
            f.write(CSV_HEADER)
            
        # Write the new data line
        f.write(data_line)

@app.route("/data", methods=["POST"])
def handle_data():
    """Listens for POST requests from the ESP32."""
    if request.method == "POST":
        
        # --- 1. Get Data from ESP32 ---
        data = request.get_json()
        
        try:
            temp = data["temperature"]
            humidity = data["humidity"]
            pressure = data["pressure"]
            
            # --- 2. Get Current Date & Time (from the Pi) ---
            now = datetime.datetime.now()
            date_str = now.strftime("%Y-%m-%d") # Format: 2025-11-03
            time_str = now.strftime("%H:%M:%S") # Format: 13:41:11
            
            # --- 3. Format the new CSV line ---
            # Add a newline character at the end
            csv_line = f"{date_str},{time_str},{temp},{humidity},{pressure}\n"
            
            # --- 4. Write to File ---
            log_to_csv(csv_line)
            
            # Print to Pi's terminal
            print(f"Data logged: {csv_line.strip()}") 
            
            # --- 5. Send Success Response ---
            return "Data logged successfully", 200

        except KeyError:
            # This happens if the ESP32 sends bad JSON
            print("Error: Received malformed JSON data")
            return "Malformed data", 400
            
    return "OK", 200

@app.route("/download/<path:filename>")
def download_file(filename):
    """When a phone scans the QR code, it asks this route for the file."""
    print(f"? Phone requested download for: {filename}")
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    # Runs the server on your Pi's hotspot IP (like 10.42.0.1)
    app.run(host="0.0.0.0", port=5001, debug=False)
