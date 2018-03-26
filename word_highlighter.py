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
        # TODO:
        # 1. Get the words from each selection
        #    Empty selections are expanded to words, nonempty are used as-is
        # 2. Get a unique color association for each selection
        # 3. Find all of the matching words
        # 4. Use add_region() to set the scope for the regions