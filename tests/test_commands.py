import sublime
from unittest.mock import MagicMock, patch
import word_highlighter.commands as commands
import word_highlighter.core as core
from tests.setup import WordHighlighter_TestCase

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
            mock_window_method.return_value=MagicMock(show_quick_panel=show_quick_panel_mock)
            self.wordHighlighterClearMenu._run()
        self.assertEqual(1, len(show_quick_panel_mock.mock_calls))

    def test_clearing_all_words(self):
        # Add some words and highlight them
        self.set_buffer("word1 word2 word3")
        self.collection._add_word(core.WordHighlight("word1", match_by_word=True))
        self.collection._add_word(core.WordHighlight("word2", match_by_word=True))
        self.collection._add_word(core.WordHighlight("word3", match_by_word=True))
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