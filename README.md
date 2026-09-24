Forecourt Assessment
Overview

This project processes forecourt controller messages for Pure-IN fuel stations.

The input data contains:

Pump sales transactions (UploadPumpTransaction)
Tank/probe measurements (ProbeMeasurements)
Registered station/controller mappings

The solution loads the data into PostgreSQL and produces daily sales per station in litres and SAR, grouped by the Riyadh calendar day.

Project Structure
text
forecourt-assessment/
├── data/
│   ├── messages.json
│   └── stations.json
├── src/
│   ├── inspect_data.py
│   ├── load_stations.py
│   └── load_data.py
├── sql/
│   └── daily_sales.sql
└── README.md
Database

The solution uses PostgreSQL and creates three tables:

stations

Stores the registered stations and their controller information:

station_code
station_name
pts_id
utc_offset_minutes
messages

Stores the original received messages, including the raw JSON payload.

pump_transactions

Stores normalized pump sale transactions extracted from the messages.

Note: ProbeMeasurements are retained inside the original messages.raw_message JSON. A separate probe table was not required because the requested output is daily sales.

Setup

Install the Python dependency:

bash
python -m pip install psycopg2-binary

Create the PostgreSQL tables using the schema created for the assessment.

The Python scripts connect to the PostgreSQL database named postgres. Update the database password in the Python files before running them.

Running the Solution
1. Inspect the input data
bash
python src/inspect_data.py

This checks the number of messages, stations, packet types, controller IDs, and controllers that are not mapped to a registered station.

2. Load stations
bash
python src/load_stations.py

This loads the station mapping into the stations table.

3. Load messages and transactions
bash
python src/load_data.py

This loads the original messages and extracts UploadPumpTransaction packets into pump_transactions.

4. Generate daily sales

From psql, run:

sql
\i 'C:/path/to/forecourt-assessment/sql/daily_sales.sql'

The query returns:

Station
Riyadh calendar date
Total litres
Total SAR
Idempotency and Duplicate Handling

The loader is designed to be idempotent. Running it multiple times does not create additional records.

Messages: a SHA-256 fingerprint is generated from the normalized message JSON.
Pump transactions: a SHA-256 fingerprint is generated from the transaction details:
PtsId
Pump
Nozzle
Fuel grade
Transaction number
Volume
Price
Amount
Controller datetime

This was necessary because the controller transaction number is not globally unique. The input data contains reused transaction numbers.

The database also has UNIQUE constraints on the fingerprints as an additional protection.

Observed results:

151 pump transaction packets in the input
148 unique transactions
3 exact duplicate transactions

The first loader run inserted 148 transactions and skipped 3 duplicates. A second run inserted 0 new transactions.

Data Quality and Untrusted Data

The input data was treated as untrusted source data.

Unknown controller

One controller ID appears in messages.json but is not present in stations.json:

text
007727854799034600674638

The raw message/transaction is retained, but it cannot be assigned to a station in the station-level daily sales report because there is no registered station mapping.

Amount inconsistencies

The reported Amount was compared with Volume × Price.

Most differences were 0.01 SAR, which is consistent with rounding.

One transaction had a significant inconsistency:

text
Volume            = 22.08 L
Price             = 2.33 SAR/L
Calculated amount = 51.45 SAR
Reported amount   = 514.50 SAR

The source value was preserved rather than silently corrected. The anomaly was documented as a data-quality issue.

Timezone Handling

The controller provides a DateTime and each station has a utc_offset_minutes.

The daily sales query converts the controller time using the station offset and then evaluates the date in Asia/Riyadh.

This ensures that sales are grouped by the Riyadh calendar day as requested.

Design Decisions
Raw messages are preserved in JSONB.
Pump transactions are normalized into a separate table for reporting.
Duplicate detection does not rely on the transaction number alone.
Source values are preserved even when data-quality checks identify inconsistencies.
Unmapped controller data is retained rather than deleted.
The solution focuses on the requested daily sales output without adding unnecessary complexity.
Example Output

The daily sales query produces one row per station per Riyadh calendar day, with total litres and total SAR.

For the provided data, this results in 12 station/day rows: 4 stations across 3 dates.