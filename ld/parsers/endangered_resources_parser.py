import re
from HTMLParser import HTMLParser

from base_parsers import OnlineParser
from utils import get_html


class EndangeredResourcesParser(OnlineParser):

    def __init__(self):

        self.langspec_url = 'https://github.com/RichardLitt/endangered' +\
                '-languages#massive-dictionary-and-lexicography-projects'
        self.austronesian_url = 'http://language.psy.auckland.ac.nz/' +\
                'austronesian/language.php?group='
        self.bantu_url = 'http://www.cbold.ish-lyon.cnrs.fr/Data/' +\
                'LangInfoFiles/CBOLDinv.html'
        self.sealang_url = 'http://sealang.net/'
        self.indo_european_url = 'http://ielex.mpi.nl./languagelist/all/'
        self.sealang_url = 'http://sealang.net/'
        self.stedt_base_url = 'http://stedt.berkeley.edu/~stedt-cgi/' +\
        'rootcanal.pl/group/'
        self.compile_patterns()

    def compile_patterns(self):
        self.h1_pattern = re.compile('(<h1><a.*?<\/a>(.*?)<\/h1>)')
        self.h3_pattern = re.compile('(<h3><a.*?<\/a>(.*?)<\/h3>)')
        self.a_pattern = re.compile('(.*?<(a.*?)>(.*?)<\/a>)', re.DOTALL)

    def parse(self):
        for d in self.parse_sources():
            yield d

    def parse_sources(self):
        langspec_html = get_html(self.langspec_url)
        for d in self.generate_langspec_dicts(langspec_html):
            yield d
        austronesian_html = get_html(self.austronesian_url)
        for d in self.generate_austronesian_dicts(austronesian_html):
            yield d
        bantu_html = get_html(self.bantu_url)
        for d in self.generate_bantu_dicts(bantu_html):
            yield d
        indo_european_html = get_html(self.indo_european_url)
        for d in self.generate_indo_european_dicts(indo_european_html):
            yield d
        sealand_html =  get_html(self.sealang_url)
        for d in self.generate_sealang_dicts(sealand_html):
            yield d
        stedt_html = get_html('{}1'.format(self.stedt_base_url))
        for d in self.generate_stedt_dicts(stedt_html):
            yield d
            
    def generate_langspec_dicts(self, html):
        blocks = self.h1_pattern.split(html)[1:]
        found = False
        for b in blocks:
            if found:
                break
            if b == 'Language Specific Projects':
                found = True
        for i, sb in enumerate(self.h3_pattern.split(b)):
            if i % 3 == 2:
                yield {'name': sb, 'endangered_langspec': True}

    def generate_austronesian_dicts(self, html):
        tabular = html.split('<table>')[1].split('</table>')[0]
        for row in tabular.split('<tr>')[2:]:  # 0.th is header
            cell = row.split('<td>')[2]
            lang = cell.split('"')[3].replace("&#039;", "'")
            yield {'name': lang, 'endangered_lex': True}

    def generate_bantu_dicts(self, html):
        p = HTMLParser()
        tabular = html.split('<table')[1].split('</table>')[0]
        for row in tabular.split('<tr>')[2:]:  # 0.th is header
            cell = row.split('<td>')[2]
            lang = p.unescape(cell)
            lang = lang.replace('*', '').replace(u'\xa0', '')
            match = self.a_pattern.match(lang)
            if match:
                lang = match.groups()[2]
            yield {'name': lang, 'endangered_lex': True}

    def generate_indo_european_dicts(self, html):
        tabular = html.split('<table')[2].split('</table>')[0]
        for row in tabular.split('<tr')[2:]:
            lang_cell = row.split('<td>')[2]
            lang_cell = lang_cell.replace('[Legacy]', '')
            lang = self.a_pattern.match(lang_cell).groups()[2].strip()
            sil_cell = row.split('<td>')[3]
            sil = self.a_pattern.match(sil_cell).groups()[2].strip()
            d = {'name': lang, 'sil': sil, 'endangered_lex': True}
            if len(sil) == 0:
                del d['sil']
            yield d 

    def generate_sealang_dicts(self, html):
        tabular = html.split('<!--Library-->')\
                [1].split('<table align="center">')[1].split('</table>')[0]
        match = self.a_pattern.match(tabular)
        while match:
            lang = match.groups()[2]
            yield {'name': lang, 'endangered_lex': True}
            tabular = tabular[len(match.groups()[0]):]
            match = self.a_pattern.match(tabular)

    def generate_stedt_dicts(self, html):
        group_tabular = html.split('<table>')[1].split('</table>')[0]
        match = self.a_pattern.match(group_tabular)
        '''
        parse http://stedt.berkeley.edu/~stedt-cgi/rootcanal.pl/group/1
        for getting language groups
        '''
        while match:
            found_names = set([])
            group_tabular = group_tabular[len(match.groups()[0]):]
            group_index = match.groups()[1].split('/')[-1]
            html = get_html('{}{}'.format(self.stedt_base_url, group_index))
            # download and parse page index by group
            tabular = html.split('<table>')[2].split('</table>')[0]
            for row in tabular.split('<tr>')[2:]:  # head
                data = row.split('<td>')
                sil = data[1].split('</td>')[0]
                m = self.a_pattern.match(sil)
                if m:
                    sil = m.groups()[2]
                name = data[2].split('</td>')[0]
                m = self.a_pattern.match(name)
                if m:
                    name = m.groups()[2]
                name = name.strip('*')
                if name in found_names:
                    continue
                found_names.add(name)
                d = {'name': name, 'sil': sil, 'endangered_lex': True}
                if sil == 'n/a':
                    del d['sil']
                yield d

            match = self.a_pattern.match(group_tabular)


def main():
    a = EndangeredResourcesParser()
    for d in a.parse():
        print d

if __name__ == "__main__":
    main()
