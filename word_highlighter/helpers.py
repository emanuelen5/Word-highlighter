import logging

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

def get_logger(module_name, file_name):
    logger = logging.getLogger(module_name)
    fh = logging.FileHandler(get_logfile_path(file_name), mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)-23s: %(name)-15s: %(levelname)-10s: %(message)s'))
    logger.addHandler(fh)
    return logger