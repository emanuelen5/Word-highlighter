import unittest

import sublime

class TestHighlighting(unittest.TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.view.set_scratch(True)
        self.error_list = []

    def tearDown(self):
        self.view.close()
        self.maxDiff = None
        self.assertEqual([], self.error_list, "List of errors during run")

    def check_character(self, c):
        self.view.run_command("overwrite", {"characters": c})
        raise AssertionError("Not implemented yet")

    def test_highlight_characters(self):
        chars = [chr(i) for i in range(0x20, 0x7f)]
        chars += ['\r', '\n']
        for i, c in enumerate(chars):
            try:
                self.check_character(c)
            except AssertionError as e:
                self.error_list.append("Highlighting for '{}' failed - {}".format(c, e))

## For testing internal functions
import sys
version = sublime.version()
if version < '3000':
    word_highlighter = sys.modules["word_highlighter"]
else:
    word_highlighter = sys.modules["Word-highlighter.word_highlighter"]