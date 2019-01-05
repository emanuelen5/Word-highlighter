from . import helpers, commands, core

def plugin_loaded():
    helpers.plugin_loaded()
    commands.plugin_loaded()
    core.plugin_loaded()