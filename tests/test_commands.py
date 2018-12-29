import sublime
from unittest.mock import MagicMock, patch
import word_highlighter.commands as commands
import word_highlighter.core as core
from word_highlighter.tests.setup import WordHighlighter_TestCase

def clip(min_val, val, max_val):
    return min(max(min_val, val), max_val)

class TestWordHighlighterClearMenu(WordHighlighter_TestCase):
    def setUp(self):
        super(TestWordHighlighterClearMenu, self).setUp()
        self.wordHighlighterClearMenu = commands.wordHighlighterClearMenu(self.view)

    def test_quick_panel_is_called(self):
        self.set_buffer("")
        with patch.object(self.wordHighlighterClearMenu.view, "window") as mock_window_method:
            show_quick_panel_mock = MagicMock(side_effect=(None))
            mock_window_method.return_value = MagicMock(show_quick_panel=show_quick_panel_mock)
            self.wordHighlighterClearMenu._run()
        self.assertEqual(1, len(show_quick_panel_mock.mock_calls))

    def test_clearing_all_words(self):
        # Add some words and highlight them
        self.set_buffer("word1 word2 word3")
        self.collection._add_word(core.WordHighlight("word1", match_by_word=True))
        self.collection._add_word(core.WordHighlight("word2", match_by_word=True))
        self.collection._add_word(core.WordHighlight("word3", match_by_word=True))
        self.collection.save()

        # Mocks the quick panel call and returns index of last item
        def show_quick_panel_mock_call__select_last_item(items, callback, *args, selected_index=0, **kwargs):
            return callback(clip(-1, selected_index, len(items)-1))

        # Do the actual testing
        with patch.object(self.wordHighlighterClearMenu.view, "window") as mock_window_method:
            show_quick_panel_mock = MagicMock(side_effect=show_quick_panel_mock_call__select_last_item)
            mock_window_method.return_value=MagicMock(show_quick_panel=show_quick_panel_mock)
            self.wordHighlighterClearMenu._run()
        self.assertEqual(4, len(show_quick_panel_mock.mock_calls))

class TestWordHighlighterEditRegexp(WordHighlighter_TestCase):
    def setUp(self):
        super(TestWordHighlighterEditRegexp, self).setUp()
        self.wordHighlighterEditRegexp = commands.wordHighlighterEditRegexp(self.view)
        # Set collection to point out word
        self.set_buffer("word1 word2 word3")
        self.collection._add_word(core.WordHighlight("word1"))
        self.collection.save()
        self.view.sel().clear()

    def assertInputNewRegexIsCalled(self):
        with patch.object(self.wordHighlighterEditRegexp, "input_new_regex") as mock_input_method:
            self.wordHighlighterEditRegexp._run()
        self.assertTrue(mock_input_method.called)

    def test_input_new_regex_is_called_when_selection_in_word(self):
        self.view.sel().add(sublime.Region(1,1))
        self.assertInputNewRegexIsCalled()

    def test_input_new_regex_is_called_when_selection_borders_word(self):
        self.view.sel().add(sublime.Region(0,0))
        self.assertInputNewRegexIsCalled()

    def test_input_new_regex_is_called_when_selection_intersects_word(self):
        self.view.sel().add(sublime.Region(3,10))
        self.assertInputNewRegexIsCalled()

    def test_input_panel_is_called(self):
        with patch.object(self.wordHighlighterEditRegexp.view, "window") as mock_window_method:
            show_input_panel_mock = MagicMock(side_effect=(None))
            mock_window_method.return_value = MagicMock(show_input_panel=show_input_panel_mock)
            word = self.collection.words[0]
            self.wordHighlighterEditRegexp.input_new_regex(word)
        self.assertTrue(show_input_panel_mock.called)
