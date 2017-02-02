import re

from base_parsers import OnlineParser
from utils import get_html

class GoogleTranslateParser(OnlineParser):

    def __init__(self, resdir):

        self.url = 'https://en.wikipedia.org/wiki/Google_Translate'
        self.title_regex = re.compile('<span class=.*?>(.*?)</span>.*')
        self.lang_regex = re.compile('<a href=.*?>(.*?)</a>.*')
        self.get_mapping_dict('{0}/mappings/google'.format(resdir))

    def get_mapping_dict(self, mapping_fn):
        self.mapping_dict = {}
        for l in open(mapping_fn):
            k, v = l.strip().decode('utf-8').split('\t')
            self.mapping_dict[k] = v
    
    def generate_h2_block(self, html):
        for b in html.split('<h2>')[1:]:
            matched = self.title_regex.match(b)
            if matched is not None:
                title = matched.groups()[0]
                yield title, b
    
    def process_h2_block(self, block): 
        needed_list = block.split('<ol>')[1].split('</ol>')[0]
        for item in needed_list.split('<li>')[1:]:
            matched = self.lang_regex.match(item)
            if matched != None:
                yield {'name': matched.groups()[0]}

    def generate_dictionaries(self, html):
        for title, block in self.generate_h2_block(html):
            if title != 'Supported languages':
                continue
            for d in self.process_h2_block(block):
                yield d
    
    def parse(self):

        html = get_html(self.url)
        for d in self.generate_dictionaries(html):
            if d['name'] in self.mapping_dict:
                d['name'] = self.mapping_dict[d['name']]
            yield d
    

def main():
    import sys
    parser = GoogleTranslateParser(sys.argv[1])
    for d in parser.parse():
        print d

if __name__ == "__main__":
    main()
