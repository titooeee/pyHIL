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
import gc
import os
from randomgen import ExtendedGenerator, PCG64

# from pynput.keyboard import Key, Controller



def main():
    
    mapDict = dict()
    mapDict['systemChannel/systemTime']=dict(channelDictTemplate())
    mapDict['systemChannel/systemTime']['index']=0
    mapDict['systemChannel/logRate']=dict(channelDictTemplate())
    mapDict['systemChannel/logRate']['index']=1


    if platform.system() == "Linux":
        shm_gen = dp.can_dict('/home/mtitoo/pyHIL/supportFiles/config_testDB.yml',manager)
    else:
        shm_gen= dp.can_dict(r'C:\Users\Public\Documents\gitRepoExternal\pyHIL\supportFiles\config_testDB.yml',manager)
    
    # shm_gen= dp.can_dict(r'C:\Users\Public\Documents\gitRepoExternal\pyHIL\supportFiles\config_testDB.yml',manager)
    startIndex = 1
    tempDict = shm_gen.updateDict(startIndex)
    mapDict.update(tempDict)

    print('>>>>>>>>>>>>>>>>>>:',len(mapDict))
    return mapDict
    

def injectData(mpSharedMemName,mpSharedMemShape,stop_event,mpLock,mapDict):
    # os.nice(-9)
    # os.sched_setaffinity(0, {4})
    os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(99))
    rng = ExtendedGenerator(PCG64())
    shm = shared_memory.SharedMemory(name=mpSharedMemName)
    mpSharedMem = np.ndarray(mpSharedMemShape, dtype='float64', buffer=shm.buf)
    print('in_update:',shm,shm.buf)

    prevT = time.perf_counter()
    prevTGC = time.perf_counter()
    lateCounter = 0
    totalCounter = 0
    updateHz = 500
    new_data = np.random.randn(len(mapDict.keys()))
    while not stop_event.is_set():
        deltaT =  time.perf_counter()-prevT
        deltaTGC = time.perf_counter() - prevTGC 
        if (deltaT) >= (1/updateHz):
            if 1/(deltaT) < (updateHz-5):
                lateCounter+=1
            prevT = time.perf_counter()
            # new_data = np.random.randn(len(mapDict.keys()))
            mpLock.acquire()

            # for key in mapDict.keys():
            #     # (random.randint(1,127))
            #     # pass
            #     mpSharedMem[mapDict[key]['index']] = 2
            mpSharedMem[:] = new_data
            mpSharedMem[mapDict['systemChannel/systemTime']['index']] = 1/(deltaT)
            totalCounter+=1
            mpLock.release()
    # time.sleep(0.0001)
    print('>>>>>>>>>>Late Counter', lateCounter,'totalCouter:',totalCounter)
            # print('Update Loop Rate:',1/(time.perf_counter()-prevT))

            
        # time.sleep(0.01)



if __name__== '__main__':
    
    # gc.disable()
    gc.enable()
    # os.nice(-10)
    
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
    hdf5_process = multiprocessing.Process(target=hdf5Writer.startThread, args=())
    
    hdf5_process.start()
    time.sleep(2)
    inject_process.start()
    

    # while True:
    # # print_unknown_structure(shared_dict)
    #     if keyboard.is_pressed('x'):
    #         print("Key 'x' pressed. Stopping the test.")
    #         stop_event.set()
    #         break
        
    time.sleep(10)  
    stop_event.set()
    
    inject_process.join()
    hdf5_process.join()
    shm.close()
    shm.unlink()