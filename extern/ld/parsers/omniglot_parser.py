import urllib
from HTMLParser import HTMLParser

from base_parsers import OnlineParser
from iso_639_3_parser import LanguageUpdate


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
            self.lang_ud = LanguageUpdate()
            self.lang_ud.name = ''
            self.lang_ud.in_omniglot = True
        elif tag == 'p':
            self.in_name = False

    def handle_endtag(self, tag):
        if tag == 'ol':
            self.in_list = False
        elif tag == 'a':
            self.in_name = False
            if self.in_list and self.lang_ud.name not in ['', 'top']:
                self.lang_updates.append(self.lang_ud)

    def handle_text(self, text):
        if self.in_name:
            self.lang_ud.name += self.unescape(text)

    def handle_data(self, data):
        self.handle_text(data)

    def handle_entityref(self, name):
        self.handle_text('&'+name+';')

    def handle_charref(self, name):
        self.handle_entityref('#'+name)


class OmniglotParser(OnlineParser):

    def __init__(self):
        self.url = 'http://www.omniglot.com/writing/languages.htm'
        
    def parse(self):
        """
        yields LanguageUpdates of languages listed by Omniglot with in_omniglot
        atrribute set to True
        """
        html_parser = OmniglotHTMLParser()
        html_filen, headers = urllib.urlretrieve(self.url)
        html_parser.feed(open(html_filen).read())
        return iter(html_parser.lang_updates)
