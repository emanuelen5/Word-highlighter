# Entry point for Sublime text when loading the plugin
import word_highlighter # This corresponds to this plugin's root directory

def plugin_loaded():
    word_highlighter.src.helpers.plugin_loaded()
    word_highlighter.src.commands.plugin_loaded()
    word_highlighter.src.core.plugin_loaded()

from .src.commands import update_words_event
from .src.commands import update_color_scheme_event
from .src.commands import wordHighlighterClearInstances
from .src.commands import wordHighlighterClearMenu
from .src.commands import wordHighlighterHighlightInstancesOfSelection
from .src.commands import wordHighlighterEditRegexp
from .src.commands import wordHighlighterCreateRegexp
from .src.commands import wordHighlighterEditRegexpMenu
from .src.commands import wordHighlighterWordColorMenu

# sublime_plugin classes must be exposed here (or at least on this level) to be registered in Sublime Text
__all__ = [
    "update_words_event",
    "update_color_scheme_event",
    "wordHighlighterClearInstances",
    "wordHighlighterClearMenu",
    "wordHighlighterHighlightInstancesOfSelection",
    "wordHighlighterEditRegexp",
    "wordHighlighterCreateRegexp",
    "wordHighlighterEditRegexpMenu",
    "wordHighlighterWordColorMenu",
]