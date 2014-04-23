import re

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException
from utils import get_html, replace_html_formatting


class CrubadanParser(OnlineParser):

    def __init__(self):

        self.url = 'http://borel.slu.edu/crubadan/stadas.html'
        # keys that we didn't use yet:
        # Classification, Polluters, Contact(s), Update, Close to
        self.needed_keys = {
            'ISO 639-3': "sil",
            'Name (English)': 'name',
            'Name (Native)': 'native_name',
            'Alternate names': 'alt_names',
            'Docs': 'cru_docs',
            'Words': 'cru_words',
            'Characters': 'cru_characters',
            'Country': 'country',
            'FLOSS SplChk': 'cru_floss_splchk',
            'WT': 'cru_watchtower',
            'UDHR': 'cru_udhr',
        }

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
                '{0} in CrubadanParser.get_tabular'.format(type(e)))

    def split_row(self, row):

        try:
            row = row.replace('\n', '')
            row = replace_html_formatting(row)
            return [item.strip('</td> ')
                    for item in re.split('<td.*?>', row)[1:]]
        except Exception as e:
            raise ParserException(
                '{0} in CrubadanParser.split_row'
                .format(type(e)))

    def get_row_dict(self, column_titles, cells):

        try:
            d = {}
            for i in xrange(len(column_titles)):
                key = column_titles[i]
                if key in ["Docs", "Words", "Characters"]:
                    try:
                        value = int(cells[i])
                    except ValueError:
                        value = None
                elif key == "Alternate names":
                    value = [s.strip() for s in cells[i].split(",")]
                elif key in ["FLOSS SplChk", "WT", "UDHR"]:
                    v = cells[i]
                    if v == "-" or v == "no":
                        value = False
                    else:
                        value = True
                else:
                    value = cells[i]
                if key in self.needed_keys:
                    d[self.needed_keys[key]] = value
            return d

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

        html = get_html(self.url)
        for dict_ in self.generate_dictionaries(html):
            print dict_
            yield dict_


def main():

    parser = CrubadanParser()
    for d in parser.parse():
        print repr(d)

if __name__ == "__main__":
    main()
