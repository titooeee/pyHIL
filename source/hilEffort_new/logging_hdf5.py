import h5py
import multiprocessing.process
import time
import os
import copy


class h5pyWriter(multiprocessing.Process):
    def __init__(self,hdf5FilePath,mpSharedMem,stop_event,mpLock):
        self.hdf5FilePath = hdf5FilePath
        self.mpSharedMem = mpSharedMem
        self.stop_event = stop_event
        self.mpLock = mpLock
    def read_and_write_to_hdf5(self):
        if os.path.exists(self.hdf5FilePath):
            os.remove(self.hdf5FilePath)
        with h5py.File(self.hdf5FilePath, 'a') as hdf:
            for key in self.mpSharedMem['CAN'].keys():
                hdf.create_dataset(key, (0,), maxshape=(None,), dtype='f')
            hdf.create_dataset('systemChannel/systemTime', (0,), maxshape=(None,), dtype='f')
            values = {f'{key}': [] for key in self.mpSharedMem['CAN'].keys()}
            values['systemChannel/systemTime']=[]
            buffCounter = 0
            copied_data = self.mpSharedMem
            while not self.stop_event.is_set():
                # # self.mpLock.acquire()
                # # copied_data = copy.deepcopy(dict(self.mpSharedMem))
                

                
                # # self.mpLock.release()
                for key in self.mpSharedMem['CAN'].keys():
                    # values[key].append(copied_data['CAN'][key]['value'])
                    self.mpSharedMem['CAN'][key]['value']
                # values['systemChannel/systemTime'].append(copied_data['systemChannel']['systemTime']['value'])
                #     # print(self.mpSharedMem['CAN'][key]['value'])
                
                # buffCounter+=1

                # if buffCounter==10:
                #     print(time.perf_counter())
                    # for key in values.keys():
                #         if key in hdf:
                #             dataset = hdf[key]
                #         else:
                #             hdf.create_dataset(key, (0,), maxshape=(None,), dtype='f')
                #             print('Not found', key)
                #         # dataset.resize((dataset.shape[0] + len(values[key]),))
                #         # dataset[-len(values[key]):] = values[key]
                        # values[key].clear()
                    # values.clear()
                    # buffCounter = 0
                #     # hdf.flush()
                # print(time.perf_counter())
                time.sleep(0.01)  # Simulate cyclic reading every second