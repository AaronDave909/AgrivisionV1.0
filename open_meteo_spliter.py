import csv

input_file = "taguig_weather_feb2026.csv"
output_file = "taguig_weather_feb2026_split.csv"

with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    header = next(reader)  # skip original header
    writer.writerow(["date", "time", "temperature", "humidity", "pressure"])

    for row in reader:
        datetime_value = row[0]  # 2026-02-19T00:00
        date_part, time_part = datetime_value.split("T")

        writer.writerow([date_part, time_part, row[1], row[2], row[3]])

print("New CSV created:", output_file)