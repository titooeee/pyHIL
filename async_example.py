import asyncio

class AsyncWorker:
    def __init__(self, stop_event):
        self.stop_event = stop_event

    async def do_work(self):
        while not self.stop_event.is_set():
            print("Working...")
            await asyncio.sleep(1)  # Simulate work with an async sleep
        print("Stopping work.")

async def main():
    # Create an event to signal stopping
    stop_event = asyncio.Event()

    # Create an instance of AsyncWorker
    worker = AsyncWorker(stop_event)

    # Start the worker task
    worker_task = asyncio.create_task(worker.do_work())

    # Run the worker for 5 seconds and then stop
    await asyncio.sleep(5)
    print("Signaling stop event...")
    stop_event.set()

    # Wait for the worker to stop
    await worker_task

if __name__ == "__main__":
    asyncio.run(main())
