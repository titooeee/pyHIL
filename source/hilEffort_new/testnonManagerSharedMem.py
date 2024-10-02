# import can_bus_manager_multiP as can_mgr
import yaml
import dbc_processor as dp
import multiprocessing
from multiprocessing import shared_memory
import time
import random
import asyncio
import logging
import platform
import keyboard
import random
import utilityScipts
from logging_hdf5_nonManagerShared import h5pyWriter
from utilityScipts import channelDictTemplate
import numpy as np


def main():
    
    mapDict = dict()
    mapDict['systemChannel/systemTime']=dict(channelDictTemplate())
    mapDict['systemChannel/systemTime']['index']=0
    
    shm_gen= dp.can_dict(r'C:\Users\Public\Documents\gitRepoExternal\pyHIL\supportFiles\config_testDB.yml',manager)
    startIndex = 1
    tempDict = shm_gen.updateDict(startIndex)
    mapDict = mapDict| tempDict

    print('>>>>>>>>>>>>>>>>>>:',len(mapDict))
    return mapDict
    

def injectData(mpSharedMemName,mpSharedMemShape,stop_event,mpLock,mapDict):
    shm = shared_memory.SharedMemory(name=mpSharedMemName)
    mpSharedMem = np.ndarray(mpSharedMemShape, dtype='float64', buffer=shm.buf)
    print('in_update:',shm,shm.buf)

    prevT = time.perf_counter()
    while not stop_event.is_set():
        deltaT =  time.perf_counter()-prevT
        if (deltaT) > 0.005:
            prevT = time.perf_counter()
            mpLock.acquire()
            for key in mapDict.keys():
                mpSharedMem[mapDict[key]['index']] = (random.randint(1,127))
            mpSharedMem[mapDict['systemChannel/systemTime']['index']] = 1/(deltaT)
            mpLock.release()
            # print('Update Loop Rate:',1/(time.perf_counter()-prevT))
        # time.sleep(0.01)



if __name__== '__main__':
    # asyncio.run(main())
    manager = multiprocessing.Manager()
    stop_event = multiprocessing.Event()
    mpLock = manager.Lock()
    mapDict = main()

    shm = shared_memory.SharedMemory(create=True, size=len(mapDict) * np.dtype('float64').itemsize)
    
    mpSharedMem = np.ndarray((len(mapDict),), dtype='float64', buffer=shm.buf)
    print('in_main:',shm,shm.buf)




    hdf5Writer = h5pyWriter('myhdf5.hdf5',shm.name,mpSharedMem.shape,stop_event,mpLock,mapDict)
    inject_process = multiprocessing.Process(target=injectData, args=(shm.name,mpSharedMem.shape,stop_event,mpLock,mapDict))
    hdf5_process = multiprocessing.Process(target=hdf5Writer.read_and_write_to_hdf5, args=())

    inject_process.start()
    hdf5_process.start()

    while True:
    # print_unknown_structure(shared_dict)
        if keyboard.is_pressed('x'):
            print("Key 'x' pressed. Stopping the test.")
            stop_event.set()
            break
        
        time.sleep(0.1)  
    
    inject_process.join()
    hdf5_process.join()
    shm.close()
    shm.unlink()