import multiprocessing
import time

def worker(shared_dict, key, lock):
    for i in range(5):
        with lock:
            # Increment the counter for the given key in the shared dictionary
            if key in shared_dict:
                shared_dict[key] += 1
            else:
                shared_dict[key] = 1
            print(f"Process {multiprocessing.current_process().name} updated {key} to {shared_dict[key]}")
        time.sleep(1)

def main():
    # Create a manager object to manage shared data
    manager = multiprocessing.Manager()
    
    # Create a shared dictionary
    shared_dict = manager.dict()
    
    # Create a lock for synchronization
    lock = manager.Lock()
    
    # Create a list to hold the processes
    processes = []

    # Create and start 5 processes
    for i in range(5):
        process_name = f'Process-{i}'
        p = multiprocessing.Process(target=worker, args=(shared_dict, process_name, lock))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()

    # Display the final value of the shared dictionary
    print("Final shared dictionary:")
    for key, value in shared_dict.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
