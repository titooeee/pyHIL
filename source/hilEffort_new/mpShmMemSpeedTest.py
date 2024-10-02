import multiprocessing
import time
from utilityScipts import channelDictTemplate
import dbc_processor as dp
import random
def main(mpSharedMem):
    # manager = multiprocessing.Manager()
    # mpSharedMem = manager.dict()
    mpSharedMem['CAN'] = manager.dict()
    mpSharedMem['systemChannel'] = manager.dict()
    mpSharedMem['systemChannel']['systemTime']=manager.dict(channelDictTemplate())
    
    shm_gen= dp.can_dict(r'C:\Users\Public\Documents\gitRepoExternal\pyHIL\supportFiles\config_testDB.yml',mpSharedMem['CAN'],manager)
    shm_gen.create_can_shm_template()
    print(mpSharedMem)

def worker(shared_dict,lock):
    while True:
        # Access shared memory
        lock.acquire()
        for key in shared_dict['CAN'].keys():
            shared_dict['CAN'][key]['value']
        var = shared_dict['A']['B']['data']
        print(time.perf_counter())
        lock.release()
        time.sleep(0.001)  # 10 times per second

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    
    shared_dict = manager.dict()
    main(shared_dict)
    shared_dict['A']=manager.dict()
    shared_dict['A']['B'] = manager.dict({'data': 0})

    # Start worker process
    process = multiprocessing.Process(target=worker, args=(shared_dict,lock))
    process.start()

    # Simulate updating shared memory
    while (True):
        lock.acquire()
        shared_dict['A']['B']['data'] = 100
        lock.release()
        time.sleep(0.001)  # Control update frequency


        shared_dict['systemChannel']['systemTime']['value'] = time.perf_counter()
        # lock.acquire()
        for key in shared_dict['CAN'].keys():
            shared_dict['CAN'][key]['value']=(random.randint(1,127))
        #     pass
        # lock.release()
        # print(mpSharedMem['CAN'][key]['value'])
        # time.sleep(.0001)
        # print('update loop:',time.perf_counter())
