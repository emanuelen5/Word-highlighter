
import os
__dir__ = os.path.dirname(os.path.realpath(__file__))
logs_dir = os.path.join(__dir__, '..', 'logs')

# Check that select bits are set
def bits_set(value, *bits):
    from functools import reduce
    bit_mask = reduce(lambda x,y: x | y, bits)
    return (value & bit_mask) == bit_mask

def get_logfile_path(filename):
    basename = os.path.splitext(os.path.basename(filename))[0]
    log_file = os.path.join(logs_dir, basename + ".log")
    os.makedirs(logs_dir, exist_ok=True)
    return log_file