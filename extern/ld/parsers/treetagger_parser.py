from base_parsers import OnlineParser
from utils import get_html
import re

class TreeTaggerParserOnlineParser(OnlineParser):

    def __init__(self):
        self.url = "http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/"
        self.lang_pattern = re.compile('.*?[(\s|>)]([a-zA-Z]+) parameter file*',
                                      re.DOTALL)
    def parse(self):
        html = get_html(self.url)
        parameter_file_list = self.get_parameter_file_list(html)
        for p in parameter_file_list:
            lang = self.parse_lang(p)
            if lang:
                yield {'name': lang, 'treetagger': True}
    
    def get_parameter_file_list(self, html):
        tabular = html.split('Parameter files')[1].split(
            '<ul>')[1].split('</ul>')[0]
        return tabular.split('<li>')[1:]

    def parse_lang(self, p):
        p = re.sub('\s+', ' ', p)
        matched = self.lang_pattern.match(p)    
        return matched.groups()[0]


def main():

    a = TreeTaggerParserOnlineParser()
    for d in a.parse():
        print d

if __name__ == "__main__":
    main()
