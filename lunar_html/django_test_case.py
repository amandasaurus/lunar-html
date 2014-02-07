from .test_case import BaseLunarHTMLTestCase

from django.test import TestCase


class LunarHTMLTestCase(BaseLunarHTMLTestCase, TestCase):
    """
    Extends Django's TestCase to include some more helper functions. This is
    heavily inspired by Selenium large multitude of assertions & verifies
    """

    def assertContainsString(self, *strings):
        """Asserts that the strings are in the last response"""
        for string in strings:
            super(LunarHTMLTestCase, self).assertContains(self.response, string)

    def assertContains(self, *strings):
        self.assertContainsString(*strings)

    def assertNotContainsString(self, *strings):
        """Asserts that the strings are not in the last response"""
        for string in strings:
            super(LunarHTMLTestCase, self).assertNotContains(self.response, string)

    def assertNotContains(self, *strings):
        self.assertNotContainsString(*strings)
