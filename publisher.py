import time
import asyncio
from datetime import datetime, timedelta
import json
import paho.mqtt.client as mqtt

unwind_commands = ["start_unwind", "stop_unwind", "pickup", "dock"]

timer_start = None
is_timer_running = False
# True while phone is off the dock
is_timer_paused = False
# timestamp when last paused
paused_at = None   
# accumulated seconds spent paused this session           
total_paused = 0.0       
# phone starts on the dock     
is_phone_docked = True     
# IDLE | PLAYING | PAUSED   
experience_state = "IDLE"    
# "HH:MM" string set at session start 
alarm_time = None  
# number of pickups in current session           
pickup_count = 0
# asyncio task for sleep countdown            
countdown_task = None         

DEVICE_ID = "device1"
START_TOPIC = "device/events/unwind_start"
STOP_TOPIC = "device/events/unwind_stop"
PICKUP_TOPIC = "device/events/phone_pickup"
DOCK_TOPIC = "device/events/phone_dock"

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

def print_state_banner(state: str, timestamp: str = ""):
    if state == "PLAYING":
        print("==========================================\n")
        print("  [UNWIND] STATE: PLAYING")
        print("  Ambient lights ON | Soundscape ACTIVE")
        if timestamp:
            print(f"  Phone docked at {timestamp}")
        print("="*50 + "\n")
    elif state == "PAUSED":
        print("==========================================\n")
        print("  [UNWIND] STATE: PAUSED")
        print("  Lights dimmed | Soundscape PAUSED")
        if timestamp:
            print(f"  Phone lifted at {timestamp}")
        print("  (Return phone to dock to resume)")
        print("-"*50 + "\n")
    elif state == "IDLE":
        print("==========================================\n")
        print("  [UNWIND] STATE: IDLE  (Session ended)")
        print("="*50 + "\n")


async def run_countdown(alarm_time_str: str):
    """Asyncio task, prints remaining sleep time every 10 seconds until cancelled."""
    try:
        while True:
            now = datetime.now()
            alarm_h, alarm_m = map(int, alarm_time_str.split(":"))
            alarm_dt = now.replace(hour=alarm_h, minute=alarm_m, second=0, microsecond=0)
            if alarm_dt <= now:
                alarm_dt += timedelta(days=1)
            delta = alarm_dt - now
            hours, minutes = divmod(int(delta.total_seconds() / 60), 60)
            print(f"  [SLEEP COUNTDOWN] {hours}h {minutes}m available  (alarm: {alarm_time_str})")
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass  # cancelled cleanly on stop_unwind


async def print_timer():
    global timer_start, is_timer_running, is_timer_paused, total_paused
    while True:
        if is_timer_running and timer_start is not None:
            if is_timer_paused:
                print("Timer paused")
            else:
                elapsed_time = time.time() - timer_start - total_paused
                print(f"Current unwind timer: {elapsed_time:.2f} seconds")
        await asyncio.sleep(1)

async def handle_timer(reader, writer):
    global timer_start, is_timer_running, is_timer_paused, paused_at, total_paused, is_phone_docked, experience_state, alarm_time, pickup_count, countdown_task

    data = await reader.read(100)
    raw_command = data.decode().strip()
    parts = raw_command.split(None, 1)
    input_command = parts[0].lower()
    command_arg = parts[1] if len(parts) > 1 else None

    if input_command not in unwind_commands:
        print("Invalid command. Please enter 'start_unwind HH:MM', 'stop_unwind', 'pickup', or 'dock'. Try again.")

    if input_command == "start_unwind":
        if not is_timer_running:
            timer_start = time.time()
            is_timer_running = True
            is_timer_paused = False
            paused_at = None
            total_paused = 0.0
            is_phone_docked = True
            experience_state = "PLAYING"
            alarm_time = command_arg  # e.g. "07:30"
            pickup_count = 0
            print_state_banner("PLAYING", format_time(timer_start))
            if alarm_time:
                countdown_task = asyncio.create_task(run_countdown(alarm_time))
            start_message = {
                "date": current_date(),
                "start_time": format_time(timer_start),
                "command": "start_unwind",
                "device_id": DEVICE_ID,
                "experience_state": experience_state,
                "alarm_time": alarm_time
            }
            publisher.publish(
                START_TOPIC,
                json.dumps(start_message),
                qos=1
            )
            print(f"Published to {START_TOPIC}: {start_message}")

    elif input_command == "pickup":
        if not is_timer_running:
            print("[DEVICE] No active session — start_unwind first.")
        elif not is_phone_docked:
            print("[DEVICE] Phone is already picked up.")
        else:
            is_phone_docked = False
            is_timer_paused = True
            paused_at = time.time()
            experience_state = "PAUSED"
            pickup_count += 1
            print_state_banner("PAUSED", format_time(paused_at))
            # countdown continues running during PAUSED
            pickup_message = {
                "date": current_date(),
                "timestamp": format_time(paused_at),
                "command": "pickup",
                "device_id": DEVICE_ID,
                "experience_state": experience_state,
                "pickup_count": pickup_count
            }
            publisher.publish(PICKUP_TOPIC, json.dumps(pickup_message), qos=1)
            print(f"Published to {PICKUP_TOPIC}: {pickup_message}")

    elif input_command == "dock":
        if not is_timer_running:
            print("[DEVICE] No active session — start_unwind first.")
        elif is_phone_docked:
            print("[DEVICE] Phone is already docked.")
        else:
            is_phone_docked = True
            is_timer_paused = False
            total_paused += time.time() - paused_at
            paused_at = None
            experience_state = "PLAYING"
            print_state_banner("PLAYING", format_time(time.time()))
            dock_message = {
                "date": current_date(),
                "timestamp": format_time(time.time()),
                "command": "dock",
                "device_id": DEVICE_ID,
                "experience_state": experience_state
            }
            publisher.publish(DOCK_TOPIC, json.dumps(dock_message), qos=1)
            print(f"Published to {DOCK_TOPIC}: {dock_message}")

    elif input_command == "stop_unwind":
        if is_timer_running:
            stop_time = time.time()
            # If stopped while paused, count the current pause segment too
            effective_paused = total_paused + (stop_time - paused_at if is_timer_paused and paused_at else 0)
            duration = stop_time - timer_start - effective_paused
            is_timer_running = False
            is_timer_paused = False
            paused_at = None
            total_paused = 0.0
            experience_state = "IDLE"
            if countdown_task and not countdown_task.done():
                countdown_task.cancel()
                countdown_task = None
            print_state_banner("IDLE")

            stop_message = {
                "date": current_date(),
                "start_time": format_time(timer_start),
                "stop_time": format_time(stop_time),
                "duration": duration,
                "command": "stop_unwind",
                "device_id": DEVICE_ID,
                "experience_state": experience_state,
                "alarm_time": alarm_time,
                "pickup_count": pickup_count
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