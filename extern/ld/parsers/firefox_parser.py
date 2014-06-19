from HTMLParser import HTMLParser
import urllib

from base_parsers import OnlineParser


class FirefoxHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_tbody = False
        self.in_en_name = False
        self.in_native = False
        self.in_software = False
        self.lang_updates = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tbody':
            self.in_tbody = True
        elif tag == 'tr':
            self.dic = False
            self.pack = False
        elif tag == 'th':
            self.in_en_name = True
        elif tag == 'td':
            if attrs:
                attr_dict = dict(attrs)
                self.code = attr_dict['lang']
                self.in_native = True
            else:
                self.in_software = True

    def handle_endtag(self, tag):
        if tag == 'tbody':
            self.in_tbody = False
        elif tag == 'th':
            self.in_en_name = False
        elif tag == 'td':
            self.in_native = False
            self.in_software = False
        elif tag == 'tr' and self.in_tbody:
            self.lang_updates.append({
                'name': self.en_name,
                'native_name': self.native,
                'code': {"firefox": self.code},
                'firefox_dict': self.dic,
                'firefox_lpack': self.pack
            })

    def handle_data(self, text):
        if self.in_tbody:
            if self.in_en_name:
                self.en_name = text.strip()
            elif self.in_native:
                self.native = text.strip()
            elif self.in_software:
                if text.endswith('Dictionary'):
                    self.dic = True
                elif text.endswith('Pack'):
                    self.pack = True


class FirefoxParser(OnlineParser):
    def parse(self):
        self.url = 'https://addons.mozilla.org/en-US/firefox/language-tools/'
        html_parser = FirefoxHTMLParser()
        html_filen, headers = urllib.urlretrieve(self.url)
        html_parser.feed(open(html_filen).read().decode('utf-8'))
        return iter(html_parser.lang_updates)


def test():
    p = FirefoxParser()
    for l in p.parse():
        print l
