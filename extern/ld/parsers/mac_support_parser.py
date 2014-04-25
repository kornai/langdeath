import sys
from HTMLParser import HTMLParser
import logging

from base_parsers import OnlineParser

"""
For some countries, there are more languages available. In this case, the
language is specified in parens like "Luxembourg (English)".
"""

class AppleSupportHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_list = False
        self.lang_updates = []

    def handle_starttag(self, tag, attrs):
        if tag == 'ul' and attrs == []:
            self.in_list = True
        elif tag == 'li':
            self.lang_ud = {'name': ''}
            self.lang_ud['mac_support'] = True
            self.generic = False
        elif tag == 'img' and dict(attrs)['src'].endswith('generic.png'):
            # Generic terms like "Other Asia" are dropped. These appear at
            # the ends of the lists for continents, and are preceded by an
            # Apple logo instead of the flag of the country.
            self.generic = True

    def handle_endtag(self, tag):
        if tag == 'ul':
            self.in_list = False
        elif tag == 'li' and self.in_list and not self.generic:
            self.lang_updates.append(self.lang_ud)
            
    def handle_data(self, text):
        if self.in_list:
            self.lang_ud['name'] += self.unescape(text).strip()

    def handle_entityref(self, name):
        self.handle_data('&'+name+';')

class AppleSupportParser(OnlineParser):
    def parse(self, filen):
        # file has to be saved from https://www.apple.com/support/country/
        # by browser 
        html_parser = AppleSupportHTMLParser()
        html_parser.feed(open(filen).read())
        return iter(html_parser.lang_updates)

def test():
    logging.basicConfig(
        level=logging.DEBUG,
        format= "%(asctime)s : %(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    p = AppleSupportParser()
    for l in p.parse(sys.argv[1]):
        print l
