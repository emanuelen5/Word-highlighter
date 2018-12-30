import sys

from . import word_highlighter  # noqa: F402
sys.modules["word_highlighter"] = word_highlighter

from word_highlighter.commands import init as commands_init
from word_highlighter.commands import update_words_event
from word_highlighter.commands import wordHighlighterClearInstances
from word_highlighter.commands import wordHighlighterClearMenu
from word_highlighter.commands import wordHighlighterHighlightInstancesOfSelection
from word_highlighter.commands import wordHighlighterEditRegexp

def plugin_loaded():
    commands_init()

__all__ = [
    "update_words_event",
    "wordHighlighterClearInstances",
    "wordHighlighterClearMenu",
    "wordHighlighterHighlightInstancesOfSelection",
    "wordHighlighterEditRegexp",
]