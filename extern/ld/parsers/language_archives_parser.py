import sys
import logging

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException
from utils import get_html

class LanguageArchivesParser(OnlineParser):

    def __init__(self):

        self.base_url = 'http://www.language-archives.org/language' 

    def parse_table(self, item):

        try:
            table = item.split('<ol>')[1].split('</ol>')[0]
            rows = table.split('<li>')[1:]
            online_count = 0
            for row in rows:
                if '<span class="online_indicator">' in row:
                    online_count += 1
            return len(rows), online_count
        except Exception as e:
            raise ParserException(
                '{0} in LanguageArchivesParser.parse_table'
                    .format(type(e)))

    def get_tabular_data(self, html):

        try:
            d = {}
            lines = html.split('<h2>')[1:]
            for item in lines:
                category = item.split('</h2>')[0]
                counts = self.parse_table(item)
                d[category] = counts
            return d
        except Exception as e:
            raise ParserException(
                '{0} in LanguageArchivesParser.get_tabular_data'
                    .format(type(e)))

    def get_name(self, string):

        try:
            name_wrapped = string.split('about the')[1].split('</title>')[0]
            if 'language'in name_wrapped:
                name = name_wrapped.split('language')[0].strip(' ')
            else:
                name = name_wrapped
            return name
        except Exception as e:
            raise ParserException(
                '{0} in LanguageArchivesParser.get_name'
                    .format(type(e)))

    def parse(self, sil_codes):

        for sil in sil_codes:

            url = '{0}/{1}'.format(self.base_url, sil)
            html = get_html(url)
            dictionary = {}
            dictionary['Name'] = self.get_name(html)
            d = self.get_tabular_data(html)
            if d is not None:
                for key in d:
                    dictionary[key] = {}
                    all_, online = d[key]
                    dictionary[key]['All'] = all_
                    dictionary[key]['Online'] = online
            yield dictionary


def main():

    sil_codes = sys.argv[1:]
    logging.basicConfig(level=logging.DEBUG)
    parser = LanguageArchivesParser()
    for d in parser.parse(sil_codes):
        print d

if __name__ == "__main__":
    main()
