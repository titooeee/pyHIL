import h5py
import multiprocessing.process
import time
import os
import copy
from multiprocessing import shared_memory
import numpy as np
import threading
import queue
from line_profiler import LineProfiler




class h5pyWriter(multiprocessing.Process):
    def __init__(self,hdf5FilePath,mpSharedMemName,mpSharedMemShape,stop_event,mpLock,mapDict):
        self.hdf5FilePath = hdf5FilePath
        self.stop_event = stop_event
        self.mpLock = mpLock
        self.mapDict = mapDict
        self.mpSharedMemName = mpSharedMemName
        self.mpSharedMemShape = mpSharedMemShape
        self.thread_stop_event = threading.Event()
        self.data_queue = queue.Queue(maxsize=500)
        
        self.logHz = 500
        self.dataBufSize = self.logHz*3
        
    # def lineProf (self):
    #     lp = LineProfiler()
    #     lp.add_function(self.write_to_hdf)
    #     lp.run('self.startThread()')
    #     lp.print_stats()


    def startThread(self):
        self.writer_thread = threading.Thread(target=self.write_to_hdf, daemon=False)
        self.writer_thread.start()  # Start the writer thread

        self.readData = threading.Thread(target=self.readData, daemon=False)
        self.readData.start()  # Start the writer thread

        while not self.stop_event.is_set():
            time.sleep(0.01)

        self.thread_stop_event.set()
        self.readData.join()
        self.writer_thread.join()



        # print('in_log:',self.shm,self.shm.buf)
    def write_to_hdf(self):
        # os.nice(-10)
        # os.sched_setaffinity(0, {6})
        # os.sched_setscheduler(0, os.SCHED_RR, os.sched_param(30))

        num_channels = len(self.mapDict.keys())
        print('>>>>>>>>>>>>>Write thread Started')
        if os.path.exists(self.hdf5FilePath):
            os.remove(self.hdf5FilePath)
        with h5py.File(self.hdf5FilePath, 'a') as hdf:
            # for key in self.mapDict.keys():
            #     hdf.create_dataset(key, (0,), maxshape=(None,), dtype='f')
            dataset = hdf.create_dataset('data', (0, num_channels), maxshape=(None, num_channels))
            dataset.attrs['channel_names'] = np.array(self.mapDict.keys(), dtype='S') 
            while True:
                try:
                    values = self.data_queue.get(block=False)  # Wait for data from the queue
                except queue.Empty:
                    time.sleep(0.01)
                    continue
                
                print('self.data_queue>>',self.data_queue.qsize())
                if values is None:  # Check for the sentinel value to stop
                    print('>>>>>>>>>>>>>Done Here in write')
                    break
            # print('>>>>>>>>>>>>>Write thread Closed')
                # Write the values to HDF5
                # for idx, key in enumerate(self.mapDict.keys()):
                #     dataset = hdf[key]
                #     dataset.resize((dataset.shape[0] + self.dataBufSize,))
                #     dataset[-self.dataBufSize:] = values[idx,:]
                #     # dataset[dataset.shape[0]:dataset.shape[0] + self.dataBufSize] = values[idx,:]
                dataset.resize((dataset.shape[0] + self.dataBufSize, num_channels))
                dataset[-self.dataBufSize:] = values    
                hdf.flush()  # Flush changes to the HDF5 file
    

    def readData(self):
        # os.nice(-10)
        # os.sched_setaffinity(0, {5})
        os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(40))
        shm = shared_memory.SharedMemory(name=self.mpSharedMemName)
        
        mpSharedMem = np.ndarray(self.mpSharedMemShape, dtype='float64', buffer=shm.buf)

       
            # hdf.create_dataset('systemChannel/systemTime', (0,), maxshape=(None,), dtype='f')
            # values = {f'{key}': [] for key in self.mapDict.keys()}
        values = np.empty((len(self.mapDict.keys()),self.dataBufSize))
        # values['systemChannel/systemTime']=[]
        buffCounter = 0
        lateCounter = 0

        indices = [self.mapDict[key]['index'] for key in self.mapDict.keys()]
        prevT = time.perf_counter()
        print('startTime', prevT)
        while not self.thread_stop_event.is_set():
            # print(mpSharedMem[0])
            deltaT =  time.perf_counter()-prevT
            if deltaT >= (1/self.logHz):
                # print('>>>>>>>',1/(time.perf_counter()-prevT),totalCounter)
                if 1/(deltaT) < (self.logHz-5):
                    lateCounter+=1
                prevT = time.perf_counter()
                self.mpLock.acquire() 
                values[:,buffCounter] = mpSharedMem 
                values[1,buffCounter] = 1/(deltaT)
                self.mpLock.release()
                buffCounter+=1
            if buffCounter==self.dataBufSize:
                # print('>>>>>>>>>>Here')
                self.data_queue.put(values,block=False, timeout=1)
                # print(values['systemChannel/systemTime'])
                # for idx, key in enumerate(self.mapDict.keys()):
                #     dataset = hdf[key]
                #     dataset.resize((dataset.shape[0] + buffCounter,))
                #     dataset[-buffCounter:] = values[idx,:]
                #     # values[key].clear()
                buffCounter = 0
                # hdf.flush()
        
            # time.sleep(0.0001)
            # os.sched_yield()
        self.data_queue.put(values, timeout=1)
        print("lateCounter>>>>>>>",lateCounter)
        self.data_queue.put(None)
  