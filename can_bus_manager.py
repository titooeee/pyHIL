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

class can_bus_manager:
    def __init__(self,can_bus_config,shm_can_dict,stop_event,lock,stop_event_as):
        self.can_bus_config = can_bus_config
        self.shm_can_dict = shm_can_dict
        self.db = cantools.database.load_file(can_bus_config['DBC'])
        self.stop_event = stop_event
        self.lock = lock
        self.stop_event_as = stop_event_as
        self.logger = logging.getLogger(__name__)
    
    def start_bus(self):
        # BUS = can.interface.Bus(channel=key['Channel'], bustype =key['Interface'], bitrate=key['BAUD'] )
        self.bus = can.Bus(interface=self.can_bus_config['Interface'], channel=self.can_bus_config['Channel'], bitrate=self.can_bus_config['BAUD'])

    
    def update_msg(self):
        self.messages = []
        self.rate = []
        for msg_name in self.can_bus_config['TX_LIST']:
            msg = self.db.get_message_by_name(msg_name)
            self.lock.acquire()
            msg_dict = self.shm_can_dict[self.can_bus_config['Channel']][msg_name]
            self.lock.release()
            self.change_shm()
            data = msg.encode(dict(msg_dict.items()))
            # data = msg.encode(a)
            self.messages.append(can.Message(arbitration_id=msg.frame_id, data=data))
            self.rate.append(msg.cycle_time)
    
    def start_tx_cyclic(self):
        self.task = []
        for idx in range(len(self.messages)):
            t = self.bus.send_periodic(self.messages[idx], self.rate[idx]/1000)
            assert isinstance(t, can.CyclicSendTaskABC)
            self.task.append(t)
    
    def modify_tx_cyclic(self):
        for idx in range(len(self.messages)):
            self.task[idx].modify_data(self.messages[idx])
    
    
    def start_logger(self):
        # logger = can.SizedRotatingLogger(str(self.can_bus_config['Channel']+".mf4"),max_bytes=5*1024**2)
        logger = can.Logger(str(self.can_bus_config['Channel']+".mf4"))
        
        self.buffer = can.BufferedReader()
        self.notifier  = can.Notifier(self.bus, [logger,self.buffer],timeout=5)
        try:
            while not self.stop_event.is_set():
                self.update_msg()
                self.modify_tx_cyclic()
                msg = self.buffer.get_message()
                if msg:
                        print("notifier receive msg:",msg)
                        if msg:
                            decoded_db_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
                            # Check if the message matches any of the filters
                            if any(f == decoded_db_msg.name for f in self.can_bus_config['RX_LIST']):
                                decoded_message = self.decode_can_message(msg)
                                if decoded_message:
                                    # print(decoded_message)
                                    self.lock.acquire()
                                    self.shm_can_dict[self.can_bus_config['Channel']][decoded_db_msg.name].update(decoded_message)
                                    self.lock.release()
            print(f"pos-1:{time.time()}")
            
            self.close()
        except Exception as e:
            e
            self.close()
        
 
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
            self.update_msg()
            self.modify_tx_cyclic()
            time.sleep(0.001)
        self.close()


    def change_shm(self):
        self.lock.acquire()
        self.shm_can_dict[self.can_bus_config['Channel']]['ControlCmd'].update({'CRC8_CMD1': 10*random.randint(1,10), 'TargetMode': 0, 'TargetMotorID_CMD1': 0, 'PositionCmd_64': 0, 'TorqueCommand_8': 0, 'TorqueCloseLoopMax_32': 0, 'Counter_CMD1': 0})
        self.shm_can_dict[self.can_bus_config['Channel']]['TorqueSensorData'].update({'CRC8_DATA1': 0, 'Counter_DATA1': 0, 'TorqueSense': random.randint(1,3)})
        self.lock.release()
    
    def close(self):
        self.logger.info("Shutting down CAN bus and logger.")
        for cyclic_task in self.task:
                cyclic_task.stop()
        if self.notifier:
            self.notifier.stop()
        if self.bus:
            self.bus.shutdown()
        self.logger.info("CAN bus and logger shut down successfully.")

    def __del__(self):
        self.close()


        
