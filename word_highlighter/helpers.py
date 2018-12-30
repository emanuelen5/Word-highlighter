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
    logger.setLevel(logging.DEBUG)

    # Make sure to remove old handlers before adding new one (necessary when reloading package)
    handlers = list(logger.handlers)
    for h in handlers:
        logger.removeHandler(h)
        h.flush()
        h.close()

    # Add new handler
    fh = logging.FileHandler(get_logfile_path(file_name), mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)-23s: %(name)-15s: %(levelname)-10s: %(message)s'))
    logger.addHandler(fh)
    return logger

# Check if the current language is case insensitive (actually just check if its VHDL, since that is the only one I know and care about currently)
# re.compile(string, re.IGNORECASE)
def is_case_insensitive_language(view):
    import re
    syntax_file = view.settings().get("syntax")
    re_case_insensitive_language_files = re.compile(r'(i?)(VHDL)\.sublime-syntax', re.IGNORECASE)
    match = re_case_insensitive_language_files.match(syntax_file)
    return match is not None