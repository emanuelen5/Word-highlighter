import unittest
import sublime

def region_to_list(region):
    assert isinstance(region, sublime.Region)
    return [region.begin(), region.end()]

class SublimeText_TestCase(unittest.TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.view.set_scratch(True)
        self.error_list = []

    def tearDown(self):
        self.view.close()

    def set_buffer(self, string):
        self.view.run_command("overwrite", {"characters": string})

class WordHighlighter_TestCase(SublimeText_TestCase):
    def setUp(self):
        super(WordHighlighter_TestCase, self).setUp()
        self.collection = word_highlighter.WordHighlightCollection(self.view)

class TestHighlighting(SublimeText_TestCase):
    def check_character(self, c):
        self.set_buffer(c)
        # Select the only character in the buffer
        s = self.view.sel()
        s.clear()
        s.add(sublime.Region(0,1))
        # Highlight the selection
        self.view.run_command("word_highlighter_highlight_instances_of_selection")
        regions = self.view.get_regions(word_highlighter.SCOPE_COLORS[0])
        self.assertEqual(1, len(regions), "A word should be highlighted")
        self.assertEqual(region_to_list(sublime.Region(0,1)), region_to_list(regions[0]), "The first word should be highlighted")

    def test_highlight_characters(self):
        chars = [chr(i) for i in range(0x20, 0x7f)]
        chars += ['\r', '\n']
        for i, c in enumerate(chars):
            try:
                self.view.run_command("word_highlighter_clear_instances")
                self.check_character(c)
            except AssertionError as e:
                self.error_list.append("'{}' - Error: '{}'".format(c,e))
        self.assertEqual([], self.error_list, "Non-highlightable characters: Errors for {}/{}".format(len(self.error_list), len(chars)))

class TestColorPickingSchemes(WordHighlighter_TestCase):
    def test_cyclic(self):
        for i in range(100):
            color_name = word_highlighter.SCOPE_COLORS[i % len(word_highlighter.SCOPE_COLORS)]
            expected_color = color_name
            self.assertEqual(expected_color, self.collection.get_next_word_color("CYCLIC").color_string, "Error for color {}".format(i))

## For testing internal functions
import sys
version = sublime.version()
if version < '3000':
    word_highlighter = sys.modules["word_highlighter"]
else:
    word_highlighter = sys.modules["Word-highlighter.word_highlighter"]