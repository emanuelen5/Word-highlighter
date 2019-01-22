import sublime
import unittest
from unittest.mock import patch

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
            if key in obj and obj[key] == value:
                content.extend(obj["children"])
        return Menu(content)

    def get(self, key):
        content = []
        for obj in self.get_objects():
            if key in obj:
                content.append(obj[key])
        return Menu(content)

    def filter(self, key, value=None):
        content = []
        for obj in self.get_objects():
            if key in obj and (value is None or obj[key] == value):
                content.append(obj)
        return Menu(content)

    @classmethod
    def from_path(cls, menu_short_path:str):
        assert menu_short_path.endswith("sublime-menu")
        menu_string = sublime.load_resource(menu_short_path)
        root = sublime.decode_value(menu_string)
        return cls(root)


class TestMenu(unittest.TestCase):
    def setUp(self):
        menu_short_path = "Packages/word_highlighter/Main.sublime-menu"
        self.main_menu = Menu.from_path(menu_short_path)

    def test_root(self):
        root = self.main_menu.get_objects()
        self.assertEqual(1, len(root))

    def test_filter_root(self):
        root = self.main_menu.filter("id").get_objects()
        self.assertEqual(1, len(root), "id exists")
        root = self.main_menu.filter("id", "preferences").get_objects()
        self.assertEqual(1, len(root), "id:preferences exists")
        root = self.main_menu.filter("id", "props").get_objects()
        self.assertEqual(0, len(root), "id:props does not exist")

    def test_children(self):
        children = self.main_menu.children("preferences")
        objs = children.get_objects()
        self.assertEqual(1, len(objs))

    def test_children_does_not_exist(self):
        children = self.main_menu.children("package-settings")
        objs = children.get_objects()
        self.assertEqual(0, len(objs))

    def test_grandchildren(self):
        children = self.main_menu.children("preferences").children("package-settings")
        objs = children.get_objects()
        self.assertEqual(1, len(objs))


def replace_dollar_constants(string:str):
    platform_name = {
        'osx': 'OSX',
        'windows': 'Windows',
        'linux': 'Linux',
    }[sublime.platform()]

    variables = {
        'packages': 'Packages',
        'platform': platform_name,
    }

    string = sublime.expand_variables(string.replace('\\', '\\\\'), variables)
    return string


class TestMainMenu(unittest.TestCase):
    def setUp(self):
        menu_short_path = "Packages/word_highlighter/Main.sublime-menu"
        main_menu = Menu.from_path(menu_short_path)
        self.menu_item = main_menu.children("preferences").children("package-settings").children("Word Highlighter", key="caption")

    def getEditSettingsBaseFile(self, caption):
        menu_item = self.menu_item.filter("caption", caption)
        objs = menu_item.get_objects()
        self.assertEqual(1, len(objs), "There should be one setting with caption '{}'".format(caption))
        settings_dict = objs[0]
        self.assertIn("command", settings_dict)
        self.assertEqual(settings_dict["command"], "edit_settings")
        self.assertIn("args", settings_dict)
        args = settings_dict["args"]
        self.assertIn("base_file", args)
        base_file = replace_dollar_constants(args["base_file"])
        try:
            sublime.load_resource(base_file)
        except IOError as e:
            raise IOError("Cannot open base file '{}': ".format(base_file))
        return base_file

    def test_settings(self):
        settings_name = self.getEditSettingsBaseFile("Settings")

    @unittest.skip("No keymap added for platform")
    def test_keymap_osx(self):
        with patch("sublime.platform") as platform_mock:
            platform_mock.return_value = "osx"
            key_bindings_name = self.getEditSettingsBaseFile("Key Bindings")

    @unittest.skip("No keymap added for platform")
    def test_keymap_linux(self):
        with patch("sublime.platform") as platform_mock:
            platform_mock.return_value = "linux"
            key_bindings_name = self.getEditSettingsBaseFile("Key Bindings")

    def test_keymap_windows(self):
        with patch("sublime.platform") as platform_mock:
            platform_mock.return_value = "windows"
            key_bindings_name = self.getEditSettingsBaseFile("Key Bindings")
