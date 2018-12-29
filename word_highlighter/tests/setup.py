import unittest
import sublime
import word_highlighter.core as core

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
        self.collection = core.WordHighlightCollection(self.view)
        # Need to set up a saved serialized wordhighlighter_collection to make it in the same state as main script
        s = self.view.settings()
        self.view.settings().set("wordhighlighter_collection", self.collection.dumps())
        self.color_count = len(core.SCOPE_COLORS)