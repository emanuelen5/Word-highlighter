import sublime
from . import helpers
import copy
import os
import re

logger = None

def plugin_loaded():
    global logger
    logger = helpers.get_logger()
    logger.info("Loading " + __name__)

## Define some color constants
class ColorType(object):
    def __init__(self, color_string, name=None, foreground=None, background=None):
        self.color_string = color_string
        self.scope = color_string
        self.name = name
        self.foreground = foreground
        self.background = background

    def __eq__(self, right):
        if isinstance(right, str):
            return self.color_string == right
        elif isinstance(right, ColorType):
            return self.color_string == right.color_string
        else:
            raise ValueError("Illegal type in comparison")

    def __str__(self):
        return self.color_string

    def __repr__(self):
        return "<{}, {}, {}, {}>".format(self.scope, self.name, self.foreground, self.background)

def lookup_color(color_string, variables):
    r = re.compile(r'var\((.*)\)')
    m = r.match(color_string.strip())
    if not m:
        return color_string

    var_name = m.group(1).strip()
    if var_name not in variables:
        logger.error("The variable {} does not exist among the variables!".format(var_name))
        return color_string
    return variables[var_name]

def get_colors(view):
    color_scheme = os.path.basename(view.settings().get("color_scheme"))
    s = sublime.load_settings(color_scheme)
    variables = s.get("variables")
    colors = []
    for rule in s.get("rules"):
        colors.append(ColorType(rule["scope"], rule["name"], lookup_color(rule["foreground"], variables), lookup_color(rule["background"], variables)))
    return colors

# Add some base colors to use for selections (perhaps read from settings file)
SCOPE_COLORS = ["word_highlighter.color{}".format(i) for i in range(10)]
UNSPECIFIED_COLOR = ColorType("UNSPECIFIED_COLOR")
color_schemes = {s:ColorType(s) for s in ["RANDOM", "RANDOM_EVEN", "CYCLIC", "CYCLIC_EVEN", "CYCLIC_EVEN_ORDERED"]}

def get_color_picking_scheme(name):
    assert isinstance(name, str)
    if name in color_schemes.keys():
        color_picking_scheme = color_schemes[name]
    else:
        color_picking_scheme = color_schemes["RANDOM"]
        logger.error("Invalid next color scheme setting {}. Choose between {}".format(name, list(color_schemes.keys())))
    return color_picking_scheme

# Instances that combine a word with a color scope
class WordHighlight(object):
    def __init__(self, regex, color=UNSPECIFIED_COLOR, literal_match=False, match_by_word=False):
        assert isinstance(regex, str)
        if isinstance(color, str):
            color = ColorType(color)
        elif not isinstance(color, ColorType):
            raise ValueError("Invalid color type")
        self.regex = WordHighlight.convert_regex(regex, literal_match=literal_match, match_by_word=match_by_word)
        self.color = color

    def get_regex(self):
        return self.regex

    def set_regex(self, regex):
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
            logger.error(error_msg)
            raise AssertionError(error_msg)
        return next_color

    # Check if the word exists, then remove it from the stack, otherwise add it
    def toggle_word(self, word):
        if self.has_word(word):
            self._remove_word(word)
        else:
            self._add_word(word)
        logger.debug("Used words: {}".format([str(w) for w in self.words]))

    def _add_word(self, word):
        assert isinstance(word, WordHighlight)
        if word.color is UNSPECIFIED_COLOR:
            settings = helpers.get_settings()
            color_picking_scheme = get_color_picking_scheme(settings.get("color_picking_scheme"))
            logger.debug("Chosen color scheme: {}".format(color_picking_scheme))
            word.set_color(self.get_next_word_color(color_picking_scheme))
        self.words.append(word)

    def _remove_word(self, word):
        assert isinstance(word, WordHighlight)
        if self.has_word(word):
            w = self.get_word_highlight(word)
            self.words.remove(w)
            self.removed_words.append(copy.deepcopy(w))

    def clear(self):
        logger.debug("Clearing all highlighted words")
        self.words.clear()
        self.removed_words.clear()
        for k in SCOPE_COLORS:
            self.view.erase_regions(k)

    @classmethod
    def load(cls, view):
        import pickle
        collection_stream = view.settings().get("wordhighlighter_collection")
        instance = pickle.loads(bytes(collection_stream))
        assert isinstance(instance, cls)
        return instance

    def save(self):
        import pickle
        collection_stream = pickle.dumps(self)
        self.view.settings().set("wordhighlighter_collection", collection_stream)

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
                logger.info("Restoring word: '{}'".format(w[0]))
                collection._add_word(WordHighlight(w[0], color=s, match_by_word=w[1]))
        return collection

# Expand the point to a region that contains a word, or an empty Region if
# the point is not placed at a word.
def expand_to_word(view, point):
    classification = view.classify(point)
    # If start of word, expand right to end of word
    if helpers.bits_set(classification, sublime.CLASS_WORD_START):
        logger.debug("At start of word!")
        back_stop = point
        forward_stop = view.find_by_class(point, forward=True, classes=sublime.CLASS_WORD_END)
        return sublime.Region(back_stop, forward_stop)
    # If end of word, expand left to start of word
    elif helpers.bits_set(classification, sublime.CLASS_WORD_END):
        logger.debug("At end of word!")
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
        if helpers.bits_set(view.classify(back_stop), sublime.CLASS_WORD_START) and helpers.bits_set(view.classify(forward_stop), sublime.CLASS_WORD_END):
            # Valid word!
            return r
        else:
            logger.debug("Expanded word is invalid: '{}'".format(view.substr(r)))
            return sublime.Region(point, point) # Empty region

class CollectionableMixin(object):
    def load_collection(self):
        self.collection = WordHighlightCollection.load(self.view)

    def save_collection(self):
        self.collection.save()

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
