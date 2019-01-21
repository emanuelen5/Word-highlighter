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


def replace_dollar_constants(string:str, environment_variables:dict={"packages":"Packages", "platform":"Windows"}):
    import re
    for key, val in environment_variables.items():
        regex_str = "\\$({{{key}}}|{key})".format(key=re.escape(key))
        regex = re.compile(regex_str)
        string = regex.sub(val, string)
    return string

class TestMainMenu(unittest.TestCase):
    def setUp(self):
        menu_short_path = "Packages/word_highlighter/Main.sublime-menu"
        main_menu = Menu.from_path(menu_short_path)
        self.menu_item = main_menu.children("preferences").children("package-settings").children("Word Highlighter", key="caption")

    def assertHasEditSetting(self, caption):
        return self.menu_item.filter("caption", caption)

    def test_settings(self):
        settings_menu_item = self.assertHasEditSetting("Settings")
        objs = settings_menu_item.get_objects()
        self.assertGreaterEqual(1, len(objs), "No settings found in menu")
        key_bindings = objs[0]
        args = key_bindings["args"]
        base_file = args["base_file"]

    def test_keymap(self):
        key_bindings_menu_item = self.assertHasEditSetting("Key Bindings")
        objs = key_bindings_menu_item.get_objects()
        self.assertGreaterEqual(1, len(objs), "No key bindings found in menu")
        key_bindings = objs[0]
        args = key_bindings["args"]
        base_file = args["base_file"]
