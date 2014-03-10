import urllib
from HTMLParser import HTMLParser

from base_parsers import OnlineParser
from iso_639_3_parser import LanguageUpdate
# TODO import name_to_code

class OmniglotHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.in_list = False

    def handle_starttag(self, tag, attrs):
        if tag == 'ol':
            self.in_list = True

    def handle_endtag(self, tag, attrs):
        if tag == 'ol':
            self.in_list = False

    def handle_data(self, data):
        if self.in_list:
            lang_ud = LanguageUpdate()
            lang_ud.code = name_to_code(data)
            lang_ud.in_omniglot = True
            yield lang_ud


class OmniglotParser(OnlineParser):

    def __init__(self):
        self.url = 'http://www.omniglot.com/writing/languages.htm'
        
    def parse(self):
        html_filen, headers = urllib.urlretrieve(self.url)
        html_parser = OmniglotHTMLParser()
        return html_parser.feed(open(html_filen).read())
