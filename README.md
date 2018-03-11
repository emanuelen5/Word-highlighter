# Word highlighter for Sublime Text
The plugin is meant as a replacement for the Emacs plugin [highlight-symbol](http://nschum.de/src/emacs/highlight-symbol/)

## Similar plugins
* [SublimeANSI]
* [ColorHighlighter]

[SublimeANSI]: https://github.com/aziz/SublimeANSI "Colorize text with ANSI color codes"
[ColorHighlighter]: https://github.com/Monnoroch/ColorHighlighter "Colorize CSS files"

## Setting syntax highlighting dynamically for regions
See the [Sublime text API reference].

```python
# Get regions that match the variable_name (case insensitive)
regions = view.find_all(r'(?i)\b(variable_name)\b')
# Set the scope for the regions (which in turn is used together 
# with the theme to determine the color of the region)
view.add_regions('unique_region_key', regions, 'scope.name')
# Can add 'sublime.DRAW_NO_OUTLINE' as a parameter to skip the outline on the region
```

This method however only colorizes the background (addressed by [this thread][SublimeTextIssues: Change foreground color through regions])

[Sublime text API reference]: https://www.sublimetext.com/docs/3/api_reference.html#sublime.View "Sublime text API (Sublime.view)"
[SublimeTextIssues: Change foreground color through regions]: https://github.com/SublimeTextIssues/Core/issues/817 "SublimetextIssues/Core: Allow plugins to change foreground text color through manually adding regions"

The snippet above is sufficient for simple highlights (paste into the Sublime text console to run), but is limited to the current theme and its defined color scopes. To define more scopes and colors dynamically, check the [ANSI highlighter][SublimeANSI] or the [Color Highlighter][ColorHighlighter]. The ANSI highlighter seems much cleaner and simpler to use, but the Color highlighter might be more complete (with some cool things to "steal").

### Changing the syntax file
`set_syntax_file(syntax_file)`: Changes the syntax used by the view. `syntax_file` should be a name along the lines of `Packages/Python/Python.tmLanguage`. To retrieve the current syntax, use `view.settings().get('syntax')`.

## Running python code
See the Sublime text guides for [plugins][Sublime Text: Plugins] together with the [API][Sublime text API reference].

Implement a class that inherits `sublime_plugin.TextCommand` and implements a `run` function, as below:

```python
class vhdlModeInsertCommentLine(sublime_plugin.TextCommand):
  def run(self, edit):
    # ...
```

[Sublime Text: Plugins]: http://docs.sublimetext.info/en/latest/extensibility/plugins.html

## Jumping between highlighted variables
The "jump between variables" should basically be some calls to the `view.sel()` function (taken from [Sublime Text Forum: Set position [...]][ST Forum: Set pos], since the `view.find_all(...)` call returns the positions in the text.:

```python
# Class sublime.View:
#   sel()                         - Returns a reference to the selection (RegionSet).
#   show(point, <show_surrounds>) - Scroll the view to show the given point.
#   show_at_center(point)         - Scroll the view to center on the point.

# To read cursor(s) postion:
pos = view.sel()

# To put the cursor(s) (selection) somewhere, simply modify the sel() RegionSet values:
view.sel().clear()
view.sel().add(sublime.Region(pos))

# Take care of multi-selection here
```

The text can however change between calls, so the `view.find_all(...)` should not be cached, but rather run from the current cursor each time.

**Tips:** The ANSI highlighter [caches regexes](https://github.com/aziz/SublimeANSI/blob/master/ansi.py#L43) and uses a [variation of the `view.find_all()` function that is supposed to be faster](https://github.com/aziz/SublimeANSI/blob/master/ansi.py#L58).

[ST Forum: Set pos]: https://forum.sublimetext.com/t/api-set-cursor-position-view-location/2308/2 "API: Set cursor position/view location?"

## Selecting the word that the cursor is currently at
See the example plugin `Packages/Default/delete_word.py` that deletes a word to the left or right of the cursor.