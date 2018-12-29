import sys

from . import word_highlighter  # noqa: F402
sys.modules["word_highlighter"] = word_highlighter


import word_highlighter.commands as word_highlighter # noqa: F401

from word_highlighter.commands import update_words_event
from word_highlighter.commands import wordHighlighterClearInstances
from word_highlighter.commands import wordHighlighterClearMenu
from word_highlighter.commands import wordHighlighterHighlightInstancesOfSelection
from word_highlighter.commands import wordHighlighterEditRegexp

__all__ = [
    "update_words_event",
    "wordHighlighterClearInstances",
    "wordHighlighterClearMenu",
    "wordHighlighterHighlightInstancesOfSelection",
    "wordHighlighterEditRegexp",
]