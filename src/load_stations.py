import json
import psycopg2


# -----------------------------
# Database connection
# -----------------------------

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="postgres",
    password="Aa123123"
)

cursor = conn.cursor()


# -----------------------------
# Load stations.json
# -----------------------------

with open("data/stations.json", "r") as file:
    data = json.load(file)


# -----------------------------
# Insert stations
# -----------------------------

for station in data["stations"]:

    cursor.execute(
        """
        INSERT INTO stations (
            station_code,
            station_name,
            pts_id,
            utc_offset_minutes
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (station_code) DO NOTHING;
        """,
        (
            station["station_code"],
            station["station_name"],
            station["pts_id"],
            station["utc_offset_minutes"]
        )
    )


# -----------------------------
# Commit
# -----------------------------

conn.commit()


# -----------------------------
# Close connection
# -----------------------------

cursor.close()
conn.close()


print("Stations loaded successfully.")