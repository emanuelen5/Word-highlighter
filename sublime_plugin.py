from .src import helpers, commands, core

def plugin_loaded():
    helpers.plugin_loaded()
    commands.plugin_loaded()
    core.plugin_loaded()

from .src.commands import WordHighlighterUpdateHighlightsEvent
from .src.commands import WordHighlighterUpdateColorSchemeEvent
from .src.commands import WordHighlighterClearInstances
from .src.commands import WordHighlighterClearMenu
from .src.commands import WordHighlighterHighlightInstancesOfSelection
from .src.commands import WordHighlighterEditRegexp
from .src.commands import WordHighlighterCreateRegexp
from .src.commands import WordHighlighterEditRegexpMenu
from .src.commands import WordHighlighterWordColorMenu

# sublime_plugin classes must be exposed here (or at least on this level) to be registered in Sublime Text
__all__ = [
    "WordHighlighterUpdateHighlightsEvent",
    "WordHighlighterUpdateColorSchemeEvent",
    "WordHighlighterClearInstances",
    "WordHighlighterClearMenu",
    "WordHighlighterHighlightInstancesOfSelection",
    "WordHighlighterEditRegexp",
    "WordHighlighterCreateRegexp",
    "WordHighlighterEditRegexpMenu",
    "WordHighlighterWordColorMenu",
]