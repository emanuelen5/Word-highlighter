# Word highlighter for Sublime Text
The plugin is meant as a replacement for the Emacs plugin [highlight-symbol](http://nschum.de/src/emacs/highlight-symbol/)

## Readup
### Setting syntax highlighting dynamically for regions
See the [Sublime text API reference].

```python
# Get regions that match the variable_name (case insensitive)
regions = view.find_all(r'(?i)\b(variable_name)\b')
# Set the scope for the regions (which in turn is used together 
# with the theme to determine the color of the region)
add_regions('unique_region_key', regions, 'scope.name')
```

This method however only colorizes the background (addressed by [this thread][2])

[Sublime text API reference]: https://www.sublimetext.com/docs/3/api_reference.html#sublime.View "Sublime text API (Sublime.view)"
[2]: https://github.com/SublimeTextIssues/Core/issues/817 "SublimetextIssues/Core: Allow plugins to change foreground text color through manually adding regions"

### Other interesting plugins
* [SublimeANSI]
* [ColorHighlighter]

[SublimeANSI]: https://github.com/aziz/SublimeANSI "Colorize text with ANSI color codes"
[ColorHighlighter]: https://github.com/Monnoroch/ColorHighlighter "Colorize CSS files"