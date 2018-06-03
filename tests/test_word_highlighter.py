import unittest
#from ..word_highlighter import ...
import sublime
import sublime_plugin

class TestHighlighting(unittest.TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.view.set_scratch(True)
        self.error_list = []

    def tearDown(self):
        self.view.close()
        self.assertEqual([], self.error_list)

    def check_character(self, c):
        self.view.run_command("test_word_highlighter_add_character", c)
        self.assertTrue(False, "Not implemented yet")

    def test_highlight_characters(self):
        chars = ["<", ">", "'"]
        for i, c in enumerate(chars):
            try:
                self.check_character(c)
            except AssertionError as e:
                self.error_list.append("{} : Highlighting for '{}' ".format(e, c))

