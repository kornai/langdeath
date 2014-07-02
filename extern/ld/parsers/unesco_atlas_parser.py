from base_parsers import OfflineParser
import re
import sys


class UnescoAtlasParser(OfflineParser):

    def __init__(self, fn):

        self.fh = open(fn)
        self.compile_regexes()

    def compile_regexes(self):

        self.html_tag_pattern = re.compile(r'<(.*?)>(.*?)</\1>')

    def format_(self, category, info):

        if category in ['Countries', 'Country_codes_alpha_3',
                        'ISO639-3_codes']:
            return category, [l.strip() for l in info.split(',')]
        return category, info

    def generate_dictionaries(self):

        d = {}
        l = self.fh.readline()
        for l in self.fh:
            if l[:7] in ['<RECORD', '</RECOR']:
                continue
            category, info = self.html_tag_pattern.match(l).groups()
            if category == 'ID':
                yield d
                d = {}
            category_, info_ = self.format_(category, info)
            d[category_] = info_
        yield d

    def parse(self):

        for d in self.generate_dictionaries():
            yield d


def main():

    a = UnescoAtlasParser(sys.argv[1])
    for d in a.parse():
        print d

if __name__ == "__main__":
    main()
