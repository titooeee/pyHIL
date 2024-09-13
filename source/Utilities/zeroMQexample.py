# import zmq

# def subscriber():
#     context = zmq.Context()
#     socket = context.socket(zmq.SUB)
#     socket.connect("tcp://localhost:5555")

#     topic_filter = "topic1"
#     socket.setsockopt_string(zmq.SUBSCRIBE, "")

#     while True:
#         message = socket.recv_string()
#         print(f"Received: {message}")

# if __name__ == "__main__":
#     subscriber()


# import zmq

# def server():
#     context = zmq.Context()
#     socket = context.socket(zmq.REP)
#     socket.bind("tcp://*:5556")

#     try:
#         while True:
#             message = socket.recv_string()
#             print(f"Received request: {message}")
#             response = f"Response to {message}"
#             socket.send_string(response)
#             print(f"Sent: {response}")
#     except KeyboardInterrupt:
#         print("Server interrupted, closing socket and context")
#     finally:
#         socket.close()
#         context.term()

# if __name__ == "__main__":
#     server()



import can
import time
import zmq
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
            self.bus = can.interface.Bus(channel=self.interface, bustype='nixnet')
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
            self.bus.shutdown()
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

def server():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5556")

    try:
        while True:
            message = socket.recv_string()
            print(f"Received request: {message}")
            if len(message)>1:
                if message == '>>>start<<<':
                    interface = 'CAN2'  # Replace with your actual interface
                    log_file = r'C:\Users\mtitoo\Downloads\tdmsfile\can_log.mf4'
                    log_file = fr'C:\Users\mtitoo\Downloads\tdmsfile\can_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.asc'
                    stop_event = Event()
                    p = Process(target=can_logging_process, args=(interface, log_file, stop_event))
                    p.start()
                
                    response = "CAN bus log started"
                    socket.send_string(response)
                    print(f"Sent: {response}")
                elif message == 'stop':
                    stop_event.set()
                    p.join()
                    print("Main process stopped.")
                    response = "CAN bus log stop"
                    socket.send_string(response)
                    print(f"Sent: {response}")
                else:
                    response = "Invalid"
                    socket.send_string(response)
            else:
                print('waiting on message')


    except KeyboardInterrupt:
        print("Server interrupted, closing socket and context")
    finally:
        socket.close()
        context.term()

class StateMachineServer:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5556")
        self.state = "IDLE"

    def handle_idle(self, message):
        if message == "start":
            interface = 'CAN2'  # Replace with your actual interface
            log_file = r'C:\Users\mtitoo\Downloads\tdmsfile\can_log.mf4'
            log_file = fr'C:\Users\mtitoo\Downloads\tdmsfile\can_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.asc'
            self.stop_event = Event()
            self.p = Process(target=can_logging_process, args=(interface, log_file, self.stop_event))
            self.p.start()
            self.state = "RUNNING"
            return "Transitioning to RUNNING state"
        return "IDLE state: Unrecognized command"

    def handle_running(self, message):
        if message == "stop":
            self.stop_event.set()
            self.p.join()
            print("Main process stopped.")
            # response = "CAN bus log stop"
            # self.socket.send_string(response)
            # print(f"Sent: {response}")
            self.state = "IDLE"
            return "Transitioning to IDLE state"
        return "RUNNING state: Processing"

    def handle_request(self, message):
        if self.state == "IDLE":
            return self.handle_idle(message)
        elif self.state == "RUNNING":
            return self.handle_running(message)
        else:
            return "Unknown state"

    def start(self):
        try:
            while True:
                message = self.socket.recv_string()
                print(f"Received request: {message}")
                response = self.handle_request(message)
                self.socket.send_string(response)
                print(f"Sent: {response}")
        except KeyboardInterrupt:
            print("Server interrupted, closing socket and context")
        finally:
            self.socket.close()
            self.context.term()

if __name__ == "__main__":
    server = StateMachineServer()
    server.start()

# if __name__ == "__main__":
#     server()
