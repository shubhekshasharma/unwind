import asyncio
from datetime import datetime

base_commands = ["start_unwind", "stop_unwind", "pickup", "dock", "exit"]


async def send_command(command):
    reader, writer = await asyncio.open_connection("127.0.0.1", 8888)
    writer.write(command.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


def validate_input(raw: str):
    """
    Validate and normalize a device command.
    Returns the command string to send, or None if invalid (and prints the error).
    """
    parts = raw.strip().split(None, 1)
    if not parts:
        return None

    base = parts[0].lower()

    if base not in base_commands:
        print(f"Invalid command '{base}'. Valid commands: {', '.join(base_commands)}")
        return None

    return base


async def main():
    print("Unwind device interface")
    print("Commands: start_unwind | stop_unwind | pickup | dock | exit")
    try:
        while True:
            raw = input("\n> ")
            command = validate_input(raw)
            if command is None:
                continue
            await send_command(command)
            if command == "exit":
                break
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting commands interface!")
        asyncio.get_running_loop().stop()


asyncio.run(main())