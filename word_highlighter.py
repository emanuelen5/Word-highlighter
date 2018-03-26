import sublime
import sublime_plugin

# Add some base colors to use for selections (perhaps read from settings file)
SCOPE_COLORS = ["word_highlighter.color{}".format(i) for i in range(10)]

# Check that select bits are set
def bits_set(value, *bits):
    from functools import reduce
    bit_mask = reduce(lambda x,y: x | y, bits)
    return (value & bit_mask) == bit_mask

# Check that select bits are not set
def bits_not_set(value, *bits):
    from functools import reduce
    bit_mask = reduce(lambda x,y: x | y, bits)
    return (value & bit_mask) == 0

## Define some color constants
class ColorType(object):
    def __init__(self, color_string):
        self.color_string = color_string

    def __eq__(self, right):
        return self.color_string == right.color_string

UNSPECIFIED_COLOR = ColorType("UNSPECIFIED_COLOR")
NEXT_COLOR        = ColorType("NEXT_COLOR")
RANDOM_COLOR      = ColorType("RANDOM_COLOR")

# Instances that combine a word with a color scope
class WordHighlight(object):
    def __init__(self, word, color=UNSPECIFIED_COLOR):
        assert isinstance(word, str)
        assert isinstance(color, ColorType)
        import random
        self.word = word
        if color == RANDOM_COLOR:
            color = SCOPE_COLORS[random.rand(len(SCOPE_COLORS))]
        self.color = color

    def get_key(self):
        return self.color.color_string

    def get_scope(self):
        return self.color.color_string

    def __eq__(self, right):
        assert isinstance(right, WordHighlight)
        return self.word == right.word and (self.color == UNSPECIFIED_COLOR or self.color == right.color)

class WordHighlightCollection(object):
    """Keeps track of the highlighted words"""

    def __init__(self, view):
        self.color_index = 0
        self.words = []
        self.view = view

    def has_word(self, word, color=UNSPECIFIED_COLOR):
        found_word = self.get_word_highlight(word)
        if color == UNSPECIFIED_COLOR:
            return found_word is not None
        else:
            return found_word.color == color

    def get_word_highlight(self, word):
        assert isinstance(word, str)
        for w in self.words:
            if w.word == word: return w
        return None

    def update(self):
        import re
        for w in self.words:
            pattern = w.word
            escaped_pattern = re.escape(pattern)
            regions = self.view.find_all(escaped_pattern)
            self.view.add_regions(w.get_key(), regions, w.get_scope())

        for w in self.words:
            print("Used word: {}, scope: {}".format(w.word, w.get_scope()))

    # Check if the word exists, then remove it from the stack, otherwise add it
    def toggle_word(self, word, color=UNSPECIFIED_COLOR):
        if self.has_word(word):
            self._remove_word(word)
        elif self.get_word_highlight(word):
            self._remove_word(word)
            self._add_word(word, color)
        else:
            self._add_word(word, color)

    def _add_word(self, word, color=UNSPECIFIED_COLOR):
        assert isinstance(color, ColorType)
        assert isinstance(word, str)
        if color == UNSPECIFIED_COLOR:
            color = NEXT_COLOR
        self.words.append(WordHighlight(word, color))
        self.color_index = (self.color_index + 1) % len(SCOPE_COLORS)

    def _remove_word(self, word, color=UNSPECIFIED_COLOR):
        assert isinstance(color, ColorType)
        assert isinstance(word, str)
        if self.has_word(word, color):
            self.view.erase_regions(self.get_word_highlight(word).get_key())
            self.words.remove(WordHighlight(word))

class wordHighlighterHighlightInstancesOfSelection(sublime_plugin.TextCommand):
    """
    Highlights all instances of a specific word that is selected
    """
    def __init__(self, view):
        self.view = view
        self.collection = WordHighlightCollection(view)

    # Expand the point to a region that contains a word, or an empty Region if 
    # the point is not placed at a word.
    def expand_to_word(self, point):
        classification = self.view.classify(point)
        # If start of word, expand right to end of word
        if bits_set(classification, sublime.CLASS_WORD_START):
            print("At start of word!")
            back_stop = point
            forward_stop = self.view.find_by_class(point, forward=True, classes=sublime.CLASS_WORD_END)
            return sublime.Region(back_stop, forward_stop)
        # If end of word, expand left to start of word
        elif bits_set(classification, sublime.CLASS_WORD_END):
            print("At end of word!")
            back_stop = self.view.find_by_class(point, forward=False, classes=sublime.CLASS_WORD_START)
            forward_stop = point
            return sublime.Region(back_stop, forward_stop)
        # Else, expand left and right until hitting word start/end or punctuation.
        # If the word start and end matches first, in right order use as word
        else:
            # Stop for anything but subwords
            stop_classes = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_START | sublime.CLASS_PUNCTUATION_END | sublime.CLASS_LINE_START | sublime.CLASS_LINE_END | sublime.CLASS_EMPTY_LINE
            back_stop = self.view.find_by_class(point, forward=False, classes=stop_classes)
            forward_stop = self.view.find_by_class(point, forward=True, classes=stop_classes)
            r = sublime.Region(back_stop, forward_stop)
            # Check that the found Region contains a word
            if bits_set(self.view.classify(back_stop), sublime.CLASS_WORD_START) and bits_set(self.view.classify(forward_stop), sublime.CLASS_WORD_END):
                # Valid word!
                return r
            else:
                print("Expanded word is invalid: '{}'".format(self.view.substr(r)))
                return sublime.Region(0, 0) # Empty region

    # Check if the current language is case insensitive (actually just check if its VHDL, since that is the only one I know and care about currently)
    # re.compile(string, re.IGNORECASE)
    def is_case_insensitive_language(self):
        import re
        syntax_file = self.view.settings().get("syntax")
        re_case_insensitive_language_files = re.compile(r'(i?)(VHDL)\.sublime-syntax')
        matches_case_insensitive_language = re_case_insensitive_language_files.match(syntax_file) is not None
        return matches_case_insensitive_language

    def run(self, edit):
        text_selections = []
        for s in self.view.sel():
            # Expand empty selections to words
            if s.empty():
                r = self.expand_to_word(s.begin())
                # Append the word if it is not empty
                txt = self.view.substr(r)
                if txt != '':
                    print("Expanded word is valid: '{}'".format(txt))
                    text_selections.append(txt)
            # Keep non-empty selections as-is
            else:
                text_selections.append(self.view.substr(s))
        # Get unique items
        text_selections = list(set(text_selections))

        print("text_selections: " + str(text_selections))

        # Find all instances of each selection
        for pattern in text_selections:
            self.collection.toggle_word(pattern)
            self.collection.update()

        # TODO:
        # 1. Get a unique color association for each selection
        # 2. Find all of the matching words
        # 3. Use add_region() to set the scope for the regions
        # 4. Save the words that have been highlighter
        # 5. Update the highlighted regions if they are edited