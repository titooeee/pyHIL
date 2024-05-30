import os
import numpy as np
import cantools
from multiprocessing import Process
from multiprocessing.shared_memory import SharedMemory
import random



class dbc_processor:
    def __init__(self,dbc_path,input_msg,output_msg):
        self.dbc_path  = dbc_path
        self.input_msg = input_msg
        self.output_msg = output_msg
        self.dbc_dic = {}
        self.lenght  = 0
        self.db = cantools.database.load_file(self.dbc_path)
    
    def parse(self):
        
        counter = 0
        for frame in self.input_msg:
            msg = self.db.get_message_by_name(frame)
            self.dbc_dic[msg.name] = {}
            # self.dbc_dic[msg.name]["startIdx"] = counter
            for sig in msg.signals:
                self.dbc_dic[msg.name][sig.name] = counter
                counter+=1
            # self.dbc_dic[msg.name]["endIdx"] = counter
        self.lenght = counter-1

    def get_message_by_name(self,msg_name):
        return self.db.get_message_by_name(msg_name)

        

class create_shared_mem:
    def __init__(self,shm_name,length):
        self.shape = (length,)
        self.shm = SharedMemory(name=shm_name,create=True, size=np.prod(self.shape) * np.float64().itemsize)
        self.array = np.ndarray(self.shape, dtype=np.float64, buffer=self.shm.buf)
        self.array[:] = [random.randint(1,3) for x in range(self.array.size)]  # Initialize the array



# lst_msg = ["ControlCmd","TorqueSensorData"]
lst_msg = ["ControlCmd"]

bus1 = dbc_processor("/home/mtitoo/pyHIL/open_actuator.dbc",lst_msg,lst_msg)
bus1.parse()

shared_mem_1 = create_shared_mem('vcan0',bus1.lenght+1)
print(type(shared_mem_1))

encode_dic = {}
try:
    for msg in bus1.dbc_dic.keys():
        encode_dic[msg] = {}    
        for sig in bus1.dbc_dic[msg].keys():
            encode_dic[msg][sig] = shared_mem_1.array[bus1.dbc_dic[msg][sig]]
        
        print(encode_dic[msg])
        
        example_message = bus1.get_message_by_name('ControlCmd')
        data = example_message.encode(encode_dic[msg],strict = True)
        
        print(data)
    shared_mem_1.shm.close()
    shared_mem_1.shm.unlink()
except Exception as e:
    print(f"Custom error occurred: {e}")
    shared_mem_1.shm.close()
    shared_mem_1.shm.unlink()


