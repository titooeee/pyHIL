# daq_interface.py
from abc import ABC, abstractmethod

class DAQInterface(ABC):
    @abstractmethod
    def read_data(self, channel):
        pass

    @abstractmethod
    def write_data(self, channel, value):
        pass

    @abstractmethod
    def close(self):
        pass
