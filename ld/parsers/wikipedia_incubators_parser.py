import re

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException
from utils import get_html, replace_html_formatting


class WikipediaIncubatorsParser(OnlineParser):

    def __init__(self, resdir):

        self.url = 'http://incubator.wikimedia.org/wiki/Incubator:Wikis'
        self.name_pat = re.compile("Wikipedia (.*)(?=\(wp)\(wp/([^\)]*)")
        self.get_mapping_dict('{0}/mappings/wp_incubator'.format(resdir))

    def get_mapping_dict(self, mapping_fn):
        self.mapping_dict = {}
        for l in open(mapping_fn):
            k, v = l.strip().decode('utf-8').split('\t')
            self.mapping_dict[k] = v

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

    def split_row(self, row):

        try:
            row = row.replace('\n', '')
            row = replace_html_formatting(row)
            return [item.replace('</td> ', '')
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
        pattern = re.compile('<span class=.*?>Wikipedia</span>.*?(<tr.*?)' +
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
            s = dict_["info page"]
            m = self.name_pat.search(s)
            name = m.group(1).strip()
            inc_code = m.group(2).strip()
            if name in self.mapping_dict:
                name = self.mapping_dict[name]
            yield {"name": name, "other_codes": {"wiki_inc": inc_code},
                   "wp_inc": True}


def main():
    import sys
    parser = WikipediaIncubatorsParser(sys.argv[1])
    for d in parser.parse():
        print repr(d)

if __name__ == "__main__":
    main()
