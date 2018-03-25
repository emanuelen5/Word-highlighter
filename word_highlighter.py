import sublime
import sublime_plugin

# Add some base colors to use for selections (perhaps read from settings file)
SCOPE_COLORS = [
]

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

class wordHighlighterHighlightInstancesOfSelection(sublime_plugin.TextCommand):
    """
    Highlights all instances of a specific word that is selected
    """
    def run(self, edit):
        text_selections = []
        for s in self.view.sel():
            if s.empty():
                p = s.begin() # A point is just an index
                classification = self.view.classify(p)
                # If start of word, expand right to end of word
                if bits_set(classification, sublime.CLASS_WORD_START):
                    print("At start of word!")
                # If end of word, expand left to start of word
                elif bits_set(classification, sublime.CLASS_WORD_END):
                    print("At end of word!")
                # Else, expand left and right until hitting word start/end or punctuation.
                # If the word start and end matches first, in right order use as word
                else:
                    pass
            else:
                text_selections.append(self.view.substr(s))
        # Get unique items
        text_selections = list(set(text_selections))

        print("text_selections: " + str(text_selections))
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