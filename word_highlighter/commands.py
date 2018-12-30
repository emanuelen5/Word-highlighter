import sublime
import sublime_plugin
import word_highlighter.core as core

# For automatically creating color schemes for the highlighter
import shutil
import os

# For updating the highlighting on modifications of text
import threading

import word_highlighter.helpers as helpers
logger = helpers.get_logger(__name__, __file__)

def plugin_loaded():
    logger.info("Loading module")
    settings = helpers.get_settings()
    logger.info("Color picking scheme: {}".format(settings.get("color_picking_scheme")))
    logger.info("Debounce time: {}".format(settings.get("debounce")))

class update_words_event(sublime_plugin.ViewEventListener, core.CollectionableMixin):
    '''
    Runs an update of the highlights
    '''
    def __init__(self, view):
        self.view = view
        settings = helpers.get_settings()
        self.debounce_time = settings.get("debounce")
        self.debouncer = None

    @core.CollectionableMixin.update_collection_nonreentrant
    def update_highlighting(self):
        logger.debug("Updating highlighting")
        self.collection.update()

    def on_modified(self):
        if self.debouncer is not None:
            self.debouncer.cancel()
        self.debouncer = threading.Timer(self.debounce_time, self.update_highlighting)
        self.debouncer.start()

class update_color_scheme_event(sublime_plugin.ViewEventListener):
    def __init__(self, view):
        self.view = view
        self.last_color_scheme = None
        self.create_color_scheme() # Run once initially, then only on change of settings
        key = "create_color_scheme_on_change"
        self.view.settings().clear_on_change(key)
        self.view.settings().add_on_change(key, self.create_color_scheme)

    def get_color_scheme(self):
        return self.view.settings().get("color_scheme")

    def create_color_scheme(self):
        current_color_scheme = self.get_color_scheme()
        if current_color_scheme != self.last_color_scheme:
            logger.info("Adding color scheme {}".format(current_color_scheme))
            color_scheme_basename = os.path.basename(current_color_scheme)
            shutil.copy(os.path.join(helpers.color_schemes_dir, "word_highlighter.template-sublime-color-scheme"), os.path.join(helpers.color_schemes_dir, color_scheme_basename))
            self.last_color_scheme = current_color_scheme

class wordHighlighterClearInstances(sublime_plugin.TextCommand, core.CollectionableMixin):
    def __init__(self, view):
        self.view = view

    @core.CollectionableMixin.update_collection_nonreentrant
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
class wordHighlighterClearMenu(sublime_plugin.TextCommand, core.CollectionableMixin):
    @core.CollectionableMixin.update_collection_nonreentrant
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

class wordHighlighterHighlightInstancesOfSelection(sublime_plugin.TextCommand, core.CollectionableMixin):
    """
    Highlights all instances of a specific word that is selected
    """
    def __init__(self, view):
        self.view = view
        self.collection = core.WordHighlightCollection.restore(view)
        self.collection.update()
        self.save_collection()

    def run(self, edit):
        text_selections = []
        for s in self.view.sel():
            # Expand empty selections to words
            if s.empty():
                r = core.expand_to_word(self.view, s.begin())
                # Append the word if it is not empty
                txt = self.view.substr(r)
                if txt != '':
                    logger.debug("Expanded word is valid: '{}'".format(txt))
                    text_selections.append(core.WordHighlight(txt, match_by_word=True, literal_match=True))
            # Keep non-empty selections as-is
            else:
                text_selections.append(core.WordHighlight(self.view.substr(s), match_by_word=False, literal_match=True))
        # Get unique items
        text_selections = list(set(text_selections))

        logger.debug("text_selections: " + str(text_selections))

        # Find all instances of each selection
        self.load_collection()
        for w in text_selections:
            self.collection.toggle_word(w)
        self.collection.update()
        self.save_collection()

class wordHighlighterEditRegexp(sublime_plugin.TextCommand, core.CollectionableMixin):
    '''
    Edit an existing regexp via an input panel
    '''
    def run(self, edit):
        self._run()

    def _run(self):
        self.load_collection()
        words = self.collection.words
        # Check if current point is placed on a region
        sel = self.view.sel()
        for w in words:
            word_regions = w.find_all_regions(self.view)
            for sr in sel:
                sr = sublime.Region(sr.begin()-1, sr.end()+1)
                if any([wr.intersects(sr) for wr in word_regions]):
                    self.input_new_regex(w)

    def input_new_regex(self, word):
        self.view.window().show_input_panel("Edit regexp", word.get_regex(), self.create_on_done(word), None, None)

    def create_on_done(self, word):
        def on_done(text):
            return self.set_word_regex(word, text)
        return on_done

    @core.CollectionableMixin.update_collection_nonreentrant
    def set_word_regex(self, word, text):
        w = self.collection.get_word_highlight(word)
        w.set_regex(text)
        self.collection.update()