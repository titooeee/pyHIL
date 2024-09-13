# import can
# import time

# class CANLogger:
#     def __init__(self, interface='can0', log_file='can_log.asc'):
#         self.interface = interface
#         self.log_file = log_file
#         self.bus = None
#         self.logger = None

#     def setup_can_interface(self):
#         try:
#             self.bus = can.interface.Bus(channel=self.interface, bustype='nixnet')
#             print(f"Successfully connected to CAN interface {self.interface}")
#         except OSError as e:
#             print(f"Failed to connect to CAN interface {self.interface}: {e}")
#             raise

#     def start_logging(self):
#         if self.bus is None:
#             self.setup_can_interface()

#         self.logger = can.Logger(self.log_file)
#         self.notifier = can.Notifier(self.bus, [self.logger])
#         print(f"Logging CAN messages to {self.log_file}... Press Ctrl+C to stop.")

#     def stop_logging(self):
#         if self.notifier is not None:
#             self.notifier.stop()
#             print("Logger process stopped.")
#         else:
#             print("No logger process running.")

# if __name__ == "__main__":
#     interface = 'CAN2'  # Replace with your actual interface
#     log_file = r'C:\Users\mtitoo\Downloads\tdmsfile\can_log.mf4'

#     logger = CANLogger(interface=interface, log_file=log_file)
#     try:
#         logger.start_logging()
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         logger.stop_logging()
#         print("Logging stopped.")


import can
import time
from multiprocessing import Process, Event
from datetime import datetime

class CANLogger:
    def __init__(self, interface='can0', log_file='can_log.asc'):
        self.interface = interface
        self.log_file = log_file
        self.bus = None
        self.logger = None
        self.notifier = None

    def setup_can_interface(self):
        try:
            self.bus = can.interface.Bus(channel=self.interface, bustype='nixnet',bitrate = 125000,fd = True)
            print(f"Successfully connected to CAN interface {self.interface}")
        except OSError as e:
            print(f"Failed to connect to CAN interface {self.interface}: {e}")
            raise

    def start_logging(self):
        if self.bus is None:
            self.setup_can_interface()

        # self.logger = can.Logger(self.log_file) can.lo
        self.logger = can.SizedRotatingLogger(self.log_file,max_bytes=10*1024)
        self.notifier = can.Notifier(self.bus, [self.logger])
        print(f"Logging CAN messages to {self.log_file}... Press Ctrl+C to stop.")

    def stop_logging(self):
        if self.notifier is not None:
            self.notifier.stop()
            print("Logger process stopped.")
        else:
            print("No logger process running.")

def can_logging_process(interface, log_file, stop_event):
    logger = CANLogger(interface=interface, log_file=log_file)
    try:
        logger.start_logging()
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.stop_logging()
        print("Logging stopped.")

if __name__ == "__main__":
    interface = 'CAN2'  # Replace with your actual interface
    log_file = r'C:\Users\mtitoo\Downloads\tdmsfile\can_log.mf4'
    log_file = fr'C:\Users\mtitoo\Downloads\tdmsfile\can_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.asc'


    stop_event = Event()
    p = Process(target=can_logging_process, args=(interface, log_file, stop_event))
    p.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        p.join()
        print("Main process stopped.")
