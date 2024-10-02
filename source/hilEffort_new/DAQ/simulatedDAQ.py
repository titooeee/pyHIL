# other_daq.py
from daqInterface import DAQInterface
from labjackDAQ import LabJackDAQ
import random

class simDAQ(DAQInterface):
    def __init__(self):
        # Initialize the other DAQ system here
        pass

    def read_data(self, channel):
        # Read data from other DAQ
        return random.randint(1,127)  # Example value

    def write_data(self, channel, value):
        # Write data to other DAQ
        pass

    def close(self):
        # Close connection
        pass
