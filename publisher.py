import time
import asyncio
from datetime import datetime
import json
import paho.mqtt.client as mqtt

unwind_commands = ["start_unwind", "stop_unwind"]

timer_start = None
is_timer_running = False

DEVICE_ID = "device1"
START_TOPIC = "device/events/unwind_start"
STOP_TOPIC = "device/events/unwind_stop"

def format_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%y%m%d%H%M%S")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Successfully connected to broker")
    else:
        print(f"Connection failed with code {rc}")

# Create publisher client
publisher = mqtt.Client()
publisher.on_connect = on_connect

# Connect to public broker
print("Connecting to broker...")

# (broker, port, keepalive)
publisher.connect("localhost", 1883, 60)
publisher.loop_start()


# Get current date
def current_date():
    return datetime.now().strftime("%Y-%m-%d")

async def print_timer():
    global timer_start, is_timer_running
    while True:
        if is_timer_running and timer_start is not None:
            elapsed_time = time.time() - timer_start
            print(f"Current unwind timer: {elapsed_time:.2f} seconds")
        await asyncio.sleep(1)

async def handle_timer(reader, writer):
    global timer_start, is_timer_running

    data = await reader.read(100)
    input_command = data.decode().strip().lower()

    if input_command not in unwind_commands:
        print("Invalid command. Please enter 'start_unwind', 'stop_unwind'. Try again.")

    if input_command == "start_unwind":
        if not is_timer_running:
            timer_start = time.time()
            is_timer_running = True
            print("Timer started...")
            start_message = {
                "date": current_date(),
                "start_time": format_time(timer_start),
                "command": "start_unwind",
                "device_id": DEVICE_ID
            }
            publisher.publish(
                START_TOPIC,
                json.dumps(start_message),
                qos=1
            )
            print(f"Published to {START_TOPIC}: {start_message}")


    elif input_command == "stop_unwind":
        if is_timer_running:
            stop_time = time.time()
            duration = stop_time - timer_start
            is_timer_running = False
            
            stop_message = {
                "date": current_date(),
                "start_time": format_time(timer_start),
                "stop_time": format_time(stop_time),
                "duration": duration,
                "command": "stop_unwind",
                "device_id": DEVICE_ID
            }
            publisher.publish(
                STOP_TOPIC,
                json.dumps(stop_message),
                qos=1
            )
            print(f"Published to {STOP_TOPIC}: {stop_message}")
            print("Timer stopped!")
            timer_start = None
        else:
            print("Timer not started yet to stop.")
            
    writer.close()


async def main():
    asyncio.create_task(print_timer())
    server = await asyncio.start_server(handle_timer, "127.0.0.1", 8888)
    print("Timer server running...")
    
    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting server...")
        asyncio.get_running_loop().stop()

if __name__ == "__main__":
    asyncio.run(main())