import h5py
import multiprocessing.process
import time
import os
import copy
from multiprocessing import shared_memory
import numpy as np


class h5pyWriter(multiprocessing.Process):
    def __init__(self,hdf5FilePath,mpSharedMemName,mpSharedMemShape,stop_event,mpLock,mapDict):
        self.hdf5FilePath = hdf5FilePath
        self.stop_event = stop_event
        self.mpLock = mpLock
        self.mapDict = mapDict
        self.mpSharedMemName = mpSharedMemName
        self.mpSharedMemShape = mpSharedMemShape

       
        # print('in_log:',self.shm,self.shm.buf)

    def read_and_write_to_hdf5(self):
        shm = shared_memory.SharedMemory(name=self.mpSharedMemName)
        
        mpSharedMem = np.ndarray(self.mpSharedMemShape, dtype='float64', buffer=shm.buf)

        if os.path.exists(self.hdf5FilePath):
            os.remove(self.hdf5FilePath)
        with h5py.File(self.hdf5FilePath, 'a') as hdf:
            for key in self.mapDict.keys():
                hdf.create_dataset(key, (0,), maxshape=(None,), dtype='f')
            # hdf.create_dataset('systemChannel/systemTime', (0,), maxshape=(None,), dtype='f')
            values = {f'{key}': [] for key in self.mapDict.keys()}
            # values['systemChannel/systemTime']=[]
            buffCounter = 0
            prevT = time.perf_counter()
            while not self.stop_event.is_set():
                # print(mpSharedMem[0])
                if (time.perf_counter()-prevT)>0.01:
                    prevT = time.perf_counter()
                    self.mpLock.acquire()
                    for key in self.mapDict.keys():
                        values[key].append(mpSharedMem[self.mapDict[key]['index']])
                    self.mpLock.release()
                    buffCounter+=1
                    
                    
                # batch write
                if buffCounter==100:
                    # print(values['systemChannel/systemTime'])
                    for key in values.keys():
                        dataset = hdf[key]
                        dataset.resize((dataset.shape[0] + len(values[key]),))
                        dataset[-len(values[key]):] = values[key]
                        values[key].clear()
                    buffCounter = 0
                    hdf.flush()
                # print(time.perf_counter())
                # time.sleep(0.01)  # Simulate cyclic reading every second
                # print('Log Loop Rate:',1/(time.perf_counter()-prevT))
                