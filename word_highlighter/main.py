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
color_schemes = {s:ColorType(s) for s in ["RANDOM", "RANDOM_EVEN", "CYCLIC", "CYCLIC_EVEN", "CYCLIC_EVEN_ORDERED"]}

def get_color_picking_scheme(name):
    assert isinstance(name, str)
    if name in color_schemes.keys():
        color_picking_scheme = color_schemes[name]
    else:
        color_picking_scheme = color_schemes["RANDOM"]
        logging.error("Invalid next color scheme setting {}. Choose between {}".format(name, list(color_schemes.keys())))
    return color_picking_scheme

# Instances that combine a word with a color scope
class WordHighlight(object):
    def __init__(self, regex, color=UNSPECIFIED_COLOR, literal_match=False, match_by_word=False):
        assert isinstance(regex, str)
        if isinstance(color, str):
            color = ColorType(color)
        elif not isinstance(color, ColorType):
            raise ValueError("Invalid color type")
        self.input_regex = regex
        self.regex = WordHighlight.convert_regex(regex, literal_match=literal_match, match_by_word=match_by_word)
        self.color = color

    def get_regex(self):
        return self.regex

    def get_input_regex(self):
        return self.input_regex

    def set_regex(self, regex):
        self.input_regex = regex
        self.regex = regex

    @staticmethod
    def convert_regex(regex, match_by_word=False, literal_match=False):
        import re
        if literal_match:
            regex = re.escape(regex)
            # Some characters are "too" escaped for add_region to find them
            regex = regex.replace("\\'", "'")
            regex = regex.replace("\\`", "`")
            regex = regex.replace("\\<", "<")
            regex = regex.replace("\\>", ">")
        if match_by_word:
            regex = '\\b' + regex + '\\b'
        return regex

    def find_all_regions(self, view):
        return view.find_all(self.get_regex())

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
        return self.get_regex() == right.get_regex() and (self.color is UNSPECIFIED_COLOR or self.color == right.color)

    def __str__(self):
        return "<{}:{}>".format(self.get_regex(), self.color)

    def __hash__(self):
        return hash(str(self))

class WordHighlightCollection(object):
    """Keeps track of the highlighted words"""

    def __init__(self, view):
        self.words = []
        self.view = view
        self.color_index = 0
        self.removed_words = []

    def has_word(self, word):
        return word.get_regex() in [w.get_regex() for w in self.words]

    def get_word_highlight(self, word):
        assert isinstance(word, WordHighlight)
        for w in self.words:
            if w.get_regex() == word.get_regex(): return w
        return None

    def update(self):
        import re

        keys = set((w.get_key() for w in self.removed_words))
        for key in keys:
            self.view.erase_regions(key)
        self.removed_words.clear()

        keys = set((w.get_key() for w in self.words))
        for k in keys:
            all_regions = [w.find_all_regions(self.view) for w in self.words if w.get_key() == k]
            # Create a list of regions from list of lists of regions
            concatenated_regions = []
            for r in all_regions:
                concatenated_regions.extend(r)
            self.view.add_regions(k, concatenated_regions, k)

    def color_frequencies(self):
        freqs = [0]*len(SCOPE_COLORS)
        for i, c in enumerate(SCOPE_COLORS):
            freqs[i] = len([1 for w in self.words if (w.color == c)])
        return freqs

    def next_color_index(self):
        self.color_index = (self.color_index + 1) % len(SCOPE_COLORS)

    def get_next_word_color(self, color_picking_scheme=get_color_picking_scheme("CYCLIC")):
        import random
        assert isinstance(color_picking_scheme, ColorType)
        if color_picking_scheme is get_color_picking_scheme("RANDOM"):
            next_color = ColorType(random.choice(SCOPE_COLORS))
        elif color_picking_scheme is get_color_picking_scheme("CYCLIC_EVEN_ORDERED"):
            min_ind = min((v,ind) for ind,v in enumerate(self.color_frequencies()))[1]
            next_color = ColorType(SCOPE_COLORS[min_ind])
        elif color_picking_scheme is get_color_picking_scheme("CYCLIC_EVEN"):
            min_frequency = min((v,ind) for ind,v in enumerate(self.color_frequencies()))[0]
            freqs = self.color_frequencies()
            while freqs[self.color_index] != min_frequency:
                self.next_color_index()
            next_color = ColorType(SCOPE_COLORS[self.color_index])
            self.next_color_index()
        elif color_picking_scheme is get_color_picking_scheme("RANDOM_EVEN"):
            min_frequency = min((v,ind) for ind,v in enumerate(self.color_frequencies()))[0]
            min_frequency_indices = [ind for ind,f in enumerate(self.color_frequencies()) if f == min_frequency]
            next_color = ColorType(SCOPE_COLORS[random.choice(min_frequency_indices)])
        elif color_picking_scheme is get_color_picking_scheme("CYCLIC"):
            next_color = ColorType(SCOPE_COLORS[self.color_index])
            self.next_color_index()
        else:
            error_msg = "No defined color picking for scheme '{}'".format(color_picking_scheme)
            logging.error(error_msg)
            raise AssertionError(error_msg)
        return next_color

    # Check if the word exists, then remove it from the stack, otherwise add it
    def toggle_word(self, word):
        if self.has_word(word):
            self._remove_word(word)
        else:
            self._add_word(word)
        logging.debug("Used words: {}".format([str(w) for w in self.words]))

    def _add_word(self, word):
        assert isinstance(word, WordHighlight)
        if word.color is UNSPECIFIED_COLOR:
            settings = sublime.load_settings("word_highlighter.sublime-settings")
            color_picking_scheme = get_color_picking_scheme(settings.get("color_picking_scheme"))
            logging.debug("Chosen color scheme: {}".format(color_picking_scheme))
            word.set_color(self.get_next_word_color(color_picking_scheme))
        self.words.append(word)

    def _remove_word(self, word):
        assert isinstance(word, WordHighlight)
        if self.has_word(word):
            w = self.get_word_highlight(word)
            self.words.remove(w)
            self.removed_words.append(w)

    def clear(self):
        logging.debug("Clearing all highlighted words")
        self.words.clear()
        self.removed_words.clear()
        for k in SCOPE_COLORS:
            self.view.erase_regions(k)

    def dumps(self):
        import pickle
        return pickle.dumps(self)

    @classmethod
    def loads(cls, s):
        import pickle
        instance = pickle.loads(bytes(s))
        assert isinstance(instance, cls)
        return instance

    @classmethod
    def restore(cls, view):
        collection = cls(view)
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
                collection._add_word(WordHighlight(w[0], color=s, match_by_word=w[1]))
        return collection

class CollectionableMixin(object):
    def load_collection(self):
        s = self.view.settings()
        self.collection = WordHighlightCollection.loads(bytes(s.get("wordhighlighter_collection")))

    def save_collection(self):
        s = self.view.settings()
        s.set("wordhighlighter_collection", self.collection.dumps())

    # Updates the collection for the object before entry and saves after exit
    # @note non-re-entrant!
    @classmethod
    def update_collection_nonreentrant(cls, function):
        def wrap(self, *args, **kwargs):
            self.load_collection()
            ret_value = function(self, *args, **kwargs)
            self.save_collection()
            return ret_value
        return wrap

class update_words_event(sublime_plugin.ViewEventListener, CollectionableMixin):
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

    @CollectionableMixin.update_collection_nonreentrant
    def update_highlighting(self):
        logging.debug("Updating highlighting")
        self.collection.update()

    def on_modified(self):
        if self.debouncer is not None:
            self.debouncer.cancel()
        self.debouncer = threading.Timer(self.debounce_time, self.update_highlighting)
        self.debouncer.start()

class wordHighlighterClearInstances(sublime_plugin.TextCommand, CollectionableMixin):
    def __init__(self, view):
        self.view = view

    @CollectionableMixin.update_collection_nonreentrant
    def run(self, edit):
        self.collection.clear()

def save_argument_wrapper(callback, *const_args, **const_kwargs):
    def saved_argument_callback(*args, **kwargs):
        args = const_args + args
        kwargs = dict(const_kwargs, **kwargs)
        return callback(*args, **kwargs)
    return saved_argument_callback

# Monkey-patching some good-to-have constants
sublime.INDEX_NONE_CHOSEN = -1

# Menu for clearing highlighted words
class wordHighlighterClearMenu(sublime_plugin.TextCommand, CollectionableMixin):
    @CollectionableMixin.update_collection_nonreentrant
    def _clear_word(self, original_words, chosen_index):
        self.collection._remove_word(original_words[chosen_index])
        self.collection.update()

    def clear_word(self, original_words, chosen_index):
        if chosen_index == sublime.INDEX_NONE_CHOSEN:
            return
        self._clear_word(original_words, chosen_index)
        new_index = min(chosen_index, len(original_words)-2)
        self._run(new_index)

    def _run(self, index=0):
        self.load_collection()
        words = [w for w in self.collection.words]
        word_strings = [w.get_input_regex() for w in words]
        self.view.window().show_quick_panel(word_strings, save_argument_wrapper(self.clear_word, words), sublime.MONOSPACE_FONT, selected_index=index)

    def run(self, edit, index=0):
        self._run(index)

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
            return sublime.Region(point, point) # Empty region

class wordHighlighterHighlightInstancesOfSelection(sublime_plugin.TextCommand, CollectionableMixin):
    """
    Highlights all instances of a specific word that is selected
    """
    def __init__(self, view):
        self.view = view
        self.collection = WordHighlightCollection.restore(view)
        self.collection.update()
        self.save_collection()

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
                r = expand_to_word(self.view, s.begin())
                # Append the word if it is not empty
                txt = self.view.substr(r)
                if txt != '':
                    logging.debug("Expanded word is valid: '{}'".format(txt))
                    text_selections.append(WordHighlight(txt, match_by_word=True, literal_match=True))
            # Keep non-empty selections as-is
            else:
                text_selections.append(WordHighlight(self.view.substr(s), match_by_word=False, literal_match=True))
        # Get unique items
        text_selections = list(set(text_selections))

        logging.debug("text_selections: " + str(text_selections))

        # Find all instances of each selection
        self.load_collection()
        for w in text_selections:
            self.collection.toggle_word(w)
        self.collection.update()
        self.save_collection()


class wordHighlighterEditRegexp(sublime_plugin.TextCommand, CollectionableMixin):
    '''
    Edit an existing regexp via an input panel
    '''
    def run(self, edit):
        self.load_collection()
        words = self.collection.words
        # Check if current point is placed on a region
        sel = self.view.sel()
        for w in words:
            word_regions = w.find_all_regions(self.view)
            for sr in sel:
                if any([wr.intersects(sr) for wr in word_regions]):
                    self.view.window().show_input_panel("Edit regexp", w.get_regex(), self.create_on_done(w), None, None)

    def create_on_done(self, word):
        def on_done(text):
            return self.set_word_regex(word, text)
        return on_done

    @CollectionableMixin.update_collection_nonreentrant
    def set_word_regex(self, word, text):
        w = self.collection.get_word_highlight(word)
        w.set_regex(text)
        self.collection.update()