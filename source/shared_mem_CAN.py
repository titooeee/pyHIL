import yaml
import can
import time
import random
import multiprocessing
import multiprocessing.process
import numpy as np
from multiprocessing import shared_memory
import keyboard



a = np.array([(random.randint(1,127)) for x in range(5)],dtype=np.int8) 
shm = shared_memory.SharedMemory(name ="shm_can", create = True, size=a.nbytes)
mem_ref = np.ndarray(a.shape, dtype=a.dtype, buffer=shm.buf)

def can_read(shm,mem_ref,stop_event):
    messages = []
    messages.append(
        can.Message(
            arbitration_id=0x401,
            data =mem_ref[:],
            is_extended_id=False,
        )
    )

    # **********************************************************************************************#

    with open('/home/mtitoo/pyHIL/config.yml','r') as file:
        dynoCOnfig = yaml.safe_load(file)


    dict_temp = dynoCOnfig['CANBUS']
    buses = []
    task = []
    for key in dict_temp:
        with can.Bus(interface=key['Interface'], channel=key['Channel'], bitrate=key['BAUD']) as BUS:
            buses.append(BUS)

    for canbus in buses:
        t = canbus.send_periodic(messages, 0.005)
        assert isinstance(t, can.CyclicSendTaskABC)
        task.append(t)
            
    while not stop_event.is_set():
        time.sleep(0.0001)
        for can_task in task:
            message_even = [can.Message(
                arbitration_id=0x401,
                data=mem_ref[:],
                is_extended_id=False,
            )]
            can_task.modify_data(message_even)

    for can_task in task:
        can_task.stop()
        print(f"{can_task} stopped cyclic send")

def mod_shared_mem(shm,mem_ref,stop_event):
    while not stop_event.is_set():
        time.sleep(0.001)
        for i in range(len(mem_ref)):
            mem_ref[i] = np.int8(random.randint(1,127))


if __name__== '__main__':
    stop_event = multiprocessing.Event()
    p1 = multiprocessing.Process(target=can_read, args=(shm,mem_ref,stop_event))
    p2 = multiprocessing.Process(target=mod_shared_mem,args=(shm,mem_ref,stop_event))

    p1.start()
    p2.start()
    
    time.sleep(10)
    stop_event.set()
    
    p1.join()
    p2.join()
    shm.close()
    shm.unlink()
            
    