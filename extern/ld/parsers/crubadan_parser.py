import csv
import json
import os
from zipfile import ZipFile
import urllib2
import logging

from utils import get_html

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException

class CrubadanParser(OnlineParser):

    def __init__(self, data_dir):
        self.needed_keys = {'m_iso_639_3_code': 'sil',
                            'name_english': 'name',
                            'm_bcp_47_code': 'other_codes',
                            'm_documents_crawled': 'cru_docs',
                            'm_language_name_native': 'native_name',
                            'altnames': 'alt_names',
                            'watchtower': 'cru_watchtower',
                            'udhr': 'cru_udhr',
                            'speller': 'cru_floss_splchk'
        }
        self.url1 = 'http://crubadan.org/writingsystems.csv?sEcho=1&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc'    #nopep8
        self.script_url = 'http://crubadan.org/writingsystems.csv?sEcho=1&iSortingCols=1&iSortCol_0=4&sSortDir_0=asc&sSearch_4='    #nopep8
        self.data_dir = data_dir
        self.file_url = 'http://crubadan.org/files'
 
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

    def generate_dicts_from(self, csv):        
        
        self.get_scripts(self.url1)
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
    

    def get_word_data(self, code):
        
        zip_fn = '{}/{}.zip'.format(self.data_dir, code)
        try:
            if not os.path.exists(zip_fn):
                url = '{}/{}.zip'.format(self.file_url, code)
                zip_ = urllib2.urlopen(url)
                f = open(zip_fn, 'w')
                f.write(zip_.read())
                f.close()
            zipfile = ZipFile(zip_fn)
            word_string = zipfile.open('{}-words.txt'.format(code)).read()
            return sum([int(l.split(' ')[1]) for l in word_string.split('\n')[:-1]])
        except urllib2.HTTPError:
            logging.info('Failed to download {}'.format(url))
        except KeyError:
            logging.info('No word list found in {}.zip'.format(code))
        return 0    


    def parse(self):
        return self.parse_or_load()

    def parse_all(self):
        for d in self.generate_dicts_from(csv):
            d['cru_words'] = self.get_word_data(d['other_codes']['bcp_47'])
            yield d

def main():

    import sys

    parser = CrubadanParser(sys.argv[1])
    for d in parser.parse():
        print repr(d)

if __name__ == '__main__':
    main()

