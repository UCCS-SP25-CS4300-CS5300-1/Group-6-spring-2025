from django.test import TestCase

# Create your tests here.
class FakeTestCase(TestCase):
    def test_assertion(self):
        self.assertEqual(type(1), int)
        self.assertEqual(type("hello"), str)