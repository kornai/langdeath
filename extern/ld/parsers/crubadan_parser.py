import urllib2
import re

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException


class CrubadanParser(OnlineParser):
    
    def __init__(self):

        self.url = 'http://borel.slu.edu/crubadan/stadas.html'

    def generate_rows(self, tabular):

        try:
            pattern = self.get_row_pattern()
            m = pattern.search(tabular)
            while m is not None:
                row, rest = m.groups()
                yield row
                m = pattern.search(rest)
        except Exception as e:
            raise ParserException(
                '{0} in CrubadanParser.generate_rows'
                .format(type(e)))

    def get_tabular(self, html):

        try:
            pattern = re.compile('<table border.*?>(.*?)</table>', re.DOTALL)
            m = pattern.search(html)
            return m.groups()[0]
        except Exception as e:
            raise ParserException(
                '{0} in CrubadanParser.get_tabular'
                    .format(type(e)))

    def replace_html_formatting(self, row):

        row = re.sub('<[/]{0,1}a.*?>', '', row)
        return row

    def split_row(self, row):

        try:
            row = row.replace('\n', '')
            row = self.replace_html_formatting(row)
            return [item.strip('</td> ')
                    for item in re.split('<td.*?>', row)[1:]]
        except Exception as e:
            raise ParserException(
                '{0} in CrubadanParser.split_row'
                .format(type(e)))

    def get_row_dict(self, column_titles, cells):

        try:
            return dict([(column_titles[i], cells[i])
                         for i in xrange(len(column_titles))])
        except Exception as e:
            raise ParserException(
                '{0} in CrubadanParser.get_row_dict'
                .format(type(e)))

    def get_row_pattern(self):
        return re.compile('<tr>(.*?)</tr>[\n]{0,1}(<tr>.*)', re.DOTALL)

    def strip_header(self, tabular_):
        pattern = self.get_row_pattern()
        try:
            header, rest = pattern.search(tabular_).groups()
            return header, rest
        except Exception as e:
            raise ParserException(
                '{0} in CrubadanParser.strip_header'
                .format(type(e)))

    def generate_dictionaries(self, string):

        tabular_ = self.get_tabular(string)
        headline, tabular = self.strip_header(tabular_)
        column_titles = self.split_row(headline)
        for row in self.generate_rows(tabular):
            cells = self.split_row(row)
            row_dict = self.get_row_dict(column_titles, cells)
            yield row_dict

    def parse(self):

        html = self.get_html()
        for dict_ in self.generate_dictionaries(html):
            yield dict_

    def get_html(self):

        try:
            response = urllib2.urlopen(self.url)
            html = response.read().decode('utf-8')
            return html
        except:
            raise ParserException(
                'Error while downloading {0}\n'.format(self.url))


def main():
    
    parser = CrubadanParser()
    for d in parser.parse():
        print repr(d)

if __name__ == "__main__":
    main()
