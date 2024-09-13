import yaml
import can
import time
import random
import multiprocessing
import multiprocessing.process
import numpy as np
from multiprocessing import shared_memory



a = np.array([(random.randint(1,127)) for x in range(5)],dtype=np.int8) 
shm = shared_memory.SharedMemory(name ="shm_can", create = True, size=a.nbytes)
mem_ref = np.ndarray(a.shape, dtype=a.dtype, buffer=shm.buf)

# print(mem_ref)
# # shared_mem_ref = []
# for i in range(9):
#     # mem = shared_memory.SharedMemory(name = str(i),create = True, size=a.nbytes)
#     # b = np.ndarray(a.shape, dtype=a.dtype, buffer=mem.buf)
#     b = multiprocessing.Array('i',5)
#     shared_mem_ref.append(b)
#     b[:] = np.array([random.randint(1,127) for x in range(5)])



messages = []
messages.append(
    can.Message(
        arbitration_id=0x401,
        data =mem_ref[:],
        is_extended_id=False,
    )
)
# messages.append(
#     can.Message(
#         arbitration_id=0x401,
#         data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
#         is_extended_id=False,
#     )
# )
# messages.append(
#     can.Message(
#         arbitration_id=0x401,
#         data=[0x33, 0x33, 0x33, 0x33, 0x33, 0x33],
#         is_extended_id=False,
#     )
# )
# messages.append(
#     can.Message(
#         arbitration_id=0x401,
#         data=[0x44, 0x44, 0x44, 0x44, 0x44, 0x44],
#         is_extended_id=False,
#     )
# )
# messages.append(
#     can.Message(
#         arbitration_id=0x401,
#         data=[0x55, 0x55, 0x55, 0x55, 0x55, 0x55],
#         is_extended_id=False,
#     )
# )


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
          
for _ in range(100):
    
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

shm.close()
shm.unlink()
# with open('/home/mtitoo/pyHIL/config.yml','r') as file:
#     dynoCOnfig = yaml.safe_load(file)


# dict_temp = dynoCOnfig['CANBUS']

# for key in dict_temp:
#     print(key["Interface"])