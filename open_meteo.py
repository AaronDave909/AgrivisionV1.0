import requests
import csv

# Coordinates for Taguig (BGC area)
LATITUDE = 14.5547
LONGITUDE = 121.0244

# Set your exact date range
START_DATE = "2026-02-19"
END_DATE = "2026-03-01"

url = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "hourly": "temperature_2m,relativehumidity_2m,surface_pressure",
    "timezone": "Asia/Manila"
}

response = requests.get(url, params=params)
data = response.json()

# Extract hourly data
times = data["hourly"]["time"]
temps = data["hourly"]["temperature_2m"]
humidity = data["hourly"]["relativehumidity_2m"]
pressure = data["hourly"]["surface_pressure"]

# Save to CSV
filename = "taguig_weather_feb2026.csv"

with open(filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    
    # Write header
    writer.writerow(["time", "temperature", "humidity", "pressure"])
    
    # Write rows
    for i in range(len(times)):
        writer.writerow([times[i], temps[i], humidity[i], pressure[i]])

print(f"Weather data successfully saved to {filename}")