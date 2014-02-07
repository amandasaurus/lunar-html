# encoding: utf-8
import re
import urlparse
import csv

import lxml.html.soupparser
import cssselect

from unittest import TestCase

class BaseLunarHTMLTestCase():

    def assertContainsRegex(self, *regexes):
        """Asserts that the regexes are in the last response"""
        for regex in regexes:
            self.assertNotEqual(re.search(regex, self.response.content), None)

    def assertNotContainsRegex(self, *regexes):
        """Asserts that the regexes are not in the last response"""
        for regex in regexes:
            self.assertEqual(re.search(regex, self.response.content), None)


    def assertCurrentURL(self, desired_url):
        """Asserts that the current URL is equal to this"""
        self.assertEquals(self.currentURL, desired_url)

    def assertParsedURLMatches(self, url, expected_parsed_url):
        """
        Given dict (expected_parsed_url) with keys that are a subset of when a
        URL gets parsed (i.e. 'path'/'scheme'/… components), asserts that those
        keys in url match that. You can use 'query_list'. A query
        of "foo=bar&baz=boo+boo" would be a query_list of [('foo', 'bar'),
                                                           ('baz', 'boo boo')]
        """
        parsed_url = urlparse.urlparse(url)
        for key, value in expected_parsed_url.items():
            if key == 'query_list':
                self.assertEqual(urlparse.parse_qsl(parsed_url.query, keep_blank_values=True), value)
            else:
                self.assertEqual(getattr(parsed_url, key), value)

    def assertCurrentURLParsed(self, expected_parsed_url):
        """
        Given dict (expected_parsed_url) with keys that are a subset of when a
        URL gets parsed (i.e. 'path'/'scheme'/… components), asserts that those
        keys in the current url match that. You can use 'query_list'. A query
        of "foo=bar&baz=boo+boo" would be a query_list of [('foo', 'bar'),
                                                           ('baz', 'boo boo')]
        """
        return self.assertParsedURLMatches(self.currentURL, expected_parsed_url)

    def assertElementExists(self, selector):
        """Assert a html element matching the selector exists"""
        try:
            self.get_dom_elements(selector)
        except ValueError:
            self.assertTrue(False, msg="Element {0} doesn't exist".format(selector))

    def assertNotElementExists(self, selector):
        """Assert a html element matching the selector doesn't exist"""
        with self.assertRaises(ValueError, msg="Element {} does exist".format(selector)):
            self.get_dom_elements(selector)

    def assertAttributeValue(self, selector, attribute, expected_value):
        """Assert that the HTML element defined by `selector` has the HTML attribute `attribute` matching value `expected_value`"""
        elements = self.get_dom_elements(selector)
        element = elements[0]
        actual_value = element.attrib[attribute]
        self.assertEqual(actual_value, expected_value)

    def assertSelectOptions(self, selector, expected_options):
        """Confirm the select box identified by selector has the options given in expected_options"""
        elements = self.get_dom_elements(selector)
        element = elements[0]
        self.assertEqual(element.tag, 'select')
        options_obj = element.xpath("option")
        self.assertEqual(expected_options, [(option.attrib['value'], option.text) for option in options_obj])

    def get(self, url, params=None):
        """Make a GET request"""
        return self._url_call('GET', url, params)

    def post(self, url, params=None):
        """Make a POST request"""
        return self._url_call('POST', url, params)

    def _url_call(self, method, url, params):
        if method == 'GET':
            func = self.client.get
        elif method == 'POST':
            func = self.client.post
        else:
            raise NotImplementedError(method)

        if params:
            self.response = func(url, params, follow=True)
        else:
            self.response = func(url, follow=True)

        if hasattr(self, '_parsed_response'):
            # Delete stale self._parsed_response
            del self._parsed_response

        # Save current URL
        if len(self.response.redirect_chain) == 0:
            self.currentURL = url
        else:
            self.currentURL = self.response.redirect_chain[-1][0]

    @property
    def parsed_response(self):
        """The current response, but parsed by BeautifulSoup"""
        if not hasattr(self, '_parsed_response'):
            self._parsed_response = lxml.html.soupparser.fromstring(self.response.content)
            # Rewrite all links so that 'form action="."' will work
            self._parsed_response.make_links_absolute(self.currentURL)

        return self._parsed_response

    def csv(self):
        """"Parse this current page as a CSV response and return that list-of-list of data"""
        # TODO take encoding into account
        return list(csv.reader(self.response))

    def get_dom_elements_by_id(self, id):
        elements = self.get_dom_elements_by_xpath('//*[@id="{0}"]'.format(id))
        if len(elements) == 0:
            raise ValueError("Not found")

        return elements

    def get_dom_elements_by_name(self, id):
        elements = self.get_dom_elements_by_xpath('//*[@name="{0}"]'.format(id))
        if len(elements) == 0:
            raise ValueError("Not found")

        return elements

    def get_dom_elements_by_xpath(self, xpath):
        elements = self.parsed_response.xpath(xpath)
        if len(elements) == 0:
            raise ValueError("Not Found")

        return elements

    def get_dom_elements_by_cssselect(self, cssselector):
        elements = self.parsed_response.cssselect(cssselector)
        if len(elements) == 0:
            raise ValueError("Not Found")

        return elements

    def get_dom_elements_by_textcontent(self, text):
        return self.get_dom_elements_by_xpath('//*[contains(., "{0}")]'.format(text))

    def get_dom_elements(self, selector):
        try:
            return self.get_dom_elements_by_id(selector)
        except (ValueError, lxml.etree.XPathEvalError):
            pass

        try:
            return self.get_dom_elements_by_xpath(selector)
        except (ValueError, lxml.etree.XPathEvalError):
            pass

        try:
            return self.get_dom_elements_by_cssselect(selector)
        except (ValueError, cssselect.SelectorSyntaxError):
            pass

        try:
            return self.get_dom_elements_by_name(selector)
        except (ValueError, lxml.etree.XPathEvalError):
            pass

        try:
            return self.get_dom_elements_by_textcontent(selector)
        except (ValueError, lxml.etree.XPathEvalError):
            pass

        # Got to here. ergo not found
        raise ValueError("Not found")

    def get_attribute_value(self, selector, attribute):
        elements = self.get_dom_elements(selector)
        if len(elements) > 1:
            raise TypeError(">1 element returned")
        element = elements[0]
        return element.attrib[attribute]

    def follow_link(self, selector):
        """Given a selector, follow that link. i.e. simulate clicking on a <a> tag"""
        has_text = self.get_dom_elements(selector)
        # this returns all nodes from the inner to the outer one. Get the most
        # inner a tag
        links = [x for x in has_text if x.tag == 'a']
        assert len(links) == 1
        self.get(links[-1].attrib['href'])

    def current_form_values(self, form):
        """Returns a dict of the current value of this form"""
        field_values = {}
        for name in list(form.inputs.keys()):
            field = form.inputs[name]
            # FIXME what happens to inputs without a name?
            if isinstance(field, lxml.html.RadioGroup):
                value = field.value
            elif isinstance(field, lxml.html.CheckboxGroup):
                value = list(field.value)
            elif field.tag in ['input', 'textarea']:
                if field.attrib.get("type") == 'checkbox':
                    value = field.attrib.get("checked") == 'checked'
                else:
                    value = field.value
            elif field.tag == 'select':
                if field.multiple:
                    value = list(field.value)
                else:
                    value = field.value
            else:
                raise NotImplementedError(field.tag)

            # If it's None, turn it into ''
            field_values[name] = value or ''

        return field_values

    def form_values_for_submitting(self, form, new_values):
        """Turn a python dict of form values into a dict to send as parameters for the form to GET/POST"""
        results = {}
        for field_name, field_value in new_values.items():
            field = form.inputs[field_name]
            if isinstance(field, lxml.html.RadioGroup):
                results[field_name] = field_value
            elif isinstance(field, lxml.html.CheckboxGroup):
                values = list(field.value)
                results[field_name] = values
            elif field.tag in ['input', 'textarea']:
                if field.attrib.get("type") == 'checkbox':
                    if field_value:
                        results[field_name] = field_name
                    else:
                        pass
                else:
                    results[field_name] = field_value
            elif field.tag == 'select':
                if field.multiple:
                    results[field_name] = list(field_value)
                else:
                    results[field_name] = field_value
            else:
                raise NotImplementedError(field.tag)

        return results

    def submit_form(self, form_selector, field_values=None):
        """Given the HTML id attribute of a form on this page, submit it with these values"""
        field_values = field_values or {}
        form = self.get_dom_elements(form_selector)[0]
        method = form.method
        action = form.action
        existing_field_values = self.current_form_values(form)

        new_field_values = {}
        new_field_values.update(existing_field_values)
        new_field_values.update(field_values)

        new_field_values = self.form_values_for_submitting(form, new_field_values)

        # Find submit button
        submitters = form.xpath("//*[@submit or @type='submit']")
        if len(submitters) == 0:
            # Don't add anything
            pass
        else:
            if 'name' in submitters[0].attrib:
                # Just use the first one, but only if it has a name
                new_field_values[submitters[0].attrib['name']] = submitters[0].attrib['value']

        self._url_call(method, action, new_field_values)

class LunarHTMLTestCase(BaseLunarHTMLTestCase, TestCase):
    pass
