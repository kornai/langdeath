import re

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException
from utils import get_html


class WikipediaIncubatorsParser(OnlineParser):
    
    def __init__(self):

        self.url = 'http://incubator.wikimedia.org/wiki/Incubator:Wikis'

    def generate_rows(self, tabular):

        pattern = re.compile('<tr.*?>(.*?)</tr>(.*)', re.DOTALL)
        try:
            m = pattern.search(tabular)
            while m is not None:
                row, rest = m.groups()
                yield row
                m = pattern.search(rest)
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaIncubatorsParser.generate_rows'
                .format(type(e)))

    def get_tabular(self, html):

        try:
            pattern = re.compile('<table class=.*?>(.*?)</table>', re.DOTALL)
            m = pattern.search(html)
            return m.groups()[0]
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaIncubatorsParser.get_tabular'
                    .format(type(e)))

    def replace_html_formatting(self, row):

        row = re.sub('<[/]{0,1}a.*?>', '', row)
        row = re.sub('<[/]{0,1}b>', '', row)
        return row

    def split_row(self, row):

        try:
            row = row.replace('\n', '')
            row = self.replace_html_formatting(row)
            return [item.strip('</td> ')
                    for item in re.split('<td.*?>', row)[1:]]
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaIncubatorsParser.split_row'
                .format(type(e)))

    def get_row_dict(self, column_titles, cells):

        try:
            return dict([(column_titles[i], cells[i])
                         for i in xrange(len(column_titles))])
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaIncubatorsParser.get_row_dict'
                .format(type(e)))

    def split_headline(self, headline):
        main_headline = headline.split('<tr>')[-2]
        main_headline = re.sub('(</tr>|\n|</th>)', '', main_headline)
        return re.split('<th.*?>', main_headline)[1:]

    def strip_header(self, tabular_):
        pattern = re.compile('<th(.*?)(<td.*)', re.DOTALL)
        try:
            header, rest = pattern.search(tabular_).groups()
            return header, rest
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaIncubatorsParser.strip_header'
                .format(type(e)))

    def get_wp_tabular(self, tabular_):
        pattern = re.compile('<span class=.*?>Wikipedia</span>.*?(<td.*?)' +
                             '<tr>[\n]{0,1}<td.*?editsection', re.DOTALL)
        try:
            wp_tabular = pattern.search(tabular_).groups()[0]
            return wp_tabular
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaIncubatorsParser.get_wp_tabular'
                .format(type(e)))

    def generate_dictionaries(self, string):

        tabular_ = self.get_tabular(string)
        headline, tabular = self.strip_header(tabular_)
        column_titles = self.split_headline(headline)
        wp_tabular = self.get_wp_tabular(tabular_)
        for row in self.generate_rows(wp_tabular):
            cells = self.split_row(row)
            row_dict = self.get_row_dict(column_titles, cells)
            yield row_dict

    def parse(self):

        html = get_html(self.url)
        for dict_ in self.generate_dictionaries(html):
            yield dict_


def main():

    parser = WikipediaIncubatorsParser()
    for d in parser.parse():
        print repr(d)

if __name__ == "__main__":
    main()
