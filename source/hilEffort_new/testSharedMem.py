# import can_bus_manager_multiP as can_mgr
import yaml
import dbc_processor as dp
import multiprocessing
import time
import random
import asyncio
import logging
import platform
import keyboard
import random
import utilityScipts
from logging_hdf5 import h5pyWriter
from utilityScipts import channelDictTemplate


def main(mpSharedMem):
    # manager = multiprocessing.Manager()
    # mpSharedMem = manager.dict()
    mpSharedMem['CAN'] = manager.dict()
    mpSharedMem['systemChannel'] = manager.dict()
    mpSharedMem['systemChannel']['systemTime']=manager.dict(channelDictTemplate())
    
    shm_gen= dp.can_dict(r'C:\Users\Public\Documents\gitRepoExternal\pyHIL\supportFiles\config_testDB.yml',mpSharedMem['CAN'],manager)
    shm_gen.create_can_shm_template()
    print(mpSharedMem)

def injectData(mpSharedMem,stop_event,mpLock):
    while not stop_event.is_set():
        mpSharedMem['systemChannel']['systemTime']['value'] = time.perf_counter()
        # mpLock.acquire()
        for key in mpSharedMem['CAN'].keys():
            mpSharedMem['CAN'][key]['value']=(random.randint(1,127))
            pass
        # mpLock.release()
        # print(mpSharedMem['CAN'][key]['value'])
        time.sleep(.0001)
        print('update loop:',time.perf_counter())


if __name__== '__main__':
    # asyncio.run(main())
    manager = multiprocessing.Manager()
    mpSharedMem = manager.dict()
    stop_event = multiprocessing.Event()
    mpLock = manager.Lock()
    main(mpSharedMem)


    hdf5Writer = h5pyWriter('myhdf5.hdf5',mpSharedMem,stop_event,mpLock)
    inject_process = multiprocessing.Process(target=injectData, args=(mpSharedMem,stop_event,mpLock))
    hdf5_process = multiprocessing.Process(target=hdf5Writer.read_and_write_to_hdf5, args=())

    inject_process.start()
    hdf5_process.start()

    while True:
    # print_unknown_structure(shared_dict)
        if keyboard.is_pressed('x'):
            print("Key 'x' pressed. Stopping the test.")
            stop_event.set()
            break
        time.sleep(0.01)  
    
    inject_process.join()
    hdf5_process.join()
