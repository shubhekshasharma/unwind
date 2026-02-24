import asyncio

unwind_commands = ["start_unwind", "stop_unwind", "exit"]


async def send_command(command):
    reader, writer = await asyncio.open_connection("127.0.0.1", 8888)
    writer.write(command.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def main():
    try:
        while True:
            input_command = input("Enter command (start_unwind/stop_unwind/exit): ")

            if input_command not in unwind_commands:
                print("Invalid command. Please enter 'start_unwind', 'stop_unwind', or 'exit'. Try again.")

            input_command = input_command.strip().lower()
            await send_command(input_command)
            if input_command == "exit":
                break
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting commands inferface!")
        asyncio.get_running_loop().stop()
    

asyncio.run(main())