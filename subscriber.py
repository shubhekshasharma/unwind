# subscriber.py
import paho.mqtt.client as mqtt
import time
from llm import get_llm_response, get_llm_client
import sqlite3
import json

START_TOPIC = "device/events/unwind_start"
STOP_TOPIC = "device/events/unwind_stop"
PICKUP_TOPIC = "device/events/phone_pickup"
DOCK_TOPIC = "device/events/phone_dock"
DATABASE_FILE="user_device_data.db"
DEVICE_ID = "device1"


def init_db(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            user_id TEXT,
            event_type TEXT,
            session_started_at TEXT,
            is_phone_down BOOLEAN,
            status TEXT,
            created_at TEXT,
            pickup_count INTEGER DEFAULT 0,
            alarm_time TEXT,
            duration_seconds REAL
        )
    """)
    conn.commit()
    # Migrate existing tables that predate these columns
    for alter_sql in [
        "ALTER TABLE sessions ADD COLUMN pickup_count INTEGER DEFAULT 0",
        "ALTER TABLE sessions ADD COLUMN alarm_time TEXT",
        "ALTER TABLE sessions ADD COLUMN duration_seconds REAL",
    ]:
        try:
            c.execute(alter_sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists


def insert_session_data(conn, msg_payload):
    try:
        data = json.loads(msg_payload)
    except json.JSONDecodeError:
        print("Failed to parse message as JSON")
        return

    message_id = data.get("message_id") or data.get("command") + "_" + data.get("start_time")
    user_id = data.get("device_id")
    event_type = data.get("command")
    session_started_at = data.get("start_time")
    is_phone_down = True
    status = "completed"
    created_at = data.get("date")
    pickup_count = data.get("pickup_count", 0)
    alarm_time = data.get("alarm_time")
    duration_seconds = data.get("duration")

    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions
            (message_id, user_id, event_type, session_started_at, is_phone_down,
             status, created_at, pickup_count, alarm_time, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (message_id, user_id, event_type, session_started_at, is_phone_down,
          status, created_at, pickup_count, alarm_time, duration_seconds))
    conn.commit()
    print(f"Inserted session from message_id {message_id}")


def query_last_sessions(conn, n=3):
    """Return the last n sessions as a list of dictionaries."""
    # make cursor return Row objects
    conn.row_factory = sqlite3.Row 
    c = conn.cursor()
    c.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (n,))
    rows = c.fetchall()

    # Convert each row to a dictionary for better representation of data
    result = [dict(row) for row in rows]
    return result



def on_connect(client, userdata, flags, rc):
    print(f"Connecting to broker with return code {rc}")
    if rc == 0:
        print("Successfully connected to broker")
        client.subscribe(START_TOPIC)
        client.subscribe(STOP_TOPIC)
        client.subscribe(PICKUP_TOPIC)
        client.subscribe(DOCK_TOPIC)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    conn = userdata["conn"]
    payload_str = msg.payload.decode()

    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        print(f"[SUBSCRIBER] Could not parse payload: {payload_str}")
        return

    if msg.topic == START_TOPIC:
        print(f"[SUBSCRIBER] Session started at {data.get('start_time')}")

    elif msg.topic == PICKUP_TOPIC:
        print(f"[SUBSCRIBER] Phone pickup #{data.get('pickup_count')} recorded")

    elif msg.topic == DOCK_TOPIC:
        print(f"[SUBSCRIBER] Phone docked")

    elif msg.topic == STOP_TOPIC:
        insert_session_data(conn, msg.payload)
        last_sessions = query_last_sessions(conn, 3)
        duration_min = round(data.get("duration", 0) / 60, 1)
        prompt = (
            f"Tonight's session: started at {data.get('start_time')}, "
            f"duration {duration_min} minutes, "
            f"phone pickups {data.get('pickup_count', 0)}, "
            f"alarm set for {data.get('alarm_time', 'not set')}.\n\n"
            f"Recent session history (newest first): {last_sessions}"
        )
        llm_client = get_llm_client()
        patterns = get_llm_response(llm_client, prompt)
        print(f"\n  [UNWIND INSIGHTS]\n{patterns}\n")


if __name__ == "__main__":
    # Database Connection, thread-safe for allowing MQTT patterns to access database
    print("Creating database connection.")
    database_conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)

    # In production, we should create database once and persist the data
    init_db(database_conn)

    # Pass connection via userdata
    subscriber = mqtt.Client(userdata={"conn": database_conn})
    subscriber.on_connect = on_connect
    subscriber.on_message = on_message
    # Connect to public broker
    print("Connecting to broker...")
    subscriber.connect("localhost", 1883, 60)

    # Start the subscriber loop
    subscriber.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping subscriber...")
        subscriber.loop_stop()
        subscriber.disconnect()
        database_conn.close()