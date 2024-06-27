import dbc_processor as dp
import multiprocessing
import time
import random

# a = {'can0': {'ControlCmd': {'CRC8_CMD1': 0, 'TargetMode': 0, 'TargetMotorID_CMD1': 0, 'PositionCmd_64': 0, 'TorqueCommand_8': 0, 'TorqueCloseLoopMax_32': 0, 'Counter_CMD1': 0}, 'TorqueSensorData': {'CRC8_DATA1': 0, 'Counter_DATA1': 0, 'TorqueSense': 0}}}
# a['can0'].update({'ControlCmd': {'CRC8_CMD1': 8858, 'TargetMode': 0, 'TargetMotorID_CMD1': 0, 'PositionCmd_64': 0, 'TorqueCommand_8': 0, 'TorqueCloseLoopMax_32': 0, 'Counter_CMD1': 0}})
# print(a)



# print("before----",shm_gen.can_shm_dict)
# b = shm_gen.can_shm_dict
# b.update({'can0': {'ControlCmd': {'CRC8_CMD1': 1, 'TargetMode': 0, 'TargetMotorID_CMD1': 0, 'PositionCmd_64': 0, 'TorqueCommand_8': 0, 'TorqueCloseLoopMax_32': 0, 'Counter_CMD1': 0}}})
# print("after:----",b)


def update_shm_dict(shared_dict,lock):
    # for i in range(10000):
    lock.acquire()
    shared_dict['can0'].update({'ControlCmd': {'CRC8_CMD1': 10*random.randint(1,10), 'TargetMode': 0, 'TargetMotorID_CMD1': 0, 'PositionCmd_64': 0, 'TorqueCommand_8': 0, 'TorqueCloseLoopMax_32': 0, 'Counter_CMD1': 0}})
    # shared_dict['can0']['ControlCmd']['CRC8_CMD1'] = i*10
    # shared_dict['new3'] = i
    # print(b)
    # print(f"in first-{shared_dict['can0']['TorqueSensorData']['Counter_DATA1']}")
    lock.release()
    # time.sleep(1)

def update_shm_dict_2(shared_dict,lock):
    
    for i in range(10000):
        lock.acquire()
        shared_dict['can0'].update({'TorqueSensorData': {'CRC8_DATA1': 0, 'Counter_DATA1': i*20, 'TorqueSense': 0} })
        # shared_dict['can0']['TorqueSensorData']={'CRC8_DATA1': i, 'Counter_DATA1': 0, 'TorqueSense': 0}
        # shared_dict['new'][] = 3
        # shared_dict['new'] = {'new':i}
        
        print(f"in second-{shared_dict['can0']['ControlCmd']['CRC8_CMD1']}")
        lock.release()
        # time.sleep(1)



if __name__=='__main__':
    # manager = multiprocessing.Manager()
    
    # Create a shared dictionary
    shm_gen = dp.can_dict('/home/mtitoo/pyHIL/config_testDB.yml')
    shm_gen.create_can_shm_template()
    shared_dict = shm_gen.can_shm_dict
    # shared_dict = manager.dict()
    print(f"in main -{shared_dict['can0']['TorqueSensorData']['Counter_DATA1']}")
    print(f"original dict - {shared_dict}")
    lock = shm_gen.manager.Lock()
    process =[]
    for i in range(100):
        p=multiprocessing.Process(target=update_shm_dict, args=(shared_dict,lock))
        process.append(p)
        p.start()

    # p1 = multiprocessing.Process(target=update_shm_dict, args=(shared_dict,lock))
    # p2 = multiprocessing.Process(target=update_shm_dict_2, args=(shared_dict,lock))
    t1 = time.perf_counter()
    for p in process:
        p.join()
    
    print(f"time took {time.perf_counter()-t1}")
    
    print(f"in main-{shared_dict['can0']['ControlCmd']['CRC8_CMD1']}")
    # p1.start()
    # p2.start()

    # time.sleep(2)
    # p1.join()
    # p2.join()

