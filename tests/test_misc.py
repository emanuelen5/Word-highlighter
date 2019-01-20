import sublime
import unittest

from word_highlighter.sublime_plugin import plugin_loaded
plugin_loaded()


class Menu(object):
    """Helper class for getting menu items"""
    def __init__(self, root):
        self._root = root

    def get_objects(self):
        root = self._root
        if isinstance(root, dict):
            return [root]
        elif isinstance(root, list):
            return root
        else:
            raise NotImplementedError("Unhandled root type. Got {}".format(type(root)))

    def children(self, value, key="id"):
        content = []
        for obj in self.get_objects():
            content.extend([o.get("children") for o in obj if key in o and o.get(key) == value])
        return Menu(content)

    def get(self, key):
        content = []
        for obj in self.get_objects():
            content.extend([o.get(key) for o in obj])
        return Menu(content)

    def filter(self, key, value=None):
        content = []
        for obj in self.get_objects():
            content.extend([o for o in obj if key in o and (value is None or o.get(key) == value)])
        return Menu(content)

    @classmethod
    def from_path(cls, menu_short_path:str):
        assert menu_short_path.endswith("sublime-menu")
        menu_string = sublime.load_resource(menu_short_path)
        root = sublime.decode_value(menu_string)
        return cls(root)

class TestMainMenu(unittest.TestCase):
    def setUp(self):
        menu_short_path = "Packages/word_highlighter/Main.sublime-menu"
        main_menu = Menu.from_path(menu_short_path)
        print("main_menu", main_menu.get_objects())
        a = main_menu.children("preferences")
        print("a", a.get_objects())
        b = a.children("package-settings")
        print("b", b.get_objects())
        c = b.children("Word Highlighter", key="caption")
        print("c", c.get_objects())
        package_settings = c.filter("caption", "Settings")
        print("package_settings", package_settings.get_objects())

    def test_settings_file_exists(self):
        self.fail()

    def test_keymap_exists_windows(self):
        self.fail()