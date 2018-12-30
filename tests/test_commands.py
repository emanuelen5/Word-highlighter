import sublime
from unittest.mock import MagicMock, patch
import word_highlighter.commands as commands
import word_highlighter.core as core
import word_highlighter.helpers as helpers
from word_highlighter.tests.setup import SublimeText_TestCase, WordHighlighter_TestCase

def clip(min_val, val, max_val):
    return min(max(min_val, val), max_val)

def region_to_list(region):
    assert isinstance(region, sublime.Region)
    return [region.begin(), region.end()]

def get_scope_color(index):
    return core.SCOPE_COLORS[index % len(core.SCOPE_COLORS)]

class TestHighlighting(SublimeText_TestCase):
    def setUp(self):
        super(TestHighlighting, self).setUp()
        settings = helpers.get_settings()
        settings.set("color_picking_scheme", "CYCLIC_EVEN_ORDERED")

    def get_highlighted_regions(self):
        highlighted_regions = []
        for key in core.SCOPE_COLORS:
            highlighted_regions += self.view.get_regions(key)
        return highlighted_regions

    def check_character(self, c):
        self.set_buffer(c)
        # Select the only character in the buffer
        s = self.view.sel()
        s.clear()
        s.add(sublime.Region(0,1))
        # Highlight the selection
        self.view.run_command("word_highlighter_highlight_instances_of_selection")
        highlighted_regions = self.get_highlighted_regions()
        self.assertEqual(1, len(highlighted_regions), "A word should be highlighted")
        self.assertEqual(region_to_list(sublime.Region(0,1)), region_to_list(highlighted_regions[0]), "The first word should be highlighted")

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

class TestWordHighlighterClearMenu(WordHighlighter_TestCase, core.CollectionableMixin):
    def setUp(self):
        super(TestWordHighlighterClearMenu, self).setUp()
        self.wordHighlighterClearMenu = commands.wordHighlighterClearMenu(self.view)

    def test_quick_panel_is_called(self):
        self.set_buffer("")
        with patch.object(self.wordHighlighterClearMenu.view, "window") as mock_window_method:
            mock_window_method.return_value.show_quick_panel.side_effect=(None)
            self.wordHighlighterClearMenu._run()
        self.assertTrue(mock_window_method.return_value.show_quick_panel.called)

    def test_clearing_all_words(self):
        # Add some words and highlight them
        self.set_buffer("word1 word2 word3")
        self.collection._add_word(core.WordHighlight("word1", match_by_word=True))
        self.collection._add_word(core.WordHighlight("word2", match_by_word=True))
        self.collection._add_word(core.WordHighlight("word3", match_by_word=True))
        self.save_collection()

        # Mocks the quick panel call and returns index of last item
        def show_quick_panel_mock_call__select_last_item(items, callback, *args, selected_index=0, **kwargs):
            return callback(clip(-1, selected_index, len(items)-1))

        # Do the actual testing
        with patch.object(self.wordHighlighterClearMenu.view, "window") as mock_window_method:
            mock_window_method.return_value.show_quick_panel.side_effect = show_quick_panel_mock_call__select_last_item
            self.wordHighlighterClearMenu._run()
        self.assertEqual(4, len(mock_window_method.return_value.show_quick_panel.mock_calls))

class TestWordHighlighterEditRegexp(WordHighlighter_TestCase, core.CollectionableMixin):
    def setUp(self):
        super(TestWordHighlighterEditRegexp, self).setUp()
        self.wordHighlighterEditRegexp = commands.wordHighlighterEditRegexp(self.view)
        # Set collection to point out word
        self.set_buffer("word1 word2 word3")
        self.collection._add_word(core.WordHighlight("word1"))
        self.save_collection()
        self.wordHighlighterEditRegexp.load_collection()
        self.word = self.wordHighlighterEditRegexp.collection.words[0]
        self.view.sel().clear()

    def assertInputNewRegexIsCalled(self):
        with patch.object(self.wordHighlighterEditRegexp, "edit_regex") as mock_input:
            self.wordHighlighterEditRegexp._run()
        self.assertTrue(mock_input.called)

    def test_input_new_regex_is_called_when_selection_in_word(self):
        self.view.sel().add(sublime.Region(1,1))
        self.assertInputNewRegexIsCalled()

    def test_input_new_regex_is_called_when_selection_borders_word(self):
        self.view.sel().add(sublime.Region(0,0))
        self.assertInputNewRegexIsCalled()

    def test_input_new_regex_is_called_when_selection_intersects_word(self):
        self.view.sel().add(sublime.Region(3,10))
        self.assertInputNewRegexIsCalled()

    def test_regex_is_set_on_done_empty(self):
        on_done = self.wordHighlighterEditRegexp.create_on_done(self.word)
        new_regex = "\b"
        on_done(new_regex)
        self.assertEqual(0, len(self.wordHighlighterEditRegexp.collection.words))

    def test_regex_is_set_on_modified(self):
        on_modified = self.wordHighlighterEditRegexp.create_on_modified(self.word)
        new_regex = "word2"
        on_modified(new_regex)
        self.assertEqual(new_regex, self.word.get_regex())

    def test_regex_is_reset_on_canceled(self):
        old_regex = self.word.get_regex()
        on_canceled = self.wordHighlighterEditRegexp.create_on_canceled(self.word)
        self.word.set_regex(old_regex + "_modified")
        on_canceled()
        self.assertEqual(old_regex, self.word.get_regex())

class TestWordHighlighterCreateRegexp(WordHighlighter_TestCase, core.CollectionableMixin):
    def setUp(self):
        super(TestWordHighlighterCreateRegexp, self).setUp()
        self.wordHighlighterCreateRegexp = commands.wordHighlighterCreateRegexp(self.view)
        # Set collection to point out word
        self.set_buffer("word1 word2 word3")
        self.save_collection()
        self.wordHighlighterCreateRegexp.load_collection()

    def test_word_is_added(self):
        with patch.object(self.wordHighlighterCreateRegexp, "edit_regex") as mock_input:
            old_length = len(self.wordHighlighterCreateRegexp.collection.words)
            self.wordHighlighterCreateRegexp._run()
            self.assertTrue(mock_input.called)
            self.assertEqual(old_length+1, len(self.wordHighlighterCreateRegexp.collection.words))

    def test_regex_is_removed_on_canceled(self):
        collection = self.wordHighlighterCreateRegexp.collection
        word = core.WordHighlight("word1")
        collection._add_word(word)
        old_length = len(self.wordHighlighterCreateRegexp.collection.words)
        on_canceled = self.wordHighlighterCreateRegexp.create_on_canceled(word)
        on_canceled()
        self.assertEqual(old_length-1, len(self.wordHighlighterCreateRegexp.collection.words))
