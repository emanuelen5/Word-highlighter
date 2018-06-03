import unittest
import sublime

class TestHighlighting(unittest.TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.view.set_scratch(True)
        self.error_list = []
        self.view.run_command("word_highlighter_clear_instances")

    def tearDown(self):
        self.view.close()

    def check_character(self, c):
        self.view.run_command("overwrite", {"characters": c})
        # Select the only character in the buffer
        s = self.view.sel()
        s.clear()
        s.add(sublime.Region(0,1))
        # Highlight the selection
        self.view.run_command("word_highlighter_highlight_instances_of_selection")
        regions = self.view.get_regions("word_highlighter.color0")
        self.assertEqual([sublime.Region(0,1)], list(regions), "The first word should be highlighted")
        self.view.run_command("word_highlighter_clear_instances")

    def test_highlight_characters(self):
        chars = [chr(i) for i in range(0x20, 0x7f)]
        chars += ['\r', '\n']
        for i, c in enumerate(chars):
            try:
                self.check_character(c)
            except AssertionError as e:
                self.error_list.append(c)
        self.maxDiff = None
        self.assertEqual([], self.error_list, "Non-highlightable characters: Errors for {}/{}".format(len(self.error_list), len(chars)))

## For testing internal functions
import sys
version = sublime.version()
if version < '3000':
    word_highlighter = sys.modules["word_highlighter"]
else:
    word_highlighter = sys.modules["Word-highlighter.word_highlighter"]