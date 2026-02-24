# subscriber.py
import paho.mqtt.client as mqtt
import time
from llm import get_llm_response, get_llm_client
import sqlite3
from datetime import datetime
import json

START_TOPIC = "device/events/unwind_start"
STOP_TOPIC = "device/events/unwind_stop"
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
            created_at TEXT
        )
    """)
    conn.commit()


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
    is_phone_down = True # because we always put phone down to start session
    status = "completed"
    created_at = data.get("date")  # use message-provided date

    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions (message_id, user_id, event_type, session_started_at, is_phone_down, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (message_id, user_id, event_type, session_started_at, is_phone_down, status, created_at))
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
        # Subscribe to topics
        client.subscribe(START_TOPIC)
        client.subscribe(STOP_TOPIC)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

    conn = userdata["conn"]

    if msg.topic == START_TOPIC:
        print(f"Session started at {msg.payload.decode()}")
        start_prompt = f"New unwind session started with data: {msg.payload.decode()}"
        print(f"LLM Prompt for session start: {start_prompt}")
        llm_client = get_llm_client()
        llm_response = get_llm_response(llm_client, start_prompt)
        print(f"LLM Response to session start: {llm_response}")

    elif msg.topic == STOP_TOPIC:
        # LLM Client Create
        # Insert directly from message payload
        insert_session_data(conn, msg.payload)
        # Query last 3 sessions for LLM
        last_sessions = query_last_sessions(conn, 3)
        prompt = f"Analyze the following session data for patterns: {last_sessions}"
        print(prompt)
        llm_client = get_llm_client()
        patterns = get_llm_response(llm_client, prompt)
        print(f"LLM Identified Patterns: {patterns}")


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