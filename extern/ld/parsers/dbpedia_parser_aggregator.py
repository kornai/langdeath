import sys

from base_parsers import OfflineParser
from dbpedia_infobox_dump_parser import DbpediaRawInfoboxParser, \
    DbpediaMapPropertiesParser
from dbpedia_shortabstract_parser import DbpediaShortAbstractsParser


class DbpediaParserAggregator(OfflineParser):

    def __init__(self, basedir):

        self.raw_infobox_parser = DbpediaRawInfoboxParser(basedir)
        self.properties_parser = DbpediaMapPropertiesParser(basedir)
        self.shortabstract_parser = DbpediaShortAbstractsParser(basedir)

    def parse(self):
        i_res = list(self.raw_infobox_parser.parse())
        sa_res = list(self.shortabstract_parser.parse())
        p_res = list(self.properties_parser.parse())

        for d in self.merge_dump_data(i_res, sa_res, p_res):
            if 'sil' in d or not "lc_ld" in d:
                yield d
            if "lc_ld" in d:
                for lc, ld in d["lc_ld"]:
                    child_d = {"sil": lc, "name": ld}
                    if "sil" in d and lc not in d["sil"]:
                        child_d["champion"] = d["sil"]
                    yield child_d
                    

    def merge_dump_data(self, res_info, res_abstract, res_prop):
        results = {}
        for res in [res_info, res_abstract, res_prop]:
            for langdict in res:
                n = langdict['name']
                if n not in results:
                    results[n] = langdict
                else:
                    results[n].update(langdict)
        for langdict in results.itervalues():
            if 'sil' in langdict and langdict['sil'] == 'none':
                del langdict['sil']
            yield langdict


def main():

    bd = sys.argv[1]
    p = DbpediaParserAggregator(bd)
    for d in p.parse():
        print d

if __name__ == "__main__":
    main()
