import re

from base_parsers import OnlineParser
from utils import get_html


class EndangeredResourcesParser(OnlineParser):

    def __init__(self):

        self.langspec_url = 'https://github.com/RichardLitt/endangered' +\
                '-languages#massive-dictionary-and-lexicography-projects'
        self.austronesian_url = 'http://language.psy.auckland.ac.nz/' +\
                'austronesian/language.php?group='
        self.compile_patterns()

    def compile_patterns(self):
        self.h1_pattern = re.compile('(<h1><a.*?<\/a>(.*?)<\/h1>)')
        self.h3_pattern = re.compile('(<h3><a.*?<\/a>(.*?)<\/h3>)')

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
            lang = cell.split('"')[3].replace("&#039;", "1")
            yield {'name': lang, 'endangered_lex': True}


def main():
    a = EndangeredResourcesParser()
    for d in a.parse():
        print d

if __name__ == "__main__":
    main()
