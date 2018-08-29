import unittest
import sublime
from unittest.mock import MagicMock, patch

def region_to_list(region):
    assert isinstance(region, sublime.Region)
    return [region.begin(), region.end()]

def get_scope_color(index):
    return word_highlighter.SCOPE_COLORS[index % len(word_highlighter.SCOPE_COLORS)]

class SublimeText_TestCase(unittest.TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.view.set_scratch(True)
        self.error_list = []
        self.maxDiff = None # Verbose printouts if error

    def tearDown(self):
        self.view.close()

    def set_buffer(self, string):
        self.view.run_command("overwrite", {"characters": string})

class WordHighlighter_TestCase(SublimeText_TestCase):
    def setUp(self):
        super(WordHighlighter_TestCase, self).setUp()
        self.collection = word_highlighter.WordHighlightCollection(self.view)
        # Need to set up a saved serialized wordhighlighter_collection to make it in the same state as main script
        s = self.view.settings()
        self.view.settings().set("wordhighlighter_collection", self.collection.dumps())

class TestHighlighting(SublimeText_TestCase):
    def setUp(self):
        super(TestHighlighting, self).setUp()
        settings = sublime.load_settings("word_highlighter.sublime-settings")
        settings.set("color_picking_scheme", "CYCLIC_EVEN_ORDERED")

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
        scheme = word_highlighter.get_color_picking_scheme("CYCLIC")
        for i in range(100):
            try:
                self.assertEqual(get_scope_color(i), self.collection.get_next_word_color(scheme).color_string, "Error for color {}".format(i))
            except AssertionError as ae:
                self.error_list.append(ae)
        self.assertEqual([], self.error_list)

    def test_cyclic_even_ordered(self):
        scheme = word_highlighter.get_color_picking_scheme("CYCLIC_EVEN")
        for i in range(100):
            try:
                self.assertEqual(get_scope_color(i), self.collection.get_next_word_color(scheme).color_string, "Error for color {}".format(i))
            except AssertionError as ae:
                self.error_list.append(ae)
        self.assertEqual([], self.error_list)

    def test_get_color_picking_schemes_invalid(self):
        scheme_string = "Not a valid color picking scheme string"
        scheme = word_highlighter.get_color_picking_scheme(scheme_string)
        self.assertIsInstance(scheme, word_highlighter.ColorType)
        self.assertNotIn(scheme_string, word_highlighter.color_schemes, "Does not already exist as a color picking scheme")
        self.assertIn(scheme.color_string, word_highlighter.color_schemes, "Resolves to correct color picking scheme")

    def test_get_color_picking_schemes(self):
        for scheme_string in word_highlighter.color_schemes.keys():
            self.assertIs(word_highlighter.color_schemes[scheme_string], word_highlighter.get_color_picking_scheme(scheme_string))

class TestCollection(WordHighlighter_TestCase):
    def test_clear_words(self):
        word = word_highlighter.WordHighlight("asd", False)
        self.collection.toggle_word(word)
        self.collection.clear()
        self.assertEqual([], self.collection.words)

class TestExpandToWordSimple(SublimeText_TestCase):
    def test_start_of_word(self):
        self.set_buffer("word")
        self.region = word_highlighter.expand_to_word(self.view, 0)
        self.assertEqual(sublime.Region(0, 4), self.region)

    def test_end_of_word(self):
        self.set_buffer("word")
        self.region = word_highlighter.expand_to_word(self.view, 4)
        self.assertEqual(sublime.Region(0, 4), self.region)

    def test_middle_of_word(self):
        self.set_buffer("word")
        self.region = word_highlighter.expand_to_word(self.view, 1)
        self.assertEqual(sublime.Region(0, 4), self.region)

    def test_no_word(self):
        self.set_buffer(" ")
        self.region = word_highlighter.expand_to_word(self.view, 1)
        self.assertEqual(sublime.Region(1, 1), self.region)

class TestRestoreCollection(SublimeText_TestCase):
    def setUp(self):
        super(TestRestoreCollection, self).setUp()
        self.scope_name = self.key_name = word_highlighter.SCOPE_COLORS[0]

    def tearDown(self):
        super(TestRestoreCollection, self).tearDown()
        self.view.erase_regions(self.scope_name)

    def test_whole_word(self):
        self.set_buffer("word")
        self.view.add_regions(self.key_name, [sublime.Region(0,4)], self.scope_name)
        collection = word_highlighter.restore_collection(self.view)
        self.assertEqual(1, len(collection.words))
        word = collection.words[0]
        self.assertIsInstance(word, word_highlighter.WordHighlight)
        self.assertEqual(self.scope_name, word.get_scope())
        self.assertEqual(self.key_name, word.get_key())
        self.assertEqual(True, word.matches_by_word())

    def test_partial_word(self):
        self.set_buffer("word")
        self.view.add_regions(self.key_name, [sublime.Region(0,3)], self.scope_name)
        collection = word_highlighter.restore_collection(self.view)
        self.assertEqual(1, len(collection.words))
        word = collection.words[0]
        self.assertIsInstance(word, word_highlighter.WordHighlight)
        self.assertEqual(self.scope_name, word.get_scope())
        self.assertEqual(self.key_name, word.get_key())
        self.assertEqual(False, word.matches_by_word())

def clip(min_val, val, max_val):
    return min(max(min_val, val), max_val)

class TestWordHighlighterClearMenu(WordHighlighter_TestCase):
    def setUp(self):
        super(TestWordHighlighterClearMenu, self).setUp()
        self.wordHighlighterClearMenu = word_highlighter.wordHighlighterClearMenu(self.view)

    def test_quick_panel_is_called(self):
        self.set_buffer("")
        with patch.object(self.wordHighlighterClearMenu.view, "window") as mock_window_method:
            show_quick_panel_mock = MagicMock(side_effect=(None))
            mock_window_method.return_value=MagicMock(show_quick_panel=show_quick_panel_mock)
            self.wordHighlighterClearMenu._run()
        self.assertEqual(1, len(show_quick_panel_mock.mock_calls))

    def test_clearing_all_words(self):
        # Add some words and highlight them
        self.set_buffer("word1 word2 word3")
        self.collection._add_word(word_highlighter.WordHighlight("word1", match_by_word=True))
        self.collection._add_word(word_highlighter.WordHighlight("word2", match_by_word=True))
        self.collection._add_word(word_highlighter.WordHighlight("word3", match_by_word=True))
        self.view.settings().set("wordhighlighter_collection", self.collection.dumps())

        # Mocks the quick panel call and returns index of last item
        def show_quick_panel_mock_call__select_last_item(items, callback, *args, selected_index=0, **kwargs):
            return callback(clip(-1, selected_index, len(items)-1))

        # Do the actual testing
        with patch.object(self.wordHighlighterClearMenu.view, "window") as mock_window_method:
            show_quick_panel_mock = MagicMock(side_effect=show_quick_panel_mock_call__select_last_item)
            mock_window_method.return_value=MagicMock(show_quick_panel=show_quick_panel_mock)
            self.wordHighlighterClearMenu._run()
        self.assertEqual(4, len(show_quick_panel_mock.mock_calls))

## For testing internal functions
import sys
version = sublime.version()
if version < '3000':
    word_highlighter = sys.modules["word_highlighter"]
else:
    word_highlighter = sys.modules["Word-highlighter.word_highlighter"]