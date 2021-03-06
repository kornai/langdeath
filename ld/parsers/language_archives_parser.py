import sys
import os
import re

from base_parsers import OnlineParser, OfflineParser, BaseParser
from ld.langdeath_exceptions import ParserException
from utils import get_html


class LanguageArchivesBaseParser(BaseParser):

    def __init__(self):
        self.needed_keys = {
            'Primary texts': 'la_primary_texts',
            'Language descriptions': 'la_lang_descr',
            'Lexical resources': 'la_lex_res',
            'Resources in the language': 'la_res_in',
            'Resources about the language': 'la_res_about',
            'Other resources in the language': 'la_oth_res_in',
            'Other resources about the language': 'la_oth_res_about',
        }
        self.alternative_names_pattern =\
            re.compile('<p>Other known names and dialect names:(.*?)</p>',
                       re.DOTALL)

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

    def get_alternative_names(self, html):

        res = self.alternative_names_pattern.search(html)
        if res is None:
            return []
        return [s.strip() for s in res.groups()[0].split(',')]

    def get_sil_codes(**kwargs):
        raise NotImplementedError()

    def manual_filter(self, name, altnames):
        to_filter = {'English':['Norfolk'],
                     'French': ['Norman'],
                     'Romanian': ['Moldovan'], 
                     'Sicilian': ['Tarantino'],
                     'Komi-Zyrian': ['Yazva'],
                     'Nenets': ['Tundra Nenets'],
                     'Mansi': ['Northern Mansi', 'Eastern Mansi', 'Western Mansi'],
                     'Selkup': ['Central Selkup', 'Central Selkups'],
                    }
        if name in to_filter:
            altnames = list(set(altnames).difference(set(to_filter[name])))
        return altnames


    def parse_all(self):
        sil_codes = self.get_sil_codes()
        errors = []
        for sil in sil_codes:
            try:
                html = self.get_html(sil)
                dictionary = {}
                dictionary['sil'] = sil
                name = self.get_name(html)
                dictionary['name'] = name
                altnames =\
                    self.get_alternative_names(html)
                dictionary['alt_names'] = self.manual_filter(name, altnames)
                d = self.get_tabular_data(html)
                if d is not None:
                    for key in d:
                        if key not in self.needed_keys:
                            continue

                        all_, online = d[key]
                        dictionary[self.needed_keys[key] + '_all'] = all_
                        dictionary[self.needed_keys[key] + '_online'] = online
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
    
    def get_sil_codes(self):
        return self.sil_codes

    def parse(self, sil_codes):
        self.sil_codes = sil_codes
        return self.parse_or_load()

    def get_html(self, sil):
        url = '{0}/{1}'.format(self.base_url, sil)
        return get_html(url)


class LanguageArchivesOfflineParser(OfflineParser, LanguageArchivesBaseParser):

    def __init__(self, basedir):
        super(LanguageArchivesOfflineParser, self).__init__()
        self.basedir = basedir
        
    def get_sil_codes(self):
        return [f for f in os.listdir(self.basedir)] 

    def parse(self):
        return self.parse_or_load()

    def get_html(self, sil, encoding='utf-8'):
        return open('{0}/{1}'.format(self.basedir, sil)).read().decode(encoding)


def test_online_parser():

    sil_codes = [l.strip('\n').split('\t')[0] for l in sys.stdin]
    parser = LanguageArchivesOnlineParser()
    for d in parser.parse(sil_codes):
        print repr(d)


def test_offline_parser():

    parser = LanguageArchivesOfflineParser(sys.argv[1])
    for d in parser.parse():
        print repr(d)


def main():

    test_offline_parser()

if __name__ == "__main__":
    main()
