import sublime
import sublime_plugin

class wordHighlighterHighlightInstancesOfSelection(sublime_plugin.TextCommand):
    """
    Highlights all instances of a specific word that is selected
    """
    def run(self, edit):
        '''
        This is run on the actual
        '''
        print("What is this \"edit\"?: " + str(edit))
        print("Now it is actully running!")

    def expand_selections_to_words(self):
        '''
        Expand all of the current selections to "words" instead
        '''
        pass