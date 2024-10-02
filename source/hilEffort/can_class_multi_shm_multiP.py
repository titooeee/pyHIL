
import can_bus_manager_multiP as can_mgr
import yaml
import dbc_processor as dp
import multiprocessing
import time
import random
import asyncio
import logging
import platform
import keyboard
import tkinter as tk
from tkinter import scrolledtext
logging.basicConfig(level=logging.INFO)
# async def main():
def main():
    manager = multiprocessing.Manager()

    if platform.system() == "Linux":
        shm_gen = dp.can_dict('/home/mtitoo/pyHIL/config_testDB.yml',manager)
    else:
        shm_gen= dp.can_dict(r'C:\Users\Public\Documents\gitRepoExternal\pyHIL\supportFiles\config_testDB.yml',manager)
    shm_gen.create_can_shm_template()
    shared_dict = shm_gen.can_shm_dict

    lst_msg = ["ControlCmd","ControlStatus","LimitsCmd"]
    
    if platform.system() == "Linux":
        with open('/home/mtitoo/pyHIL/config_testDB.yml','r') as file:
            dynoConfig = yaml.safe_load(file)
    else:
        with open(r'C:\Users\Public\Documents\gitRepoExternal\pyHIL\supportFiles\config_testDB.yml','r') as file:
            dynoConfig = yaml.safe_load(file)

    
    
    
    # # Create the GUI
    # root = tk.Tk()
    # root.title("Shared Memory Content")

    # text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
    # text_widget.pack(padx=10, pady=10)
    # text_widget.config(state=tk.DISABLED)

    # # Start a separate process to update the GUI
    # gui_process = multiprocessing.Process(target=update_gui, args=(shared_dict, text_widget))
    # gui_process.start()

    # # Start the Tkinter main loop
    # root.mainloop()
    
    
    
    canBuses = dynoConfig['CANBUS']
    buses = []
    task = []
    log_notifier_list = []
    stop_event = multiprocessing.Event()
    lock = shm_gen.manager.Lock()
    process =[]
    # stop_event_as = asyncio.Event()
    stop_event_as = asyncio.Event()

    
    for bus_config in canBuses:
        
        p1 = can_mgr.can_bus_manager(name= 'Process'+bus_config['Interface'],can_bus_config=bus_config,shm_can_dict=shared_dict,stop_event=stop_event,lock=lock)
        process.append(p1)
        p1.start()

    # time.sleep(5)
    wait_for_keypress(shared_dict)
    stop_event.set()
    # for canobj in buses:
    #     canobj.stop_can_bus()
    for p in process:
        p.join()
    
    # shared_dict.close()
    # shared_dict.unlink()

    # gui_process.terminate()

def wait_for_keypress(shared_dict):
    print("Press 'x' to stop the test...")

    # Wait for the 'x' key to be pressed
    while True:
        # print_unknown_structure(shared_dict)
        if keyboard.is_pressed('x'):
            print("Key 'x' pressed. Stopping the test.")
            break
        time.sleep(2)  # Sleep to prevent excessive CPU usage

def print_unknown_structure(d, indent=0):
    formatText = ""
    for key, value in d.items():
        print('  ' * indent + str(key) + ': ', end='')
        formatText+= '  ' * indent + str(key) + ': '+':'

        # Check if the value is a DictProxy object (shared dict)
        if isinstance(value, dict) or isinstance(value, multiprocessing.managers.DictProxy):
            print()  # New line for nested dict or DictProxy
            # If it's a DictProxy, dereference it
            # if hasattr(value, '_get_dict'):
            if isinstance(value, (int, float)):
                value = value  # Access the actual dictionary
            formatText += print_unknown_structure(value, indent + 1)  # Recursively print
        else:
            # Print the value if it's not a dictionary or DictProxy
            formatText += str(value) + '\n'
    return formatText
# def update_gui(shared_dict, text_widget):
#     while True:
#         # content = print_unknown_structure(shared_dict)
#         text_widget.config(state=tk.NORMAL)
#         text_widget.delete(1.0, tk.END)
#         text_widget.insert(tk.END, content)
#         text_widget.config(state=tk.DISABLED)
#         time.sleep(1)


if __name__== '__main__':
    # asyncio.run(main())
    main()
    