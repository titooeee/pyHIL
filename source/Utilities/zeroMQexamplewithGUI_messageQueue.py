import tkinter as tk
from tkinter import messagebox
import can
import time
import zmq
from multiprocessing import Process, Event, Queue  # Use multiprocessing.Queue
from datetime import datetime
import threading
import json
import queue  # You can remove this if it's no longer used
import multiprocessing

class CANLogger:
    def __init__(self, interface='can0', log_file='can_log.asc', message_queue=None):
        self.interface = interface
        self.log_file = log_file
        self.bus = None
        self.logger = None
        self.notifier = None
        self.message_queue = message_queue  # Store the message queue
        

    def setup_can_interface(self):
        try:
            self.bus = can.interface.Bus(channel=self.interface, bustype='nixnet',receive_own_messages = True)
            self.log_message(f"Successfully connected to CAN interface {self.interface}")
        except OSError as e:
            self.log_message(f"Failed to connect to CAN interface {self.interface}: {e}")
            raise

    def start_logging(self):
        if self.bus is None:
            self.setup_can_interface()

        self.logger = can.SizedRotatingLogger(self.log_file, max_bytes=200*1024)
        self.notifier = can.Notifier(self.bus, [self.logger])
        self.log_message(f"Logging CAN messages to {self.log_file}... Press Ctrl+C to stop.")

    def stop_logging(self):
        if self.notifier is not None:
            self.notifier.stop()
            self.bus.shutdown()
            self.log_message("Logger process stopped.")
        else:
            self.log_message("No logger process running.")

    def log_message(self, message):
        if self.message_queue:
            self.message_queue.put(message)
        else:
            print(message)

def can_logging_process(interface, log_file, stop_event, message_queue):
    logger = CANLogger(interface=interface, log_file=log_file, message_queue=message_queue)
    try:
        logger.start_logging()
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.stop_logging()
        logger.log_message("Logging stopped.")
class StateMachineServer:
    def __init__(self, update_gui_callback, message_queue):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5556")
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.state = "IDLE"
        self.update_gui_callback = update_gui_callback
        self.message_queue = message_queue  # Store the message queue
        self.canProcess = []
        self.stop_event = multiprocessing.Event()

    def handle_idle(self, message):
        if message == "start":
            file_path = r"C:\Users\Public\Documents\dynoSoftwareSuite\systemDefinitionTool\config\pythonCANLogger.json"
            with open(file_path,'r') as file:
                data =  json.load(file)
            
            for section in data:
                interface = section['interfaceName']
                log_file = fr'C:\Users\mtitoo\Downloads\tdmsfile\{section["interfaceName"]}_{section["vsPortName"]}_can_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mf4'
                
                p = Process(target=can_logging_process, args=(interface, log_file, self.stop_event, self.message_queue))
                p.start()
                self.canProcess.append(p)
                self.state = "RUNNING"
                self.update_gui_callback(self.state)
            return "Transitioning to RUNNING state"
        return "IDLE state: Unrecognized command"

    def handle_running(self, message):
        if message == "stop":
            self.stop_event.set()
            for p in self.canProcess:
                print(f"Closing Thread- {p}")
                p.join()
                
            self.state = "IDLE"
            self.update_gui_callback(self.state)
            self.stop_event.clear()
            self.canProcess.clear()
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
                            if message == "quit-app":
                                self.socket.send_string("Quitting")
                                break
                            response = self.handle_request(message)
                            self.socket.send_string(response)
                        except zmq.Again as e:
                            pass
                        except zmq.ZMQError as e:
                            break
                    else:
                        continue
                except KeyboardInterrupt:
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
        self.message_queue = Queue()  # Create the multiprocessing.Queue

        self.history_text = tk.Text(master, state='disabled', height=10, width=150)
        self.history_text.pack(pady=10)

    def start_server(self):
        if self.server_thread is None:
            self.running = True
            self.server_thread = threading.Thread(target=self.server_loop)
            self.server_thread.start()
            self.update_state("RUNNING")
            self.master.after(100, self.check_messages)  # Periodically check the message queue
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
        server = StateMachineServer(self.update_state, self.message_queue)
        server.start()

    def check_messages(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.append_to_history(message)
        except queue.Empty:
            pass
        if self.running:
            self.master.after(100, self.check_messages)  # Continue checking the queue if running

    def append_to_history(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"{timestamp}: {message}\n"
        self.history_text.configure(state='normal')
        self.history_text.insert(tk.END, formatted_message)
        self.history_text.configure(state='disabled')
        self.history_text.yview(tk.END)  # Scroll to the end of the text box

if __name__ == "__main__":
    root = tk.Tk()
    app = StateMachineGUI(root)
    app.start_server()
    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = StateMachineGUI(root)
    app.start_server()
    root.mainloop()
