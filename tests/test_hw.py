import sublime
import sys
from unittest import TestCase

version = sublime.version()


# for testing sublime command
class TestWordHighlighter(TestCase):

    def setUp(self):
        self.view = sublime.active_window().new_file()
        # make sure we have a window to work with
        s = sublime.load_settings("Preferences.sublime-settings")
        s.set("close_windows_when_empty", False)

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command("close_file")

    def setText(self, string):
        self.view.run_command("insert", {"characters": string})

    def getRow(self, row):
        return self.view.substr(self.view.line(self.view.text_point(row, 0)))

    # since ST3 uses python 2 and python 2 doesn't support @unittest.skip,
    # we have to do primitive skipping
    if version >= '3000':
        def test_hello_world_st3(self):
            self.setText("hello world")
            first_row = self.getRow(0)
            self.assertEqual(first_row, "hello world")

    def test_hello_world(self):
        self.setText("new ")
        self.setText("hello world")
        first_row = self.getRow(0)
        self.assertEqual(first_row, "new hello world")

    def test_run_internal_function(self):
        test_str = "new text with unique words"
        self.setText(test_str)
        word_highlighter.expand_to_word(self.view, 0)


# for testing internal function
if version < '3000':
    word_highlighter = sys.modules["word_highlighter"]
else:
    word_highlighter = sys.modules["Word-highlighter.word_highlighter"]