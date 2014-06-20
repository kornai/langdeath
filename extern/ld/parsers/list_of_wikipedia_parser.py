import re

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException
from utils import get_html, replace_html_formatting


class WikipediaListOfLanguagesParser(OnlineParser):

    def __init__(self):

        self.url = 'http://meta.wikimedia.org/wiki/List_of_Wikipedias'
        self.needed_keys = {
            "Wiki": "other_codes",
            "Language": "name",
            "Language (local)": "native_name",
            "Articles": "wp_articles",
            "Total": "wp_total",
            "Edits": "wp_edits",
            "Admins": "wp_admins",
            "Users": "wp_users",
            "Active Users": "wp_active_users",
            "Images": "wp_images",
            "Depth": "wp_depth"
        }
        self.numnorm = lambda x: re.compile(",([0-9]{3})").sub("\\1", x)

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

    def split_row(self, row):

        try:
            row = row.replace('\n', '')
            row = replace_html_formatting(row)
            return [item.replace('</td>', '')
                    for item in re.split('<td.*?>', row)]
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

    def clean_dict(self, d):
        cd = {}
        for k in d:
            if k not in self.needed_keys:
                continue

            k2 = self.needed_keys[k]
            if k2 == "other_codes":
                cd[k2] = {"wiki": d[k]}
            if k2 in ["name", "native_name"]:
                cd[k2] = d[k]
            if k2.startswith("wp_"):
                norm = self.numnorm(d[k])
                try:
                    cd[k2] = int(norm)
                except ValueError:
                    cd[k2] = 0
        return cd

    def parse(self):

        html = get_html(self.url)
        for dict_ in self.generate_dictionaries(html):
            cd = self.clean_dict(dict_)
            if cd["other_codes"]["wiki"] in ["simple", "be-x-old", "arc"]:
                cd["sil"] = "xxw-{0}".format(cd["other_codes"]["wiki"])
            yield self.clean_dict(dict_)


def main():

    parser = WikipediaListOfLanguagesParser()
    for d in parser.parse():
        print repr(d)

if __name__ == "__main__":
    main()
