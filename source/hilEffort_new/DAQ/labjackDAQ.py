# labjack_daq.py
import ljm
from daqInterface import DAQInterface

class LabJackDAQ(DAQInterface):
    def __init__(self, device_type='ANY', connection_type='ANY', identifier='ANY'):
        self.handle = ljm.open(device_type, connection_type, identifier)

    def read_data(self, channel):
        return ljm.eReadName(self.handle, channel)

    def write_data(self, channel, value):
        ljm.eWriteName(self.handle, channel, value)

    def close(self):
        ljm.close(self.handle)
