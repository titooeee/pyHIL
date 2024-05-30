import yaml
import can
import time
import random
import multiprocessing
import multiprocessing.process
import numpy as np
from multiprocessing import shared_memory
import keyboard
import dbc_processor as dp



# a = np.array([(random.randint(1,127)) for x in range(5)],dtype=np.int8) 
# shm = shared_memory.SharedMemory(name ="shm_can", create = True, size=a.nbytes)
# mem_ref = np.ndarray(a.shape, dtype=a.dtype, buffer=shm.buf)

def can_read(mem_ref,stop_event,bus1):

    messages = []
    rate = []
    encode_dic = {}
    for msg in bus1.dbc_dic.keys():
        encode_dic[msg] = {}    
        for sig in bus1.dbc_dic[msg].keys():
            encode_dic[msg][sig] = mem_ref[bus1.dbc_dic[msg][sig]]

        example_message = bus1.get_message_by_name('ControlCmd')
        data = example_message.encode(encode_dic[msg],strict = True)
        messages.append(can.Message(arbitration_id=example_message.frame_id, data=data))
        rate.append(example_message.cycle_time)


    with open('/home/mtitoo/pyHIL/config_testDB.yml','r') as file:
        dynoCOnfig = yaml.safe_load(file)


    dict_temp = dynoCOnfig['CANBUS']
    buses = []
    task = []
    for key in dict_temp:
        with can.Bus(interface=key['Interface'], channel=key['Channel'], bitrate=key['BAUD']) as BUS:
            buses.append(BUS)

    for canbus in buses:
        for idx in range(len(messages)):
            t = canbus.send_periodic(messages[idx], rate[idx]/1000)
            assert isinstance(t, can.CyclicSendTaskABC)
            task.append(t)
            
    while not stop_event.is_set():
        time.sleep(0.001)
        for can_task in task:
            messages = []
            encode_dic = {}
            for msg in bus1.dbc_dic.keys():
                encode_dic[msg] = {}    
                for sig in bus1.dbc_dic[msg].keys():
                    encode_dic[msg][sig] = mem_ref[bus1.dbc_dic[msg][sig]]

                example_message = bus1.get_message_by_name('ControlCmd')
                data = example_message.encode(encode_dic[msg],strict = True)
                messages.append(can.Message(arbitration_id=example_message.frame_id, data=data))
            can_task.modify_data(messages)

    for can_task in task:
        can_task.stop()
        print(f"{can_task} stopped cyclic send")

def mod_shared_mem(mem_ref,stop_event):
    while not stop_event.is_set():
        time.sleep(0.001)
        for i in range(len(mem_ref)):
            mem_ref[i] = np.float64(random.randint(0,3))


if __name__== '__main__':
    lst_msg = ["ControlCmd"]
    bus1 = dp.dbc_processor("/home/mtitoo/pyHIL/open_actuator.dbc",lst_msg,lst_msg)
    bus1.parse()
    shm_1 = dp.create_shared_mem('vcan0',bus1.lenght+1)

    try:
        stop_event = multiprocessing.Event()
        p1 = multiprocessing.Process(target=can_read, args=(shm_1.array,stop_event,bus1))
        p2 = multiprocessing.Process(target=mod_shared_mem,args=(shm_1.array,stop_event))

        p1.start()
        p2.start()
        
        time.sleep(10)
        stop_event.set()

        p1.join()
        p2.join()
        shm_1.close()
        shm_1.unlink()

    except Exception as e:
        p1.join()
        p2.join()
        shm_1.shm.close()
        shm_1.shm.unlink()

    
    
            
    