import tkinter as tk
from tkinter import messagebox
import can
import time
import zmq
from multiprocessing import Process, Event
from datetime import datetime
import threading
import json

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

        self.logger = can.SizedRotatingLogger(self.log_file, max_bytes=10*1024)
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

class StateMachineServer:
    def __init__(self, update_gui_callback):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5556")
        # Create a poller
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.state = "IDLE"
        self.update_gui_callback = update_gui_callback

    def handle_idle(self, message):
        if message == "start":
            file_path = r"C:\Users\Public\Documents\dynoSoftwareSuite\systemDefinitionTool\config\pythonCANLogger.json"
            with open(file_path,'r') as file:
                data =  json.load(file)
            
            for section in data:
                # interface = 'CAN2'  # Replace with your actual interface
                interface = section['interfaceName']
                print(f"interface name >>>>>>>>>>>>{interface}")
                log_file = fr'C:\Users\mtitoo\Downloads\tdmsfile\{section['interfaceName']}_{section['vsPortName']}_can_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.asc'
                self.stop_event = Event()
                self.p = Process(target=can_logging_process, args=(interface, log_file, self.stop_event))
                self.p.start()
                self.state = "RUNNING"
                self.update_gui_callback(self.state)
            return "Transitioning to RUNNING state"
        return "IDLE state: Unrecognized command"

    def handle_running(self, message):
        if message == "stop":
            self.stop_event.set()
            self.p.join()
            print("Main process stopped.")
            self.state = "IDLE"
            self.update_gui_callback(self.state)
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
                try:
                    socks = dict(self.poller.poll(1000))
                    if self.socket in socks:
                        try:
                            message = self.socket.recv_string(zmq.DONTWAIT)
                            print(f"Received request: {message}")
                            if message == "quit-app":
                                self.socket.send_string("Quitting")
                                print("quitting app")
                                break
                            response = self.handle_request(message)
                            self.socket.send_string(response)
                            print(f"Sent: {response}")
                        except zmq.Again as e:
                            print("No message received (non-blocking).")
                        except zmq.ZMQError as e:
                            print(f"ZMQError: {e}")
                            break  # Exit the loop if a serious error occurs
                    else:
                        continue
                        # print("No message received within the timeout period.")
                except KeyboardInterrupt:
                    print("Server interrupted, closing socket and context")
                    break
        finally:
            self.socket.close()
            self.context.term()

                    
        


class StateMachineGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("State Machine GUI")

        self.state_label = tk.Label(master, text="State: INIT", font=("Helvetica", 16))
        self.state_label.pack(pady=10)

        self.start_button = tk.Button(master, text="Start Server", command=self.start_server)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(master, text="Stop Server", command=self.stop_server)
        self.stop_button.pack(pady=5)

        self.quit_button = tk.Button(master, text="Quit", command=self.quit)
        self.quit_button.pack(pady=5)

        self.server_thread = None
        self.running = False

    def start_server(self):
        if self.server_thread is None:
            self.running = True
            self.server_thread = threading.Thread(target=self.server_loop)
            self.server_thread.start()
            self.update_state("RUNNING")
        else:
            messagebox.showinfo("Info", "Server is already running")

    def stop_server(self):
        if self.server_thread is not None:
            self.running = False
            self.server_thread.join()
            self.server_thread = None
            self.update_state("STOPPED")

    def quit(self):
        self.stop_server()
        self.master.quit()

    def update_state(self, state):
        self.state_label.config(text=f"State: {state}")

    def server_loop(self):
        server = StateMachineServer(self.update_state)
        server.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = StateMachineGUI(root)
    app.start_server()
    root.mainloop()
