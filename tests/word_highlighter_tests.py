import unittest
#from ..word_highlighter import ...

class TestSomething(unittest.TestCase):
    def test_dummy(self):
        pass

def create_test_suite():
    test_cases = (TestSomething, )
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

def main():
    unittest.TextTestRunner().run(create_test_suite())