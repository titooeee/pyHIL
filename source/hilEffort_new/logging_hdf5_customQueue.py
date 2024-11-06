import h5py
import multiprocessing.process
import time
import os
import copy
from multiprocessing import shared_memory
import numpy as np
import threading
from line_profiler import LineProfiler
# from multiprocessing import shared_memory, Queue
from SharedMemoryQueue import SharedMemoryQueue
from queue import Empty





class h5pyWriter(multiprocessing.Process):
    def __init__(self,hdf5FilePath,mpSharedMemName,mpSharedMemShape,stop_event,mpLock,mapDict):
        self.hdf5FilePath = hdf5FilePath
        self.stop_event = stop_event
        self.mpLock = mpLock
        self.mapDict = mapDict
        self.mpSharedMemName = mpSharedMemName
        self.mpSharedMemShape = mpSharedMemShape
        self.thread_stop_event = threading.Event()
        # self.data_queue = Queue(maxsize=20)
        
        self.logHz = 200
        self.dataBufSize = self.logHz*3
        # Create shared memory queue
        queue_shape = (len(self.mapDict.keys()), self.dataBufSize)
        self.data_queue = SharedMemoryQueue(maxsize=100, shape=queue_shape)
        
    # def lineProf (self):
    #     lp = LineProfiler()
    #     lp.add_function(self.write_to_hdf)
    #     lp.run('self.startThread()')
    #     lp.print_stats()


    def startThread(self):
        writer_process = multiprocessing.Process(target=self.write_to_hdf, args=(self.data_queue, self.hdf5FilePath, self.mapDict,self.dataBufSize))
        writer_process.start()

        readData = threading.Thread(target=self.readData, daemon=False)
        readData.start()  # Start the writer thread

        while not self.stop_event.is_set():
            time.sleep(0.01)

        self.thread_stop_event.set()
        readData.join()
        writer_process.join()




    @staticmethod
    def write_to_hdf(data_queue,hdf5FilePath, mapDict,dataBufSize):
        # os.nice(-10)
        os.sched_setaffinity(0, {6})
        os.sched_setscheduler(0, os.SCHED_RR, os.sched_param(30))

        num_channels = len(mapDict.keys())
        print('>>>>>>>>>>>>>Write thread Started')
        if os.path.exists(hdf5FilePath):
            os.remove(hdf5FilePath)
        with h5py.File(hdf5FilePath, 'a') as hdf:
            for key in mapDict.keys():
                hdf.create_dataset(key, (0,), maxshape=(None,), dtype='f')
            # dataset = hdf.create_dataset('data', (0, num_channels), maxshape=(None, num_channels))
            # dataset.attrs['channel_names'] = np.array(self.mapDict.keys(), dtype='S') 
            while True:
                try:
                    values = data_queue.get_nowait()

                    if values is None:  # End signal
                        print("Received end signal, exiting writer loop")
                        break

                    # Process the data
                    for idx, key in enumerate(mapDict.keys()):
                        dataset = hdf[key]
                        dataset.resize((dataset.shape[0] + dataBufSize,))
                        dataset[-dataBufSize:] = values[idx, :]
                    hdf.flush()

                except Empty:
                    if data_queue.is_end:
                        print("Received end signal, exiting writer loop")
                        break

                    # Queue is empty, continue to next iteration
                    continue

        print("Writer process finished")
            
           
            
            
            # while True:
            #     try:
            #         values = data_queue.get(block=False)  # Wait for data from the queue
            #         # values = None
            #         # time.sleep(0.01)
                    
            #     except  multiprocessing.queues.Empty:
            #         time.sleep(0.01)
            #         continue
                
            #     print('self.data_queue>>',data_queue.qsize())
            #     if values is None:  # Check for the sentinel value to stop
            #         print('>>>>>>>>>>>>>Done Here in write')
            #         break
            # # print('>>>>>>>>>>>>>Write thread Closed')
            #     # Write the values to HDF5
            #     for idx, key in enumerate(mapDict.keys()):
            #         dataset = hdf[key]
            #         dataset.resize((dataset.shape[0] + dataBufSize,))
            #         dataset[-dataBufSize:] = values[idx,:]
            #         # dataset[dataset.shape[0]:dataset.shape[0] + self.dataBufSize] = values[idx,:]
            #     # dataset.resize((dataset.shape[0] + self.dataBufSize, num_channels))
            #     # dataset[-self.dataBufSize:] = values    
            #     hdf.flush()  # Flush changes to the HDF5 file
            #     time.sleep(0.001)
    

    def readData(self):
        total_put_time = 0
        put_count = 0
        # os.nice(-10)
        os.sched_setaffinity(0, {5})
        os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(99))
        shm = shared_memory.SharedMemory(name=self.mpSharedMemName)
        
        mpSharedMem = np.ndarray(self.mpSharedMemShape, dtype='float64', buffer=shm.buf)

       
            # hdf.create_dataset('systemChannel/systemTime', (0,), maxshape=(None,), dtype='f')
            # values = {f'{key}': [] for key in self.mapDict.keys()}
        values = np.empty((len(self.mapDict.keys()),self.dataBufSize))
        # values['systemChannel/systemTime']=[]
        buffCounter = 0
        lateCounter = 0

        indices = [self.mapDict[key]['index'] for key in self.mapDict.keys()]
        prevT = time.perf_counter_ns()
        print('startTime', prevT)
        while not self.thread_stop_event.is_set():
            # print(mpSharedMem[0])
            deltaT =  time.perf_counter_ns()-prevT
            if deltaT >= (1e9/self.logHz):
                # print('>>>>>>>',1/(time.perf_counter()-prevT),totalCounter)
                if 1/(deltaT) < (self.logHz-5):
                    lateCounter+=1
                prevT = time.perf_counter_ns()
                self.mpLock.acquire() 
                values[:,buffCounter] = mpSharedMem 
                values[1,buffCounter] = 1e9/(deltaT)
                self.mpLock.release()
                buffCounter+=1

                # if buffCounter==self.dataBufSize:
                    # print('>>>>>>>>>>Filling wrote buffer Here')
                    # self.data_queue.put(values.copy())
                    # print(values['systemChannel/systemTime'])
                    # for idx, key in enumerate(self.mapDict.keys()):
                    #     dataset = hdf[key]
                    #     dataset.resize((dataset.shape[0] + buffCounter,))
                    #     dataset[-buffCounter:] = values[idx,:]
                    #     # values[key].clear()
                    # values[key].clear()
                    # buffCounter = 0
                    # hdf.flush()


                if buffCounter == self.dataBufSize:
                    start_put = time.perf_counter_ns()
                    self.data_queue.put(values)
                    end_put = time.perf_counter_ns()
                    
                    put_time = end_put - start_put
                    total_put_time += put_time
                    put_count += 1
                    
                    if put_count % 2 == 0:  # Log every 100 puts
                        avg_put_time = total_put_time / put_count
                        print(f"Average queue.put() time: {avg_put_time/1e6:.3f} ms")
                    
                    buffCounter = 0
            
            time.sleep(0.00001)
            # os.sched_yield()
        self.data_queue.put(values)
        print("lateCounter>>>>>>>",lateCounter)
        self.data_queue.put(None)
  