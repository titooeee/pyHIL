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
import asyncio
import threading

class can_bus_manager (multiprocessing.Process):
    def __init__(self,name,can_bus_config,shm_can_dict,stop_event,lock):
        super().__init__()
        self.name = name
        self.can_bus_config = can_bus_config
        self.shm_can_dict = shm_can_dict
        self.db = cantools.database.load_file(can_bus_config['DBC'])
        self.stop_event = stop_event
        self.lock = lock
        self.logger = logging.getLogger(__name__)
        self.notifier = None
        self.buffer = None
        self.localEvent = multiprocessing.Event()
        self.rx_list_dict = {}
    
    def start_bus(self):
        # BUS = can.interface.Bus(channel=key['Channel'], bustype =key['Interface'], bitrate=key['BAUD'] )
        self.bus = can.Bus(interface=self.can_bus_config['Interface'], channel=self.can_bus_config['Channel'], bitrate=self.can_bus_config['BAUD'], fd = False)

    
    def update_msg(self):
        self.messages = []
        self.rate = []
        self.lock.acquire()
        try:
            for msg_name in self.can_bus_config['TX_LIST']:
                msg = self.db.get_message_by_name(msg_name)
                msg_dict = self.shm_can_dict[self.can_bus_config['Channel']][msg_name]
                self.change_shm()
                data = msg.encode(dict(msg_dict.items()))
                # data = msg.encode(a)
                self.messages.append(can.Message(arbitration_id=msg.frame_id, data=data,is_extended_id=msg.is_extended_frame))
                
                self.rate.append(msg.cycle_time/100)
        finally:
            self.lock.release()
    
    def start_tx_cyclic(self):
        self.task = []
        for idx in range(len(self.messages)):
            t = self.bus.send_periodic(self.messages[idx], self.rate[idx])
            print(self.rate[idx],'\n')
            assert isinstance(t, can.CyclicSendTaskABC)
            self.task.append(t)
    
    def modify_tx_cyclic(self):
        for idx in range(len(self.messages)):
            self.task[idx].modify_data(self.messages[idx])
    
    def start_logger(self):
        # logger = can.SizedRotatingLogger(str(self.can_bus_config['Channel']+".mf4"),max_bytes=5*1024**2)
        logger = can.Logger(str(self.can_bus_config['Channel']+".asc"))
        self.buffer = can.BufferedReader()
        self.notifier  = can.Notifier(self.bus, [logger,self.buffer],timeout=1)
        # self.notifier  = can.Notifier(self.bus, [self.buffer],timeout=1)
        rx_list_set = set(self.can_bus_config['RX_LIST'])
        # self.rx_list_dict = dict()
        self.rx_list_dict[self.can_bus_config['Channel']] = {}
        try:
            while not self.localEvent.is_set():
                # self.update_msg()
                # self.modify_tx_cyclic()
                msg = self.buffer.get_message()
                if msg:
                        print("notifier receive msg:",self.can_bus_config['Channel'],msg)
                        if msg:
                            decoded_db_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
                            # Check if the message matches any of the filters
                            # print(decoded_db_msg.name)
                            if decoded_db_msg.name in rx_list_set:
                                decoded_message = self.decode_can_message(msg)
                                # print(decoded_message)
                                
                                if decoded_message:
                                    # print('hereeeee',decoded_message)
                                    # self.lock.acquire()
                                    # self.shm_can_dict[self.can_bus_config['Channel']][decoded_db_msg.name].update(decoded_message)
                                    self.rx_list_dict[self.can_bus_config['Channel']][decoded_db_msg.name]= decoded_message
                                    # print('Temp data:',self.rx_list_dict)
                                    # self.lock.release()
            # print(f"pos-1:{time.time()}")
            
            # self.close()
        except Exception as e:
            print(e)
            # self.close()
        
    def decode_can_message(self,msg):
        try:
            # Decode the message using cantools
            decoded = self.db.decode_message(msg.arbitration_id, msg.data)
            return decoded
        except KeyError:
            # If the message ID is not in the DBC file
            return None
    
    def stop_can_bus(self):
        try:
            for cyclic_task in self.task:
                cyclic_task.stop()
            self.notifier.stop()
            time.sleep(2)
            self.bus.shutdown()
        except Exception as e:
            print(e)
            
    
    def cyclic_task(self):
        while not self.stop_event.is_set():
            self.change_shm()
            self.update_msg()
            self.modify_tx_cyclic()
            time.sleep(0.1)
        
        for cyclic_task in self.task:
                cyclic_task.stop()
        self.task.clear()
        
        self.close()
        time.sleep(1)
        self.localEvent.set()
        

    def change_shm(self):
        # self.lock.acquire()
        self.shm_can_dict[self.can_bus_config['Channel']]['ControlCmd'].update({'CRC8_CMD1': 10*random.randint(1,10), 'TargetMode': 0, 'TargetMotorID_CMD1': 0, 'PositionCmd_64': 0, 'TorqueCommand_8': 0, 'TorqueCloseLoopMax_32': 0, 'Counter_CMD1': 0})
        self.shm_can_dict[self.can_bus_config['Channel']]['TorqueSensorData'].update({'CRC8_DATA1': 0, 'Counter_DATA1': 0, 'TorqueSense': random.randint(1,3)})
        # self.lock.release()
    
    def close(self):
        self.logger.info("Shutting down CAN bus and logger.")
        if self.notifier:
            self.notifier.stop()
        if self.bus:
            self.bus.shutdown()
            # self.buffer.stop()
        self.logger.info("CAN bus and logger shut down successfully.")

    def run(self):
        self.update_msg()
        self.start_bus()
        self.start_tx_cyclic()
        task1 = threading.Thread(target=self.start_logger())
        # task2 = threading.Thread(target=self.cyclic_task())
        task1.start()
        while not self.stop_event.is_set():
            # self.change_shm()
            # self.update_msg()
            # self.modify_tx_cyclic()
            time.sleep(0.01)
        
        for cyclic_task in self.task:
                cyclic_task.stop()
        self.logger.info("Stopped cyclic out")
        self.task.clear()
        self.localEvent.set()
        self.close()
        
    # def __del__(self):
    #     self.close()


        
