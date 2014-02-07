#! /usr/bin/env python

from setuptools import setup, find_packages


setup(name="lunar-html",
      version="0.1.0",
      author="Rory McCann",
      author_email="rory@technomancy.org",
      packages=['lunar_html'],
      license = 'GPLv3+',
      description = '',
      test_suite='lunar_html.tests',
      install_requires = [
          'cssselect',
          'lxml',
          'BeautifulSoup',
      ],
)
