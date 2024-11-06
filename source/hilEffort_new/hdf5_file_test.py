import multiprocessing as mp
import time
import h5py
import numpy as np

NUM_CHANNELS = 4000
NUM_CHANNELS = 8000
SAMPLE_RATE = 500  # 1 kHz
BATCH_SIZE = 1000  # Number of samples to accumulate before writing to disk

def data_generator(queue, stop_event):
    prevT = 0
    queue_time = 2.626e+5
    while not stop_event.is_set():
        if (time.perf_counter()-prevT)>=1/SAMPLE_RATE:
            delta = time.perf_counter() - prevT
            prevT = time.perf_counter()
            start_time = time.time()
            data = np.random.random(NUM_CHANNELS).astype('float32')    # Generate random data for 4000 channels
            timestamp = time.time()
            sample_time = timestamp - start_time
            
            sample_rate = 1.0 / delta if delta != 0 else 0
            queue_start_time = time.perf_counter_ns()
            queue.put((timestamp, data, sample_time, delta, sample_rate,queue_time))
            queue_end_time = time.perf_counter_ns()
            queue_time = queue_end_time - queue_start_time
            
            # Ensure 1ms interval
            
def data_saver(queue, stop_event, filename):
    with h5py.File(filename, 'w') as f:
        time_dset = f.create_dataset('time', (0,), maxshape=(None,), dtype='float32', chunks=(BATCH_SIZE,))
        data_dset = f.create_dataset('data', (0, NUM_CHANNELS), maxshape=(None, NUM_CHANNELS), dtype='float32', chunks=(BATCH_SIZE, NUM_CHANNELS))
        sample_time_dset = f.create_dataset('sample_time', (0,), maxshape=(None,), dtype='float32', chunks=(BATCH_SIZE,))
        delta_dset = f.create_dataset('delta', (0,), maxshape=(None,), dtype='float32', chunks=(BATCH_SIZE,))
        sample_rate_dset = f.create_dataset('sample_rate', (0,), maxshape=(None,), dtype='float32', chunks=(BATCH_SIZE,))
        queue_time_dset = f.create_dataset('queue_time', (0,), maxshape=(None,), dtype='float32', chunks=(BATCH_SIZE,))
        
        # Add column names as attributes
        for i in range(NUM_CHANNELS):
            data_dset.attrs[f'channel_{i}'] = f'Channel {i}'
        
        buffer = []
        while not stop_event.is_set() or not queue.empty():
            while not queue.empty():
                buffer.append(queue.get())
            if len(buffer) >= BATCH_SIZE:
                new_data = np.array(buffer, dtype=object)
                time_dset.resize(time_dset.shape[0] + new_data.shape[0], axis=0)
                data_dset.resize(data_dset.shape[0] + new_data.shape[0], axis=0)
                sample_time_dset.resize(sample_time_dset.shape[0] + new_data.shape[0], axis=0)
                delta_dset.resize(delta_dset.shape[0] + new_data.shape[0], axis=0)
                sample_rate_dset.resize(sample_rate_dset.shape[0] + new_data.shape[0], axis=0)
                queue_time_dset.resize(queue_time_dset.shape[0] + new_data.shape[0], axis=0)
                
                time_dset[-new_data.shape[0]:] = np.array(new_data[:, 0], dtype='float32')
                data_dset[-new_data.shape[0]:] = np.vstack(new_data[:, 1]).astype('float32')
                sample_time_dset[-new_data.shape[0]:] = np.array(new_data[:, 2], dtype='float32')
                delta_dset[-new_data.shape[0]:] = np.array(new_data[:, 3], dtype='float32')
                sample_rate_dset[-new_data.shape[0]:] = np.array(new_data[:, 4], dtype='float32')
                queue_time_dset[-new_data.shape[0]:] = np.array(new_data[:, 5], dtype='float32')
                
                # Flush the data to disk
                f.flush()
                
                buffer = []


if __name__ == '__main__':
    queue = mp.Queue(maxsize=10000)  # Larger buffer size
    stop_event = mp.Event()
    filename = 'data.h5'

    generator_process = mp.Process(target=data_generator, args=(queue, stop_event))
    saver_process = mp.Process(target=data_saver, args=(queue, stop_event, filename))

    generator_process.start()
    saver_process.start()

    try:
        time.sleep(20)  # Run for 10 seconds
    except KeyboardInterrupt:
        pass

    stop_event.set()
    generator_process.join()
    saver_process.join()