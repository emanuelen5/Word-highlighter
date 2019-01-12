import sublime
import unittest
from unittest.mock import MagicMock

from word_highlighter.sublime_plugin import plugin_loaded
plugin_loaded()

import word_highlighter.src.helpers as helpers
