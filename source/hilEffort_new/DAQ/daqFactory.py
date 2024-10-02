# daq_factory.py
from simulatedDAQ import simDAQ

class DAQFactory:
    @staticmethod
    def get_daq(daq_type=None):
        """
        Autoload the proper DAQ based on the `daq_type`.
        If no type is passed, it can default to LabJack.
        """
        if daq_type == "LabJack":
            return LabJackDAQ()
        elif daq_type == "OtherDAQ":
            return OtherDAQ()
        else:
            # Autodetect or set default
            return LabJackDAQ()  # Default to LabJack
