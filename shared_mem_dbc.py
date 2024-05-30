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
import logging

can.Logger("test.asc",)

# a = np.array([(random.randint(1,127)) for x in range(5)],dtype=np.int8) 
# shm = shared_memory.SharedMemory(name ="shm_can", create = True, size=a.nbytes)
# mem_ref = np.ndarray(a.shape, dtype=a.dtype, buffer=shm.buf)
# logging.basicConfig(filename='can_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# class MyCANListener(can.Listener):
#     def on_message_received(self, msg):
#         print(f"msg is --------------------------{msg}")
#         log_entry = f"RECEIVED - ID: {msg.arbitration_id}, DLC: {msg.dlc}, Data: {msg.data.hex()}"
#         logging.info(log_entry)


def can_read(mem_ref,stop_event,bus1):

    messages = []
    rate = []
    encode_dic = {}
    for msg in bus1.dbc_dic.keys():
        encode_dic[msg] = {}    
        for sig in bus1.dbc_dic[msg].keys():
            encode_dic[msg][sig] = mem_ref[bus1.dbc_dic[msg][sig]]

        example_message = bus1.get_message_by_name(msg)
        data = example_message.encode(encode_dic[msg],strict = True)
        messages.append(can.Message(arbitration_id=example_message.frame_id, data=data))
        rate.append(example_message.cycle_time)


    with open('/home/mtitoo/pyHIL/config_testDB.yml','r') as file:
        dynoCOnfig = yaml.safe_load(file)


    dict_temp = dynoCOnfig['CANBUS']
    buses = []
    task = []
    log_notifier_list = []
    for key in dict_temp:
        # BUS = can.interface.Bus(channel=key['Channel'], bustype =key['Interface'], bitrate=key['BAUD'] )
        BUS = can.Bus(interface=key['Interface'], channel=key['Channel'], bitrate=key['BAUD'])
        buses.append(BUS)
        # logger = can.Logger(str(key['Channel']+".mf4"))
        logger = can.SizedRotatingLogger(str(key['Channel']+".asc"),max_bytes=1024*1024*1)
        # logger = can.Logger("can_log_hereeee.mf4")
        
        # listener = MyCANListener()
        log_notifier_list.append(can.Notifier(BUS, [logger],timeout=2))


    for canbus in buses:
        for idx in range(len(messages)):
            t = canbus.send_periodic(messages[idx], rate[idx]/2000)
            assert isinstance(t, can.CyclicSendTaskABC)
            task.append(t)
            
    while not stop_event.is_set():
    # for i in range(100):
        time.sleep(0.001)
        
        messages = []
        encode_dic = {}
        for msg in bus1.dbc_dic.keys():
            encode_dic[msg] = {}    
            for sig in bus1.dbc_dic[msg].keys():
                encode_dic[msg][sig] = mem_ref[bus1.dbc_dic[msg][sig]]

            example_message = bus1.get_message_by_name(msg)
            data = example_message.encode(encode_dic[msg],strict = True)
            messages.append(can.Message(arbitration_id=example_message.frame_id, data=data))
        
        counter = 0
        for canbus in buses:
            for idx in range(len(messages)):
                task[counter].modify_data(messages[idx])
                counter+=1

    for can_task in task:
        can_task.stop()
        print(f"{can_task} stopped cyclic send")
    
    for notifier in log_notifier_list:
        notifier.stop()
    
    for canbus in buses:
        canbus.shutdown()


def mod_shared_mem(mem_ref,stop_event):
    while not stop_event.is_set():
        time.sleep(0.0001)
        for i in range(len(mem_ref)):
            mem_ref[i] = np.float64(random.randint(0,3))


if __name__== '__main__':
    lst_msg = ["ControlCmd","ControlStatus","LimitsCmd"]
    # lst_msg = ["ControlCmd"]
    bus1 = dp.dbc_processor("/home/mtitoo/pyHIL/open_actuator.dbc",lst_msg,lst_msg)
    bus1.parse()
    shm_1 = dp.create_shared_mem('vcan0',bus1.lenght+1)
    # stop_event = multiprocessing.Event()

    try:
        stop_event = multiprocessing.Event()
        p1 = multiprocessing.Process(target=can_read, args=(shm_1.array,stop_event,bus1))
        p2 = multiprocessing.Process(target=mod_shared_mem,args=(shm_1.array,stop_event))

        p1.start()
        p2.start()
        
        time.sleep(50)
        stop_event.set()

        p1.join()
        p2.join()
        shm_1.close()
        shm_1.unlink()

    except Exception as e:
        p1.join()
        # p2.join()
        shm_1.shm.close()
        shm_1.shm.unlink()
    

    # can_read(shm_1.array,bus1)
    # time.sleep(5)
    # # stop_event.set()
    # shm_1.shm.close()
    # shm_1.shm.unlink()


    
    
            
# import can
# import logging
# from datetime import datetime
# import time

# # Set up logging
# logging.basicConfig(filename='can_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# class MyCANListener(can.Listener):
#     def on_message_received(self, msg):
#         log_entry = f"RECEIVED - ID: {msg.arbitration_id}, DLC: {msg.dlc}, Data: {msg.data.hex()}"
#         logging.info(log_entry)
#         print(log_entry)

# def send_can_message(bus):
#     # Example CAN message
#     msg = can.Message(arbitration_id=0x123, data=[0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88], is_extended_id=False)
#     try:
#         bus.send(msg)
#         log_entry = f"TRANSMITTED - ID: {msg.arbitration_id}, DLC: {msg.dlc}, Data: {msg.data.hex()}"
#         logging.info(log_entry)
#         print(log_entry)
#     except can.CanError:
#         print("Message NOT sent")

# def main():
#     # Set up the CAN interface (replace 'vcan0' with your actual CAN interface)
#     bus = can.interface.Bus(channel='can0', bustype='socketcan')

#     # Set up the logger to log messages to a file
#     logger = can.Logger('can_log_titoo.mf4')
    

#     # Create an instance of your listener
#     listener = MyCANListener()

#     # Create a Notifier to manage the logger and listener
#     notifier = can.Notifier(bus, [logger])

#     print("Logging CAN messages to can_log.asc. Press Ctrl+C to stop.")

#     try:
#         # Periodically send a CAN message
#         while True:
#             send_can_message(bus)
#             time.sleep(1)  # Adjust the sleep time as needed
#     except KeyboardInterrupt:
#         print("Stopping CAN logger.")
#     finally:
#         # Clean up the notifier
#         notifier.stop()

# if __name__ == "__main__":
#     main()
