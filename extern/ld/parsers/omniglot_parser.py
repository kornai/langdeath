import urllib
from HTMLParser import HTMLParser

from base_parsers import OnlineParser
from iso_639_3_parser import LanguageUpdate

def name_to_code(ref_name):
    # TODO import this function from somewhere
    return ref_name


class OmniglotHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_list = False
        self.in_name = False
        self.lang_updates = []

    def handle_starttag(self, tag, attrs):
        if tag == 'ol':
            self.in_list = True
        elif self.in_list and tag == 'a':
            self.in_name = True

    def handle_endtag(self, tag):
        if tag == 'ol':
            self.in_list = False
        elif tag == 'a':
            self.in_name = False

    def handle_data(self, data):
        if self.in_name:
            lang_ud = LanguageUpdate()
            lang_ud.code = name_to_code(data)
            lang_ud.in_omniglot = True
            self.lang_updates.append(lang_ud)


class OmniglotParser(OnlineParser):

    def __init__(self):
        self.url = 'http://www.omniglot.com/writing/languages.htm'
        
    def parse(self):
        html_parser = OmniglotHTMLParser()
        html_filen, headers = urllib.urlretrieve(self.url)
        html_parser.feed(open(html_filen).read())
        return iter(html_parser.lang_updates)
