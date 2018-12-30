import sys

from . import word_highlighter  # noqa: F402
sys.modules["word_highlighter"] = word_highlighter

from word_highlighter.commands import update_words_event
from word_highlighter.commands import update_color_scheme_event
from word_highlighter.commands import wordHighlighterClearInstances
from word_highlighter.commands import wordHighlighterClearMenu
from word_highlighter.commands import wordHighlighterHighlightInstancesOfSelection
from word_highlighter.commands import wordHighlighterEditRegexp

def plugin_loaded():
    word_highlighter.commands.plugin_loaded()
    word_highlighter.core.plugin_loaded()
    word_highlighter.helpers.plugin_loaded()

__all__ = [
    "update_words_event",
    "update_color_scheme_event",
    "wordHighlighterClearInstances",
    "wordHighlighterClearMenu",
    "wordHighlighterHighlightInstancesOfSelection",
    "wordHighlighterEditRegexp",
]