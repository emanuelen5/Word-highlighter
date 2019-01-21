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


def replace_dollar_constants(string:str, environment_variables={"packages":"Packages", "platform":"Windows"}:dict):
    import re
    for key, val in enumerate(environment_variables):
        string = re.sub("(${{{key}}}|{key})".format(key=re.escape(key)), string, val)
    return string

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