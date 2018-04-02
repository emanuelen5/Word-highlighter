import unittest
from ..word_highlighter import create_colorscheme_scope_settings_xml, create_colorscheme_scope_xml
import xml.etree.ElementTree as ET
import os

here = os.path.dirname(os.path.abspath(__file__))
theme_root = ET.parse(os.path.join(here, "dummy.tmTheme"))
theme_root = theme_root.getroot()

class TestXML(unittest.TestCase):
    def test_ScopeCreation(self):
        pass

def create_test_suite():
    test_cases = (TestXML, )
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

def main():
    unittest.TextTestRunner().run(create_test_suite())