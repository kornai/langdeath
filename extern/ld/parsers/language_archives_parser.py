import sys
import os

from base_parsers import OnlineParser, OfflineParser
from ld.langdeath_exceptions import ParserException
from utils import get_html


class LanguageArchivesBaseParser(object):

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
                '{0} in LanguageArchivesBaseParser.parse_table'
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
                '{0} in LanguageArchivesBaseParser.get_tabular_data'
                .format(type(e)))

    def get_html(self, sil):
        raise NotImplementedError()

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
                '{0} in LanguageArchivesBaseParser.get_name'
                .format(type(e)))

    def parse(self, sil_codes):
        errors = []
        for sil in sil_codes:
            try:
                html = self.get_html(sil)
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
            except ParserException:
                errors.append(sil)
                continue

        if len(errors) > 0:
            msg = "Error in LanguageArchiveParser for following sils: "
            msg += repr(errors)
            raise ParserException(msg)


class LanguageArchivesOnlineParser(OnlineParser, LanguageArchivesBaseParser):

    def __init__(self):

        super(LanguageArchivesOnlineParser, self).__init__()
        self.base_url = 'http://www.language-archives.org/language'

    def get_html(self, sil):

        url = '{0}/{1}'.format(self.base_url, sil)
        return get_html(url)


class LanguageArchivesOfflineParser(OfflineParser, LanguageArchivesBaseParser):

    def __init__(self, basedir):
        super(LanguageArchivesOfflineParser, self).__init__()
        self.basedir = basedir

    def get_html(self, sil):
        fn = '{0}/{1}'.format(self.basedir, sil)
        if os.path.exists(fn):
            return open(fn).read()
        else:
            return ''
            raise ParserException()


def test_online_parser():

    sil_codes = [l.strip('\n').split('\t')[0] for l in sys.stdin]
    parser = LanguageArchivesOnlineParser()
    for d in parser.parse(sil_codes):
        print repr(d)


def test_offline_parser():

    sil_codes = [l.strip('\n').split('\t')[0] for l in sys.stdin]
    parser = LanguageArchivesOfflineParser(sys.argv[1])
    for d in parser.parse(sil_codes):
        print repr(d)


def main():

    test_offline_parser()

if __name__ == "__main__":
    main()
