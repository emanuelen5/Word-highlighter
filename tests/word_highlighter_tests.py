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

class TestWordHighlighterAddCharacterCommand(sublime_plugin.TextCommand):
    def run(edit, c):
        print("TestWordHighlighterAddCharacterCommand.run()")
        self.view.insert(edit, 0, c)

def create_test_suite():
    test_cases = (TestHighlighting, )
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

def main():
    unittest.TextTestRunner().run(create_test_suite())