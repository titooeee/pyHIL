
import can_bus_manager as can_mgr
import yaml
import dbc_processor as dp
import dbc_processor as dp
import multiprocessing
import time
import random
import asyncio
import logging
import platform
# logging.basicConfig(level=logging.DEBUG)
# async def main():
def main():
    manager = multiprocessing.Manager()

    if platform.system() == "Linux":
        shm_gen = dp.can_dict('/home/mtitoo/pyHIL/config_testDB.yml',manager)
    else:
        shm_gen= dp.can_dict("C:\\Users\\Public\\Documents\\Python Scripts\\pyHIL\\config_testDB.yml",manager)
    shm_gen.create_can_shm_template()
    shared_dict = shm_gen.can_shm_dict

    lst_msg = ["ControlCmd","ControlStatus","LimitsCmd"]
    
    if platform.system() == "Linux":
        with open('/home/mtitoo/pyHIL/config_testDB.yml','r') as file:
            dynoConfig = yaml.safe_load(file)
    else:
        with open(r'C:\Users\Public\Documents\Python Scripts\pyHIL\config_testDB.yml','r') as file:
            dynoConfig = yaml.safe_load(file)

    
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
        can_obj = can_mgr.can_bus_manager(bus_config,shared_dict,stop_event,lock,stop_event_as)
        can_obj.update_msg()
        can_obj.start_bus()
        
        can_obj.start_tx_cyclic()
        # can_obj.start_logger()
        p1=multiprocessing.Process(target=can_obj.start_logger, args=())
        p2=multiprocessing.Process(target=can_obj.cyclic_task, args=())
        process.append(p1)
        process.append(p2)
        p1.start()
        p2.start()
        buses.append(can_obj)

    time.sleep(5)
    stop_event.set()
    # for canobj in buses:
    #     canobj.stop_can_bus()
    for p in process:
        p.join()
    
    
    
    # shared_dict.close()
    # shared_dict.unlink()
if __name__== '__main__':
    # asyncio.run(main())
    main()