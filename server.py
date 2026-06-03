from flask import Flask, request
import os

app = Flask(__name__)

# This is where all the data will be permanently saved on your Pi
MASTER_CSV = "master_weather_log.csv"

@app.route('/data', methods=['POST'])
def receive_data():
    # Make sure we are receiving CSV data
    if request.content_type == 'text/csv':
        # Decode the raw bytes into a string
        data = request.data.decode('utf-8').strip()
        if not data:
            return "Empty data", 400

        lines = data.split('\n')
        file_exists = os.path.isfile(MASTER_CSV)
        
        with open(MASTER_CSV, 'a') as f:
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # If this is the first line (header) AND our master file already exists, skip it
                if i == 0 and "DateTime" in line and file_exists:
                    continue
                
                # Write the data to the master file
                f.write(line + '\n')
                
        print(f"Received and saved {len(lines)} lines of data.")
        return "Data received successfully", 200
        
    else:
        return "Unsupported Media Type, expected text/csv", 415

if __name__ == '__main__':
    # Changed port to 5050 to avoid the Port 5000 conflict!
    app.run(host='0.0.0.0', port=5050, debug=False)
