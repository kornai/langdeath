import csv
from utils import get_html
from base_parsers import OnlineParser

class GlottologParser(OnlineParser):

    def __init__(self):
        self.url1 = 'http://glottolog.org/glottolog/language.csv?type='\
                + 'languages&sEcho=1&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc'
        self.family_based_search_url = 'http://glottolog.org/glottolog/'\
                + 'language.csv?type=languages&sEcho=1&iSortingCols='\
                + '1&iSortCol_0=0&sSortDir_0=asc&sSearch_2='
        self.macro_area_based_family_search_url =\
                'http://glottolog.org/glottolog/language.csv?type='\
                + 'families&sEcho=1&iSortingCols=2&iSortCol_0=4&sSortDir_0='\
        + 'desc&iSortCol_1=0&sSortDir_1=asc&sSearch_1=Top-level+family&sSearch_='
        self.needed_keys = {'hid': 'sil',
                              'id': 'glotto',
                              'longitude': 'longitude',
                              'latitude': 'latitude',
                              'name': 'name',
                              }

    
    def get_family_urls(self, url1):
        html = get_html(url1)
        self.family_urls = set([])
        for relevant_dict in self.get_relevant_dict(html):
            self.family_urls.add()
    
    def get_top_level_families(self):
        '''
        to get all top level families we have to download another tabular,
        grouped by macro area for the same reason.
        '''
        tlfs = set([])
        for i in range(6):
            url = '{0}{1}'.format(self.macro_area_based_family_search_url, i)
            html = get_html(url)
            csv_reader = csv.reader(html.encode('utf-8').split('\n'))
            l = csv_reader.next()
            index = l.index('name')
            l = csv_reader.next()    
            while l: 
                tlfs.add(l[index])
                l = csv_reader.next()
        return tlfs
         
    def parse(self):
        '''
        we cannot download all data in one csv (maximum 2000 rows or so)
        so we download the the languages grouped by its top level family.
        '''
        for f in self.get_top_level_families():
            if f in ['Unattested', 'Bookkeeping']:
                continue
            html = get_html('{0}{1}'.format(self.family_based_search_url,
                                            '_'.join(f.split(' '))))
            csv_reader = csv.reader(html.encode('utf-8').split('\n'))
            l = csv_reader.next()
            self.needed_indeces = {}
            for k in self.needed_keys:
                i = l.index(k)
                self.needed_indeces[i] = k
            l = csv_reader.next()
            while l:
                d = {}
                for i in self.needed_indeces:
                    if l[i]:
                        if self.needed_indeces[i] == 'id':
                            d['other_codes'] = {'glotto': l[i]}
                        elif self.needed_indeces[i] in ['longitude', 'latitude']:
                            d[self.needed_indeces[i]] = float(l[i])
                        else:
                            d[self.needed_keys[self.needed_indeces[i]]] =\
                                    l[i].decode('utf-8')
                yield d
                l = csv_reader.next()            


def main():
    a = GlottologParser()
    for d in a.parse():
        print d
    
if __name__ == "__main__":
    main()
