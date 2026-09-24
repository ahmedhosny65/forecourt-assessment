import json
from datetime import datetime, timedelta

with open("data/messages.json", "r") as file:
    messages = json.load(file)

with open("data/stations.json", "r") as file:
    stations = json.load(file)


# Create mapping: PtsId -> station information
station_map = {}

for station in stations["stations"]:
    station_map[station["pts_id"]] = station


total_transactions = 0
invalid_datetimes = []
unknown_controllers = []
date_counts = {}


for message in messages:
    pts_id = message["PtsId"]

    # Check if controller exists in stations.json
    station = station_map.get(pts_id)

    for packet in message["Packets"]:
        if packet["Type"] != "UploadPumpTransaction":
            continue

        data = packet["Data"]

        total_transactions += 1

        datetime_value = data["DateTime"]

        # Check DateTime format
        try:
            dt = datetime.fromisoformat(datetime_value)
        except ValueError:
            invalid_datetimes.append({
                "PtsId": pts_id,
                "Transaction": data["Transaction"],
                "DateTime": datetime_value
            })
            continue

        # Unknown controller
        if station is None:
            if pts_id not in unknown_controllers:
                unknown_controllers.append(pts_id)

            continue

        # Convert controller time to UTC using the station offset
        offset_minutes = station["utc_offset_minutes"]

        utc_time = dt - timedelta(minutes=offset_minutes)

        # Riyadh is UTC+3
        riyadh_time = utc_time + timedelta(hours=3)

        riyadh_date = riyadh_time.date().isoformat()

        date_counts[riyadh_date] = date_counts.get(riyadh_date, 0) + 1


print("Total transactions:", total_transactions)

print("\nInvalid DateTime:", len(invalid_datetimes))

if invalid_datetimes:
    for item in invalid_datetimes:
        print(item)


print("\nUnknown controllers:", len(unknown_controllers))

for pts_id in unknown_controllers:
    print(pts_id)


print("\nTransactions by Riyadh calendar date:")

for date in sorted(date_counts):
    print(date, "->", date_counts[date])