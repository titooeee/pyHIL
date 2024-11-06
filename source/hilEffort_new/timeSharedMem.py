import mmap
import multiprocessing
import numpy as np
import time
import ctypes

def write_to_mmap(offset, size, data, filename, lock):
    with lock:  # Lock to prevent race conditions
        with open(filename, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0)  # Memory-map the file
            mm.seek(offset)  # Move to the appropriate offset
            mm.write(data.tobytes())  # Write the data
            mm.close()  # Close the memory map

def init_mmap(filename, size):
    with open(filename, "wb") as f:
        f.write(b'\x00' * size)  # Initialize the file to the desired size

if __name__ == "__main__":
    filename = "shared_mem.dat"
    num_batches = 1000
    data_size = 6000 * 100 * num_batches * np.dtype(np.int64).itemsize  # Total memory size for 10 batches of 6000x100
    
    batch_size = 6000 * 100 * np.dtype(np.int64).itemsize  # Each batch size

    # Initialize the shared memory file
    init_mmap(filename, data_size)

    # Prepare the data (simulating 10 sets of 6000x100 arrays)
    data_list = [np.random.randint(0, 100, size=(6000 * 100), dtype=np.int64) for _ in range(num_batches)]

    # Create a lock to prevent concurrent access to the mmap
    lock = multiprocessing.Lock()

    # Start timing
    start_time = time.time()

    # Start multiprocessing to write data
    processes = []
    for i, data in enumerate(data_list):
        offset = i * batch_size
        p = multiprocessing.Process(target=write_to_mmap, args=(offset, batch_size, data, filename, lock))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()

    # End timing
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Output the time taken
    print(f"Time taken to write 10 batches of 6000x100 arrays using mmap and multiprocessing: {elapsed_time:.6f} seconds")

    # Clean up the mmap file
    import os
    os.remove(filename)
