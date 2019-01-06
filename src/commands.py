import sublime
import sublime_plugin
from . import core

# For automatically creating color schemes for the highlighter
import shutil
import os

# For updating the highlighting on modifications of text
import threading

from . import helpers
logger = None
is_loaded = False

# Monkey-patching some good-to-have constants
sublime.INDEX_NONE_CHOSEN = -1
sublime.POPUP_LOCATION_AT_CURSOR = -1

import re

def plugin_loaded():
    global logger, is_loaded
    logger = helpers.get_logger()
    logger.info("Loading module")
    settings = helpers.get_settings()
    logger.info("Color picking scheme: {}".format(settings.get("color_picking_scheme")))
    logger.info("Debounce time: {}".format(settings.get("debounce")))
    is_loaded = True

class wordHighlighterWordColorMenu(sublime_plugin.TextCommand, core.CollectionableMixin):
    def navigate(self, word, chosen_color:str):
        color = core.ColorType(chosen_color)
        self.collection._remove_word(word) # Make sure to remove old highlight
        word.set_color(color)
        self.collection._add_word(word)
        self.collection.update()
        self.save_collection()
        self.view.hide_popup()

    def show_word_color_menu(self, word, location=sublime.POPUP_LOCATION_AT_CURSOR):
        content = "<h3>Change highlight color</h3>"
        link_template = "<a href=\"{color_name}\" style=\"color:{foreground};background-color:{background}\">{disp_name}</a><br>"
        for idx, color in enumerate(core.get_colors(self.view)):
            content += link_template.format(color_name=color.scope, disp_name=color.name, foreground=color.foreground, background=color.background)
        self.view.show_popup(content, sublime.HIDE_ON_MOUSE_MOVE_AWAY, location=location, max_width=500, max_height=500, on_navigate=save_argument_wrapper(self.navigate, word))

    def run(self, edit):
        self._run()

    def _run(self):
        self.load_collection()

        sel = self.view.sel()
        for sr in sel:
            sr = sublime.Region(sr.begin()-1, sr.end()+1)
            for w in self.collection.words:
                for wr in w.find_all_regions(self.view):
                    if wr.intersects(sr):
                        self.show_word_color_menu(w, min(sr.end(), wr.end()))
                        return

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
        if not is_loaded:
            return
        current_color_scheme = self.get_color_scheme()
        if current_color_scheme is None:
            return

        if current_color_scheme == self.last_color_scheme:
            return

        logger.info("Adding color scheme {}".format(current_color_scheme))
        scheme_dest_path = os.path.join(helpers.dirs.color_schemes, os.path.basename(current_color_scheme))
        template_contents = sublime.load_resource("Packages/word_highlighter/word_highlighter.template-sublime-color-scheme")
        with open(scheme_dest_path, "w") as f:
            f.write(template_contents)
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
        word_strings = [w.get_regex() for w in words]
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
    def __init__(self, view):
        self.view = view
        self.input_panel_prompt = "Edit regexp"

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
                    self.edit_regex(w)

    def edit_regex(self, word):
        self.view.window().show_input_panel(self.input_panel_prompt, word.get_regex(), self.create_on_done(word), self.create_on_modified(word), self.create_on_canceled(word))

    def create_on_done(self, word):
        def on_done(text):
            self.set_word_regex(word, text)
            regions = word.find_all_regions(self.view)
            highlighted_characters = sum([r.end() - r.begin() for r in regions])

            if highlighted_characters == 0:
                logger.debug("Removing non-matching regex: {}".format(word.get_regex()))
                self.collection._remove_word(word)
                self.collection.update()
                self.collection.save()
        return on_done

    def create_on_modified(self, word):
        def on_modified(text):
            self.set_word_regex(word, text)
        return on_modified

    def create_on_canceled(self, word):
        original_regex = word.get_regex()
        def on_canceled():
            self.set_word_regex(word, original_regex)
        return on_canceled

    def set_word_regex(self, word, text):
        word.set_regex(text)
        self.collection.update()
        self.collection.save()

class wordHighlighterCreateRegexp(wordHighlighterEditRegexp):
    '''
    Create a regexp via an input panel
    '''
    def __init__(self, view):
        self.view = view
        self.input_panel_prompt = "Create regexp"

    def _run(self):
        self.load_collection()
        word = core.WordHighlight("")
        self.collection._add_word(word)
        self.edit_regex(word)

    def create_on_canceled(self, word):
        def on_canceled():
            logger.debug("Cancelling create regexp")
            self.collection._remove_word(word)
            self.collection.update()
            self.collection.save()
        return on_canceled

class wordHighlighterEditRegexpMenu(wordHighlighterEditRegexp):
    '''
    Edit regexp from a list of inputs
    '''
    def _run(self, index=0):
        self.load_collection()
        words = self.collection.words
        word_strings = [w.get_regex() for w in words]
        self.view.window().show_quick_panel(word_strings, save_argument_wrapper(self.edit_chosen_word, words), sublime.MONOSPACE_FONT, selected_index=index)

    def edit_chosen_word(self, original_words, chosen_index):
        if chosen_index == sublime.INDEX_NONE_CHOSEN:
            return
        self.edit_regex(original_words[chosen_index])
