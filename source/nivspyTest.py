from niveristand import nivs_rt_sequence, NivsParam, realtimesequencetools
from niveristand.clientapi import *
from niveristand.errors import RunError
@nivs_rt_sequence
def fn_1():
    state = I32Value(0)
    iters = I32Value(0)
    amplitude = DoubleValue(1000)
    stop = BooleanValue(False)
    output = ChannelReference("Aliases/DesiredRPM")


if __name__ == "__main__":
    realtimesequencetools.save_py_as_rtseq(fn_1,r"C:\Users\Public\Documents\Python Scripts\pyHIL")