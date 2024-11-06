import numpy as np
from multiprocessing import shared_memory, Lock, Semaphore
import queue

class SharedMemoryQueue:
    def __init__(self, maxsize, shape, dtype=np.float64):
        self.maxsize = maxsize
        self.shape = shape
        self.dtype = dtype
        
        # Calculate the size of the shared memory
        item_size = np.prod(shape) * np.dtype(dtype).itemsize
        self.buffer_size = item_size * maxsize
        
        # Create shared memory
        self.shm = shared_memory.SharedMemory(create=True, size=self.buffer_size)
        
        # Create NumPy array using the shared memory buffer
        self.buffer = np.ndarray((maxsize,) + shape, dtype=dtype, buffer=self.shm.buf)
        
        # Synchronization primitives
        self.lock = Lock()
        self.empty_slots = Semaphore(maxsize)
        self.filled_slots = Semaphore(0)
        
        # Pointers for queue operations
        self.put_index = 0
        self.get_index = 0
        self.is_end = False

    def put(self, item):
        if item is None:
            self.is_end = True
            return
        self.empty_slots.acquire()
        with self.lock:
            np.copyto(self.buffer[self.put_index], item)
            self.put_index = (self.put_index + 1) % self.maxsize
        self.filled_slots.release()

    def get(self):
        self.filled_slots.acquire()
        with self.lock:
            item = self.buffer[self.get_index].copy()
            self.get_index = (self.get_index + 1) % self.maxsize
        self.empty_slots.release()
        return item

    def close(self):
        self.shm.close()
        self.shm.unlink()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    
    def get_nowait(self):
        if self.is_end:
            raise queue.Empty
        try:
            # Try to acquire without blocking
            if not self.filled_slots.acquire(False):
                raise queue.Empty
            with self.lock:
                item = self.buffer[self.get_index].copy()
                self.get_index = (self.get_index + 1) % self.maxsize
            self.empty_slots.release()
            return item
        except ValueError:  # For Python versions where acquire() doesn't accept 'blocking'
            if self.filled_slots.acquire(0):
                with self.lock:
                    item = self.buffer[self.get_index].copy()
                    self.get_index = (self.get_index + 1) % self.maxsize
                self.empty_slots.release()
                return item
            else:
                raise queue.Empty

