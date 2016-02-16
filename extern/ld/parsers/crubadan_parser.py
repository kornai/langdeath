import csv
import json

from utils import get_html

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException

class CrubadanParser(OnlineParser):

    def __init__(self):
        self.needed_keys = {'m_iso_639_3_code': 'sil',
                            'name_english': 'name',
                            'm_bcp_47_code': 'other_codes',
                            'm_documents_crawled': 'cru_docs',
                            'm_words': 'cru_words',
                            'm_language_name_native': 'native_name',
                            'altnames': 'alt_names',
                            'watchtower': 'cru_watchtower',
                            'udhr': 'cru_udhr',
                            'speller': 'cru_floss_splchk'
        }
        url1 = 'http://crubadan.org/writingsystems.csv?sEcho=1&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc'    #nopep8
        self.script_url = 'http://crubadan.org/writingsystems.csv?sEcho=1&iSortingCols=1&iSortCol_0=4&sSortDir_0=asc&sSearch_4='    #nopep8
        self.get_scripts(url1)
 
    def get_scripts(self, url1):
        html = get_html(url1)
        self.scripts = set([])
        for relevant_dict in self.get_relevant_dict(html):
            self.scripts.add(relevant_dict['script'].lower().strip('\n'))

    def get_relevant_dict(self, html):
        reader = csv.reader(html.encode('utf-8').split('\n'))
        line = reader.next()
        json_i = None
        for i, h in enumerate(line):
            if h == 'jsondata':
                json_i = i
                break
        while line:
            line = reader.next()
            if line != []:
                yield json.loads(line[json_i])

    def generate_script_dicts(self):
        for s in self.scripts:
            html = get_html('{0}{1}'.format(self.script_url, s))
            for d in self.get_relevant_dict(html):
                yield d

    def parse(self):
        for dict_ in self.generate_script_dicts():
            d = {}
            for k in dict_:
                if k not in self.needed_keys:
                    continue
                v = dict_[k].strip('\n')
                if k in ['m_documents_crawled', 'm_words']:
                    try:
                        v = int(v)
                    except:
                        v = None
                if k in ['altnames']:
                    if v == 'None':
                        v = []
                    else:
                        v = [i.strip() for i in v.split(',')]
                if k in ['m_language_name_native']:
                    if v == '(Unknown)':
                        continue
                if k in ['watchtower', 'udhr', 'speller']:    
                    if v in ['(Unknown)', '-', 'no']:
                        v = False
                    else:
                        v = True
                if k == 'm_bcp_47_code':        
                    v = {'bcp_47': v}
                d[self.needed_keys[k]] = v
            yield d    


def main():

    parser = CrubadanParser()
    for d in parser.parse():
        print repr(d)
            #print repr(d['native_name'])

if __name__ == '__main__':
    main()

