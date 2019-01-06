import sublime
from unittest.mock import patch

from word_highlighter.sublime_plugin import plugin_loaded
plugin_loaded()

import word_highlighter.src.core as core
from word_highlighter.src.tests.setup import SublimeText_TestCase, WordHighlighter_TestCase

class TestColorPickingSchemes(WordHighlighter_TestCase):
    def setUp(self):
        super(TestColorPickingSchemes, self).setUp()
        self.cyclic_scheme              = core.get_color_picking_scheme("CYCLIC")
        self.cyclic_even_scheme         = core.get_color_picking_scheme("CYCLIC_EVEN")
        self.cyclic_even_ordered_scheme = core.get_color_picking_scheme("CYCLIC_EVEN_ORDERED")
        self.random_scheme              = core.get_color_picking_scheme("RANDOM")
        self.random_even_scheme         = core.get_color_picking_scheme("RANDOM_EVEN")

    def get_color_index(self, word):
        assert isinstance(word, core.ColorType), "get_color_index: word is not a ColorType"
        return core.SCOPE_COLORS.index(word.color_string)

    def test_cyclic(self):
        for i in range(self.color_count):
            try:
                self.assertEqual(i, self.get_color_index(self.collection.get_next_word_color(self.cyclic_scheme)), "Error for color {}".format(i))
            except AssertionError as ae:
                self.error_list.append(ae)
        self.assertEqual([], self.error_list)

    def test_cyclic_even(self):
        for i in range(self.color_count):
            try:
                self.assertEqual(i, self.get_color_index(self.collection.get_next_word_color(self.cyclic_even_scheme)), "Error for color {}".format(i))
            except AssertionError as ae:
                self.error_list.append(ae)
        self.assertEqual([], self.error_list)

    def test_random(self):
        self.is_static = True
        self.is_statically_incrementing = True
        self.color_bins = [0] * self.color_count
        self.incrementing_bins = [0] * self.color_count

        def index_diff(old_index, new_index):
            return (new_index - old_index) % self.color_count

        iterations_per_color = 1000
        iterations = iterations_per_color * self.color_count
        new_index = self.get_color_index(self.collection.get_next_word_color(self.random_scheme))
        old_index = self.get_color_index(self.collection.get_next_word_color(self.random_scheme))
        old_diff = index_diff(old_index, new_index)
        for i in range(iterations):
            new_index = self.get_color_index(self.collection.get_next_word_color(self.random_scheme))
            new_diff = index_diff(old_index, new_index)
            self.color_bins[new_index] += 1
            self.incrementing_bins[new_diff] += 1
            self.is_static = self.is_static and (old_index == new_index)
            self.is_statically_incrementing = self.is_statically_incrementing and (old_diff == new_diff)
            old_index = new_index
            old_diff = new_diff

        self.assertFalse(self.is_static)
        self.assertFalse(self.is_statically_incrementing)
        with self.assertRaises(ValueError):
            self.color_bins.index(0)
        with self.assertRaises(ValueError):
            self.incrementing_bins.index(0)

    def test_color_picking_affected_by_frequencies(self):
        self.collection.next_color_index() # Make sure that the first index is already taken
        with patch.object(self.collection, "color_frequencies") as color_frequencies_mock:
            # Fake that all colors are taken except for the first
            frequencies = [1] * self.color_count
            color_frequencies_mock.return_value = frequencies
            frequencies[0] = 0
            self.assertEqual(1, self.get_color_index(self.collection.get_next_word_color(self.cyclic_scheme)), "Cyclic should always take the next irrespective of frequencies")
            self.assertEqual(0, self.get_color_index(self.collection.get_next_word_color(self.cyclic_even_scheme)), "Even schemes take the least occuring color")
            self.assertEqual(0, self.get_color_index(self.collection.get_next_word_color(self.cyclic_even_ordered_scheme)), "Even schemes take the least occuring color")
            self.assertEqual(0, self.get_color_index(self.collection.get_next_word_color(self.random_even_scheme)), "Even schemes take the least occuring color")
            frequencies[1] = 0
            self.assertEqual(0, self.get_color_index(self.collection.get_next_word_color(self.cyclic_even_ordered_scheme)), "Ordered schemes take the first least occuring color")
            self.assertEqual(1, self.get_color_index(self.collection.get_next_word_color(self.cyclic_even_scheme)), "Not ordered schemes take the next least occuring color")

    def test_get_color_picking_schemes_invalid(self):
        scheme_string = "Not a valid color picking scheme string"
        scheme = core.get_color_picking_scheme(scheme_string)
        self.assertIsInstance(scheme, core.ColorType)
        self.assertNotIn(scheme_string, core.color_schemes, "Does not already exist as a color picking scheme")
        self.assertIn(scheme.color_string, core.color_schemes, "Resolves to correct color picking scheme")

    def test_get_color_picking_schemes(self):
        for scheme_string in core.color_schemes.keys():
            self.assertIs(core.color_schemes[scheme_string], core.get_color_picking_scheme(scheme_string))

class TestCollection(WordHighlighter_TestCase):
    def test_toggle_word(self):
        word = core.WordHighlight("asd", match_by_word=False)
        self.collection.toggle_word(word)
        self.assertEqual([word], self.collection.words)
        self.collection.toggle_word(word)
        self.assertEqual([], self.collection.words)

    def test_clear_words(self):
        word = core.WordHighlight("asd", match_by_word=False)
        self.collection.toggle_word(word)
        self.collection.clear()
        self.assertEqual([], self.collection.words)

class TestExpandToWordSimple(SublimeText_TestCase):
    def test_start_of_word(self):
        self.set_buffer("word")
        self.region = core.expand_to_word(self.view, 0)
        self.assertEqual(sublime.Region(0, 4), self.region)

    def test_end_of_word(self):
        self.set_buffer("word")
        self.region = core.expand_to_word(self.view, 4)
        self.assertEqual(sublime.Region(0, 4), self.region)

    def test_middle_of_word(self):
        self.set_buffer("word")
        self.region = core.expand_to_word(self.view, 1)
        self.assertEqual(sublime.Region(0, 4), self.region)

    def test_no_word(self):
        self.set_buffer(" ")
        self.region = core.expand_to_word(self.view, 1)
        self.assertEqual(sublime.Region(1, 1), self.region)

class TestRestoreCollection(SublimeText_TestCase):
    def setUp(self):
        super(TestRestoreCollection, self).setUp()
        self.scope_name = self.key_name = core.SCOPE_COLORS[0]

    def tearDown(self):
        super(TestRestoreCollection, self).tearDown()
        self.view.erase_regions(self.scope_name)

    def test_whole_word(self):
        self.set_buffer("word")
        self.view.add_regions(self.key_name, [sublime.Region(0,4)], self.scope_name)
        collection = core.WordHighlightCollection.restore(self.view)
        self.assertEqual(1, len(collection.words))
        word = collection.words[0]
        self.assertIsInstance(word, core.WordHighlight)
        self.assertEqual(self.scope_name, word.get_scope())
        self.assertEqual(self.key_name, word.get_key())

    def test_partial_word(self):
        self.set_buffer("word")
        self.view.add_regions(self.key_name, [sublime.Region(0,3)], self.scope_name)
        collection = core.WordHighlightCollection.restore(self.view)
        self.assertEqual(1, len(collection.words))
        word = collection.words[0]
        self.assertIsInstance(word, core.WordHighlight)
        self.assertEqual(self.scope_name, word.get_scope())
        self.assertEqual(self.key_name, word.get_key())
