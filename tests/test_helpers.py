import sublime
import unittest
from unittest.mock import MagicMock

from word_highlighter import plugin_loaded
plugin_loaded()

import word_highlighter.helpers as helpers

class TestIsCaseSensitiveLanguage(unittest.TestCase):
    def assertLanguageCaseSensitivity(self, case_sensitivity, language):
        view_mock = MagicMock()
        view_mock.settings.return_value.get.return_value = language.lower() + ".sublime-syntax"
        self.assertEqual(case_sensitivity, helpers.is_case_sensitive_language(view_mock))

    def test_some_languages(self):
        self.assertLanguageCaseSensitivity(False, "VHDL")
        self.assertLanguageCaseSensitivity(True,  "Python")
        self.assertLanguageCaseSensitivity(True,  "C")
        self.assertLanguageCaseSensitivity(True,  "C++")