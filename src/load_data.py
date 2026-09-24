import json
import hashlib
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
# Load messages.json
# -----------------------------

with open("data/messages.json", "r") as file:
    messages = json.load(file)


# -----------------------------
# Counters
# -----------------------------

messages_inserted = 0
messages_skipped = 0

transactions_inserted = 0
transactions_skipped = 0


# -----------------------------
# Process messages
# -----------------------------

for message in messages:

    pts_id = message["PtsId"]
    protocol = message["Protocol"]

    # Create deterministic fingerprint
    message_json = json.dumps(
        message,
        sort_keys=True,
        separators=(",", ":")
    )

    message_fingerprint = hashlib.sha256(
        message_json.encode("utf-8")
    ).hexdigest()


    # -------------------------
    # Check if message exists
    # -------------------------

    cursor.execute(
        """
        SELECT message_id
        FROM messages
        WHERE message_fingerprint = %s;
        """,
        (message_fingerprint,)
    )

    existing_message = cursor.fetchone()


    if existing_message:

        message_id = existing_message[0]

        messages_skipped += 1

    else:

        # Insert message

        cursor.execute(
            """
            INSERT INTO messages (
                pts_id,
                protocol,
                raw_message,
                message_fingerprint
            )
            VALUES (%s, %s, %s, %s)
            RETURNING message_id;
            """,
            (
                pts_id,
                protocol,
                json.dumps(message),
                message_fingerprint
            )
        )

        message_id = cursor.fetchone()[0]

        messages_inserted += 1


    # -----------------------------
    # Process packets
    # -----------------------------

    for packet in message["Packets"]:

        if packet["Type"] != "UploadPumpTransaction":
            continue

        data = packet["Data"]


        # -------------------------
        # Create transaction fingerprint
        # -------------------------

        transaction_string = "|".join([
            pts_id,
            data["Pump"],
            data["Nozzle"],
            data["FuelGradeId"],
            data["FuelGradeName"],
            data["Transaction"],
            str(data["Volume"]),
            str(data["Price"]),
            str(data["Amount"]),
            data["DateTime"]
        ])

        transaction_fingerprint = hashlib.sha256(
            transaction_string.encode("utf-8")
        ).hexdigest()


        # -------------------------
        # Check if transaction exists
        # -------------------------

        cursor.execute(
            """
            SELECT transaction_id
            FROM pump_transactions
            WHERE transaction_fingerprint = %s;
            """,
            (transaction_fingerprint,)
        )

        existing_transaction = cursor.fetchone()


        if existing_transaction:

            transactions_skipped += 1

            continue


        # -------------------------
        # Insert transaction
        # -------------------------

        cursor.execute(
            """
            INSERT INTO pump_transactions (
                message_id,
                pts_id,
                pump,
                nozzle,
                fuel_grade_id,
                fuel_grade_name,
                controller_transaction,
                volume_litres,
                price_per_litre,
                amount_sar,
                controller_datetime,
                raw_data,
                transaction_fingerprint
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            );
            """,
            (
                message_id,
                pts_id,
                data["Pump"],
                data["Nozzle"],
                data["FuelGradeId"],
                data["FuelGradeName"],
                data["Transaction"],
                data["Volume"],
                data["Price"],
                data["Amount"],
                data["DateTime"],
                json.dumps(data),
                transaction_fingerprint
            )
        )

        transactions_inserted += 1


# -----------------------------
# Commit all changes
# -----------------------------

conn.commit()


# -----------------------------
# Close connection
# -----------------------------

cursor.close()
conn.close()


# -----------------------------
# Print results
# -----------------------------

print("Messages inserted:", messages_inserted)
print("Messages skipped:", messages_skipped)

print("Transactions inserted:", transactions_inserted)
print("Transactions skipped:", transactions_skipped)

print("\nLoader completed successfully.")