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
import cantools

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
db = cantools.database.load_file('/home/mtitoo/pyHIL/open_actuator.dbc')

def decode_can_message(msg):
    try:
        # Decode the message using cantools
        decoded = db.decode_message(msg.arbitration_id, msg.data)
        return decoded
    except KeyError:
        # If the message ID is not in the DBC file
        return None

def receive_and_decode_can_messages(interface, filters):
    bus = can.interface.Bus(interface, bustype='socketcan')
    print(f"Listening on {bus.channel_info}...")
    
    while True:
        msg = bus.recv()
        if msg:
            # Check if the message matches any of the filters
            if any(f['can_id'] == msg.arbitration_id for f in filters):
                decoded_message = decode_can_message(msg)
                if decoded_message:
                    print(f"Decoded message: {decoded_message}")

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
        logger = can.SizedRotatingLogger(str(key['Channel']+".mf4"),max_bytes=5*1024)
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
        
        
        interface = 'vcan3'
        # Define filters (example: filter messages with ID 123 and 456)
        filters = [
        {"can_id": 0xFA, "can_mask": 0x7FF},
        {"can_id": 0xFB, "can_mask": 0x7FF},
        {"can_id": 0xFC, "can_mask": 0x7FF}
        ]
        # receive_and_decode_can_messages(interface, filters)
        time.sleep(5)
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
    