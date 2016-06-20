import urllib
from HTMLParser import HTMLParser

from base_parsers import OnlineParser


class OmniglotHTMLParser(HTMLParser):
    def __init__(self, fn):
        HTMLParser.__init__(self)
        self.in_list = False
        self.in_name = False
        self.lang_updates = []
        self.get_mapping_dict(fn)

    def get_mapping_dict(self, mapping_fn):
        self.mapping_dict = {}
        for l in open(mapping_fn):
            k, v = l.strip().decode('utf-8').split('\t')
            self.mapping_dict[k] = v

    def handle_starttag(self, tag, attrs):
        if tag == 'ol':
            self.in_list = True
        elif self.in_list and tag == 'a':
            self.in_name = True
            self.lang_ud = {}
            self.lang_ud['name'] = ''
            self.lang_ud['in_omniglot'] = True
        elif tag == 'p':
            self.in_name = False

    def handle_endtag(self, tag):
        if tag == 'ol':
            self.in_list = False
        elif tag == 'a':
            self.in_name = False
            if self.in_list and self.lang_ud['name'] not in ['', 'top']:
                self.lang_updates.append(self.lang_ud)

    def handle_text(self, text):
        if self.in_name:
            self.lang_ud['name'] += self.unescape(text)

    def handle_data(self, data):
        self.handle_text(data)

    def handle_entityref(self, name):
        self.handle_text('&'+name+';')

    def handle_charref(self, name):
        self.handle_entityref('#'+name)


class OmniglotParser(OnlineParser):

    def __init__(self, fn):
        self.url = 'http://www.omniglot.com/writing/languages.htm'
        self.fn = fn

    def parse(self):
        """
        yields LanguageUpdates of languages listed by Omniglot with in_omniglot
        atrribute set to True
        """
        html_parser = OmniglotHTMLParser(self.fn)
        html_filen, headers = urllib.urlretrieve(self.url)
        html_parser.feed(open(html_filen).read().decode('utf-8'))
        for d in html_parser.lang_updates:
            if d['name'] in html_parser.mapping_dict:
                d['name'] = html_parser.mapping_dict[d['name']]
            yield d    


def main():
    
    import sys
    a = OmniglotParser(sys.argv[1])
   
    for d in a.parse():
        print d

if __name__ == '__main__':
    main()
