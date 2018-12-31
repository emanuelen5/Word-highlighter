import sys

from . import word_highlighter  # noqa: F402
sys.modules["word_highlighter"] = word_highlighter

from word_highlighter.commands import update_words_event
from word_highlighter.commands import update_color_scheme_event
from word_highlighter.commands import wordHighlighterClearInstances
from word_highlighter.commands import wordHighlighterClearMenu
from word_highlighter.commands import wordHighlighterHighlightInstancesOfSelection
from word_highlighter.commands import wordHighlighterEditRegexp
from word_highlighter.commands import wordHighlighterCreateRegexp
from word_highlighter.commands import wordHighlighterEditRegexpMenu

def plugin_loaded():
    word_highlighter.commands.plugin_loaded()
    word_highlighter.core.plugin_loaded()
    word_highlighter.helpers.plugin_loaded()

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
]