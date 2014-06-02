from collections import defaultdict

from base_parsers import OfflineParser
from dbpedia_infobox_dump_parser import DbpediaInfoboxParser
from dbpedia_shortabstract_parser import DbpediaShortAbstractsParser


class DbpediaDumpsParser(OfflineParser):

    def __init__(self, sil_list, infobox_basedir='dbpedia_dumps',
                 shortabstract_basedir='dbpedia_dumps'):

        self.sil_list = sil_list
        self.infobox_parser = DbpediaInfoboxParser(infobox_basedir)
        self.shortabstract_parser = DbpediaShortAbstractsParser(
            shortabstract_basedir)

    def parse_and_save_dumps(self, fn=None):

        self.infobox_parser.parse_and_save(fn)
        self.shortabstract_parser.parse_and_save(fn)
        for d in self.parse(fn):
            yield d

    def parse(self, fn=None):

        for d in self.merge_dump_data(self.infobox_parser.read_results(fn),
                                      self.shortabstract_parser.
                                      read_results(fn)):
            yield d

    def merge_dump_data(self, res_info, res_abstract):

        res_info_sil_dict = defaultdict(list)
        for d in res_info:
            res_info_sil_dict[d[u'sil']].append(d)
        res_abstract_name_dict = dict([(d[u'name'], d) for d in res_abstract])
        for s in self.sil_list:
            if s not in res_info_sil_dict:
                continue
            for d1 in res_info_sil_dict[s]:
                if u'name' in d1 and d1[u'name'] in res_abstract_name_dict:
                    d2 = res_abstract_name_dict[d1[u'name']]
                    d1[u'altname'] = d1.get(u'altname', []) + d2[u'altname']
                yield d1


def main():

    p = DbpediaDumpsParser(['alt'])
    for d in p.parse():
        print repr(d)

if __name__ == "__main__":
    main()
