import time
import asyncio

unwind_commands = ["start_unwind", "stop_unwind", "exit"]
timer = None
timer_task = None
is_timer_running = False

async def print_timer():
    global timer
    global is_timer_running
    while True:
        if is_timer_running:
            elapsed_time = time.time() - timer
            print(f"Current unwind timer: {elapsed_time:.2f} seconds")
        else:
            pass
        await asyncio.sleep(2)

async def handle_timer():
    global timer
    global timer_task
    global is_timer_running
    loop = asyncio.get_running_loop()
    timer_task = asyncio.create_task(print_timer())
    data = await reader.read()
    try:
        while True:
            input_command = await loop.run_in_executor(None, input, "Enter command (start_unwind/stop_unwind/exit): ")
            if input_command not in unwind_commands:
                print("Invalid command. Please enter 'start_unwind', 'stop_unwind', or 'exit'. Try again.")
                continue
            if input_command == "exit":
                timer_task.cancel()
                break
            elif input_command == "start_unwind":
                if is_timer_running:
                    continue
                print("Starting unwind timer...")
                timer = time.time()
                is_timer_running = True
            elif input_command == "stop_unwind":
                if not is_timer_running:
                    continue
                is_timer_running = False
                print("Unwind timer stopped.")
            await asyncio.sleep(5)


    except KeyboardInterrupt:
        print("Stopping publisher...")

if __name__ == "__main__":
    asyncio.run(main())