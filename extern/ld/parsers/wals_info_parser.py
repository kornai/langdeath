import logging

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException
from utils import get_html


class WalsInfoParser(OnlineParser):

    def __init__(self):

        self.url = "http://wals.info/languoid.tab?sEcho=1&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc"  # nopep8

    def get_header(self, html):
        try:
            lines = html.split('\n')
            header_line = lines[0]
            header = header_line.strip('\n').split('\t')
            return header, lines[1:]
        except Exception as e:
            raise ParserException(
                'Error in WalsInfoParser.get_header(): {0}'.format(e))

    def format_dict(self, d):

        d[u'longitude'] = float(d[u'longitude'])
        d[u'latitude'] = float(d[u'latitude'])
        return d

    def generate_dictionaries(self, html):

        header, data = self.get_header(html)
        for l in data:
            try:
                d = {}
                cells = l.strip('\n').split('\t')
                for i in xrange(len(header)):
                    d[header[i]] = cells[i]
                d = self.format_dict(d)
                yield d
            except Exception as e:
                raise ParserException(
                    'Error in WalsInfoParser.generate_dictionaries():' +
                    '{0} at line {1}'.format(e, l))

    def parse(self):

        html = get_html(self.url)
        for d in self.generate_dictionaries(html):
            yield d


def main():

    logging.basicConfig(level=logging.DEBUG)
    parser = WalsInfoParser()
    for d in parser.parse():
        print d

if __name__ == "__main__":
    main()
