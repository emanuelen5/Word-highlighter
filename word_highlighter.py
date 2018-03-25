import sublime
import sublime_plugin

# Add some base colors to use for selections (perhaps read from settings file)
SCOPE_COLORS = [
]

class wordHighlighterHighlightInstancesOfSelection(sublime_plugin.TextCommand):
    """
    Highlights all instances of a specific word that is selected
    """
    def run(self, edit):
        text_selections = [self.view.substr(s) for s in self.view.sel()]
        # Get unique items
        text_selections = list(set(text_selections))

        # TODO:
        # 1. Get the words from each selection
        #    Empty selections are expanded to words, nonempty are used as-is
        # 2. Get a unique color association for each selection
        # 3. Find all of the matching words
        # 4. Use add_region() to set the scope for the regions

    def expand_selections_to_words(self):
        '''
        Expand all of the current selections to "words" instead
        '''
        pass