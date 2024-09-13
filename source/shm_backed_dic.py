import multiprocessing
import pickle
import time
from multiprocessing import shared_memory, Lock

def create_shared_dict(initial_dict, shm_name):
    pickled_dict = pickle.dumps(initial_dict)
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=len(pickled_dict))
    shm.buf[:len(pickled_dict)] = pickled_dict
    shm.close()

def worker_shared_memory(shm_name, lock, key, value):
    shm = shared_memory.SharedMemory(name=shm_name)
    with lock:
        pickled_dict = bytes(shm.buf[:shm.size])
        shared_dict = pickle.loads(pickled_dict)
        shared_dict[key] = value
        pickled_dict = pickle.dumps(shared_dict)
        shm.buf[:len(pickled_dict)] = pickled_dict
    shm.close()

def test_shared_memory():
    initial_dict = {}
    shm_name = 'shared_dict'
    lock = Lock()
    create_shared_dict(initial_dict, shm_name)

    processes = []
    start_time = time.time()
    for i in range(1000):
        p = multiprocessing.Process(target=worker_shared_memory, args=(shm_name, lock, f'key{i}', f'value{i}'))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
    end_time = time.time()
    print("Shared Memory Time:", end_time - start_time)

    shm = shared_memory.SharedMemory(name=shm_name)
    shm.close()
    shm.unlink()

if __name__ == "__main__":
    test_shared_memory()
