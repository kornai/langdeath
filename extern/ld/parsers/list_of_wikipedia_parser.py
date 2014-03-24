import urllib2
import re

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException


class WikipediaListOfLanguagesParser(OnlineParser):
    
    def __init__(self):

        self.url = 'http://meta.wikimedia.org/wiki/List_of_Wikipedias'

    def generate_rows(self, tabular):

        try:
            pattern = re.compile('<tr>[\n]{0,1}<td>(.*?)(</tr>.*)', re.DOTALL)
            m = pattern.search(tabular)
            while m is not None:
                row, rest = m.groups()
                yield row
                m = pattern.search(rest)
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaListOfLanguagesParser.generate_rows'
                .format(type(e)))

    def generate_tabulars(self, html):

        try:
            pattern = re.compile('<table border.*?<th>(.*?)' +
                                 '(</tr>.*?)</table>(.*)', re.DOTALL)
            m = pattern.search(html)
            while m is not None:
                header, tabular, rest = m.groups()
                yield header, tabular
                m = pattern.search(rest)
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaListOfLanguagesParser.generate_tabulars'
                    .format(type(e)))

    def split_headline(self, headline):

        try:
            return headline.replace('\n', '').replace('</th>', '')\
                    .split('<th>')
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaListOfLanguagesParser.split_headline'
                .format(type(e)))

    def replace_html_formatting(self, row):

        row = re.sub('<[/]{0,1}a.*?>', '', row)
        row = re.sub('<[/]{0,1}b>', '', row)
        return row

    def split_row(self, row):

        try:
            row = row.replace('\n', '')
            row = self.replace_html_formatting(row)
            return [item.strip('</td>') for item in re.split('<td.*?>', row)]
        except Exception as e:
            raise ParserException(
                '{0} in WikipediaListOfLanguagesParser.split_row'
                .format(type(e)))

    def get_row_dict(self, column_titles, cells):

        try:
            return dict([(column_titles[i], cells[i])
                         for i in xrange(len(column_titles))])

        except Exception as e:
            raise ParserException(
                '{0} in WikipediaListOfLanguagesParser.get_row_dict'
                .format(type(e)))

    def generate_dictionaries(self, string):

        for pair in self.generate_tabulars(string):
            headline, tabular = pair
            column_titles = self.split_headline(headline)
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

    parser = WikipediaListOfLanguagesParser()
    for d in parser.parse():
        print repr(d)

if __name__ == "__main__":
    main()
