from base_parsers import BaseParser, OnlineParser, OfflineParser
from collections import defaultdict
from utils import get_html
import os
import re

class FindBibleParser(BaseParser):

    def __init__(self, resdir):
        self.resdir = resdir

    def parse(self):
        for lang_code in self.get_lang_code():
            d = defaultdict(int)
            d['sil'] = lang_code
            for bible_page in self.get_bible_page(lang_code):
                parsed = self.parse_bible_page(bible_page)
                for k in parsed:
                    d[k] += parsed[k]
                    d['find_bible_all_versions'] += parsed[k]
            if len(d) > 1:        
                yield dict(d)    
    
    def get_bible_page(self, lang_code):
        for page in os.listdir('{}/{}'.format(self.resdir, lang_code)):
            yield open('{}/{}/{}'.format(self.resdir, lang_code, page)).read()

    def get_lang_code(self):
        raise NotImplementedError

    def parse_bible_page(self, bible_page):
        d = {}
        article = bible_page.split(
            '<article id="bible" class="row"')[1].split('</article>')[0]
        genres = article.split('<h2 class="icon-')[1:]
        for g in genres:
            tag = g.split('"')[0]
            bible_list = g.split('<ul>')[1].split('</ul>')[0]
            bible_len = len(bible_list.split('<li>')) - 1
            d['findbible_{}'.format(tag.lower())] = bible_len
        return d
        

class FindBibleOnlineParser(OnlineParser, FindBibleParser):

    def __init__(self, resdir, sils):
        self.sils = sils
        self.base_url = 'https://find.bible'
        self.extract_pattern = re.compile(
            '.*?<a href="\/bibles\/(.*?)">*', re.DOTALL)
        super(FindBibleOnlineParser, self).__init__(resdir)

    def get_lang_code(self):
        for sil in self.sils:
            self.save_pages(sil)
            yield sil

    def save_pages(self, sil):
        langpage_html = get_html('{}/languages/{}'.format(
        self.base_url, sil))
        new_dir = '{}/{}'.format(self.resdir, sil)
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)
        for bible_id in self.extract_ids(langpage_html):
            if bible_id in os.listdir(new_dir):
                continue
            html = get_html('{}/bibles/{}'.format(
            self.base_url, bible_id))
            f = open('{}/{}'.format(new_dir, bible_id), 'w')
            f.write(html.encode('utf-8'))
        
    def extract_ids(self, langpage_html):
        tabular = langpage_html.split(
            '<section id="biblelist"')[1].split('\section')[0]
        matched = self.extract_pattern.match(tabular)
        while matched:
            yield matched.groups()[0]
            tabular = tabular[len(matched.groups()[0]):]
            matched = self.extract_pattern.match(tabular)


class FindBibleOfflineParser(OfflineParser, FindBibleParser):

    def __init__(self, resdir):
        self.sils = os.listdir(resdir)
        super(FindBibleOfflineParser, self).__init__(resdir)
    
    def get_lang_code(self):
        for sil in self.sils:
            yield sil
         
def main():
    
    import sys

    a = FindBibleOfflineParser(sys.argv[1])
    for d in a.parse():
        print d
        
if __name__ == "__main__":
    main()
