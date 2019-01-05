import sublime
import logging
import inspect

import os

class Dirs(object):
    pass
dirs = Dirs()

def plugin_loaded():
    dirs.word_highlighter = os.path.join(sublime.packages_path(), "word_highlighter")
    dirs.logs = os.path.join(dirs.word_highlighter, 'logs')
    dirs.color_schemes = os.path.join(dirs.word_highlighter, "Color Schemes")

# Check that select bits are set
def bits_set(value, *bits):
    from functools import reduce
    bit_mask = reduce(lambda x,y: x | y, bits)
    return (value & bit_mask) == bit_mask

def get_logfile_path(filename):
    basename = os.path.splitext(os.path.basename(filename))[0]
    log_file = os.path.join(dirs.logs, basename + ".log")
    os.makedirs(dirs.logs, exist_ok=True)
    return log_file

def get_settings():
    return sublime.load_settings("word_highlighter.sublime-settings")

def get_logger(module_name=None, file_name=None):

    if module_name is None or file_name is None:
        caller_frame = inspect.stack()[1]

    if file_name is None:
        file_name = caller_frame[1]
    if module_name is None:
        module_name = os.path.splitext(os.path.basename(file_name))[0]

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

# Check if the current language is case sensitive (actually just check if it's not VHDL, since that is the only one I know and care about currently)
def is_case_sensitive_language(view):
    import re
    syntax_file = view.settings().get("syntax")
    case_insensitive_languages = ("VHDL", )
    for lang in case_insensitive_languages:
        re_lang_file = "^" + lang + r'\.sublime-syntax'
        match = re.compile(re_lang_file, re.IGNORECASE).match(syntax_file)
        if match:
            return False
    return True