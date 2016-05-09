from base_parsers import OnlineParser
from utils import get_html


class BiblesParser(OnlineParser):

    def __init__(self):
        self.url = "https://bibles.org/versions"
    
    def generate_pairs(self, html):
        needed = html.split('<div id="version_index_list">')[1]
        for langblock in needed.split('<li data-lang')[1:]:
            code = langblock.split('"')[1]
            if code in ['eng-US', 'eng-GB']:
                code = 'eng'
            name = langblock.split('<span class="lang-name">')[1].split(
                '</span>')[0] 
            yield name, code

    
    def parse(self):
        html = get_html(self.url)
        for lang, code in self.generate_pairs(html):
            yield {'name': lang, 'sil': code, 'on_bible_org': True}

def main():
    bp = BiblesParser()
    for d in bp.parse():
        print d

if __name__ == '__main__':
    main()
