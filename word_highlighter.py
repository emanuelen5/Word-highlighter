import sublime
import sublime_plugin

import threading

import os
dir_path = os.path.dirname(os.path.realpath(__file__))
log_file = os.path.join(dir_path, "word_highlighter.log")

import logging
logging.basicConfig(filename=log_file, format='%(asctime)-23s: %(name)-15s: %(levelname)-10s: %(message)s', filemode='w', level=logging.DEBUG)
logging.info("Starting module")

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
        if isinstance(right, str):
            return self.color_string == right
        elif isinstance(right, ColorType):
            return self.color_string == right.color_string
        else:
            raise ValueError("Illegal type in comparison")

    def __str__(self):
        return self.color_string

UNSPECIFIED_COLOR = ColorType("UNSPECIFIED_COLOR")
NEXT_COLOR        = ColorType("NEXT_COLOR")
RANDOM_COLOR      = ColorType("RANDOM_COLOR")

# Instances that combine a word with a color scope
class WordHighlight(object):
    def __init__(self, word, match_by_word, color=UNSPECIFIED_COLOR):
        import random
        if color is RANDOM_COLOR:
            color = SCOPE_COLORS[random.rand(len(SCOPE_COLORS))]

        assert isinstance(word, str)
        if isinstance(color, str):
            color = ColorType(color)
        elif not isinstance(color, ColorType):
            raise ValueError("Invalid color type")
        self.word = word
        self.match_by_word = match_by_word
        self.color = color

    def get_regex(self):
        import re
        regex = re.escape(self.word)
        regex = regex.replace("\\'", "'")
        if self.match_by_word:
            regex = '\\b' + regex + '\\b'
        return regex

    def get_key(self):
        return self.color.color_string

    def get_scope(self):
        return self.color.color_string

    def set_color(self, color):
        if not isinstance(color, ColorType):
            raise ValueError("Invalid type of color. Got '{}'. Should be string or ColorType".format(type(color)))
        self.color = color

    def __eq__(self, right):
        if right is None: return False
        assert isinstance(right, WordHighlight)
        return self.word == right.word and (self.color is UNSPECIFIED_COLOR or self.color == right.color)

    def __str__(self):
        return "<{}:{}>".format(self.word, self.color)

    def __hash__(self):
        return hash(str(self))

class WordHighlightCollection(object):
    """Keeps track of the highlighted words"""

    def __init__(self, view):
        self.words = []
        self.view = view

    def has_word(self, word):
        return word in self.words

    def get_word_highlight(self, word):
        assert isinstance(word, WordHighlight)
        for w in self.words:
            if w.word == word.word: return w
        return None

    def update(self):
        import re
        keys = set((w.get_key() for w in self.words))
        for k in keys:
            words = [w for w in self.words if w.get_key() == k]
            regions = []
            for w in words:
                pattern = w.get_regex()
                regions += self.view.find_all(pattern)
            self.view.add_regions(k, regions, k)

    def color_frequencies(self):
        freqs = [0]*len(SCOPE_COLORS)
        for i, c in enumerate(SCOPE_COLORS):
            freqs[i] = len([1 for w in self.words if (w.color == c)])
        return freqs

    # Check if the word exists, then remove it from the stack, otherwise add it
    def toggle_word(self, word):
        if self.has_word(word):
            self._remove_word(word)
        else:
            self._add_word(word)
        logging.debug("Used words: {}".format([str(w) for w in self.words]))

    def get_next_color(self):
        min_ind = min((v,ind) for ind,v in enumerate(self.color_frequencies()))[1]
        return ColorType(SCOPE_COLORS[min_ind])

    def _add_word(self, word):
        assert isinstance(word, WordHighlight)
        if word.color is UNSPECIFIED_COLOR or word.color is NEXT_COLOR:
            word.set_color(self.get_next_color())
        self.words.append(word)

    def _remove_word(self, word):
        assert isinstance(word, WordHighlight)
        if self.has_word(word):
            w = self.get_word_highlight(word)
            self.view.erase_regions(w.get_key())
            self.words.remove(w)

    def clear(self):
        words = [w for w in self.words]
        for w in words:
            self._remove_word(w)
        logging.debug("Clearing all highlighted words")

    def dumps(self):
        import pickle
        return pickle.dumps(self)

    @classmethod
    def loads(cls, s):
        import pickle
        instance = pickle.loads(bytes(s))
        assert isinstance(instance, cls)
        return instance

# Updates the collection for the object
def update_collection_wrapper(function):
    def wrap(self, *args, **kwargs):
        s = self.view.settings()
        self.collection = WordHighlightCollection.loads(bytes(s.get("wordhighlighter_collection")))
        ret_value = function(self, *args, **kwargs)
        s.set("wordhighlighter_collection", self.collection.dumps())
        return ret_value
    return wrap

class update_words_event(sublime_plugin.ViewEventListener):
    '''
    Runs an update of the highlights
    '''
    def __init__(self, view):
        self.view = view
        logging.info("Initializing updater instance...")
        settings = sublime.load_settings("word_highlighter.sublime-settings")
        self.debounce_time = settings.get("debounce")
        self.debouncer = None
        logging.debug("Debounce time: {}".format(self.debounce_time))

    @update_collection_wrapper
    def update_highlighting(self):
        logging.debug("Updating highlighting")
        self.collection.update()

    def on_modified(self):
        if self.debouncer is not None:
            self.debouncer.cancel()
        def update_highlighting_f():
            self.update_highlighting()
        self.debouncer = threading.Timer(self.debounce_time, update_highlighting_f)
        self.debouncer.start()

class wordHighlighterClearInstances(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.view = view

    @update_collection_wrapper
    def run(self, edit):
        self.collection.clear()

def restore_collection(view):
    collection = WordHighlightCollection(view)
    for s in SCOPE_COLORS:
        regions = view.get_regions(s)
        unique_words = set()
        if len(regions):
            for r in regions:
                word = view.substr(r)
                whole_word = view.substr(expand_to_word(view, r.begin()))
                matches_whole_word = (word == whole_word)
                unique_words |= set(((word, matches_whole_word), ))
        for w in unique_words:
            logging.info("Restoring word: '{}'".format(w[0]))
            collection._add_word(WordHighlight(*w, color=s))
    collection.update()
    return collection

# Expand the point to a region that contains a word, or an empty Region if
# the point is not placed at a word.
def expand_to_word(view, point):
    classification = view.classify(point)
    # If start of word, expand right to end of word
    if bits_set(classification, sublime.CLASS_WORD_START):
        logging.debug("At start of word!")
        back_stop = point
        forward_stop = view.find_by_class(point, forward=True, classes=sublime.CLASS_WORD_END)
        return sublime.Region(back_stop, forward_stop)
    # If end of word, expand left to start of word
    elif bits_set(classification, sublime.CLASS_WORD_END):
        logging.debug("At end of word!")
        back_stop = view.find_by_class(point, forward=False, classes=sublime.CLASS_WORD_START)
        forward_stop = point
        return sublime.Region(back_stop, forward_stop)
    # Else, expand left and right until hitting word start/end or punctuation.
    # If the word start and end matches first, in right order use as word
    else:
        # Stop for anything but subwords
        stop_classes = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_START | sublime.CLASS_PUNCTUATION_END | sublime.CLASS_LINE_START | sublime.CLASS_LINE_END | sublime.CLASS_EMPTY_LINE
        back_stop = view.find_by_class(point, forward=False, classes=stop_classes)
        forward_stop = view.find_by_class(point, forward=True, classes=stop_classes)
        r = sublime.Region(back_stop, forward_stop)
        # Check that the found Region contains a word
        if bits_set(view.classify(back_stop), sublime.CLASS_WORD_START) and bits_set(view.classify(forward_stop), sublime.CLASS_WORD_END):
            # Valid word!
            return r
        else:
            logging.debug("Expanded word is invalid: '{}'".format(view.substr(r)))
            return sublime.Region(0, 0) # Empty region

class wordHighlighterHighlightInstancesOfSelection(sublime_plugin.TextCommand):
    """
    Highlights all instances of a specific word that is selected
    """
    def __init__(self, view):
        self.view = view
        collection = restore_collection(view)
        settings = sublime.load_settings("word_highlighter.sublime-settings")
        # Save the instance globally for the buffer
        self.view.settings().set("wordhighlighter_collection", collection.dumps())

    # Check if the current language is case insensitive (actually just check if its VHDL, since that is the only one I know and care about currently)
    # re.compile(string, re.IGNORECASE)
    def is_case_insensitive_language(self):
        import re
        syntax_file = self.view.settings().get("syntax")
        re_case_insensitive_language_files = re.compile(r'(i?)(VHDL)\.sublime-syntax')
        matches_case_insensitive_language = re_case_insensitive_language_files.match(syntax_file) is not None
        return matches_case_insensitive_language

    @update_collection_wrapper
    def run(self, edit):
        text_selections = []
        for s in self.view.sel():
            # Expand empty selections to words
            if s.empty():
                r = expand_to_word(self.view, s.begin())
                # Append the word if it is not empty
                txt = self.view.substr(r)
                if txt != '':
                    logging.debug("Expanded word is valid: '{}'".format(txt))
                    text_selections.append(WordHighlight(txt, match_by_word=True))
            # Keep non-empty selections as-is
            else:
                text_selections.append(WordHighlight(self.view.substr(s), match_by_word=False))
        # Get unique items
        text_selections = list(set(text_selections))

        logging.debug("text_selections: " + str(text_selections))

        # Find all instances of each selection
        for w in text_selections:
            self.collection.toggle_word(w)
        self.collection.update()
