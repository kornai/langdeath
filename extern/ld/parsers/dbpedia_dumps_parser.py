"""This parser needs dbpedia dump to be downloaded from
http://wiki.dbpedia.org/Downloads39
Three files are needed: Raw Infobox Properties, nt
to be put into @basedir,
short abstracts dump (nt) to be put into @basedir, and
a file containing the titles (one per line) of dbpedia type Language,
(see Mapping Based Types Dump) which has to be put in
@basedir/@needed_fn (see constructor).
Since dumpis are quite big, parsing is a little slow, so there is a
parse_and_save() method, that will pickle results to two files files, and
parse() that only reads end merges results parsed from the two dump.
"""

from base_parsers import OfflineParser
from dbpedia_infobox_dump_parser import DbpediaInfoboxParser
from dbpedia_shortabstract_parser import DbpediaShortAbstractsParser


class DbpediaDumpsParser(OfflineParser):

    def __init__(self, new_parse=False,
                 infobox_basedir='dbpedia_dumps',
                 shortabstract_basedir='dbpedia_dumps'):

        self.infobox_parser = DbpediaInfoboxParser(infobox_basedir, new_parse)
        self.shortabstract_parser = DbpediaShortAbstractsParser(
            shortabstract_basedir, new_parse)
        self.needed_keys = {
            "name": "name",
            "altname": "alt_name",
            "nativename": "alt_name",
            "sil": "sil",
        }

    def parse_and_save_dumps(self, sil_list, fn=None):

        self.infobox_parser.parse_and_save(fn)
        self.shortabstract_parser.parse_and_save(fn)
        for d in self.parse(sil_list, fn):
            yield d

    def parse(self, fn=None):
        i_res = self.infobox_parser.read_results(fn)
        sa_res = self.shortabstract_parser.read_results(fn)

        for d in self.merge_dump_data(i_res, sa_res):
            new_d = {}
            for k in d.keys():
                if k in self.needed_keys:
                    new_d[self.needed_keys[k]] = d[k]
            yield new_d
            if "lc" in d and "ld" in d and len(d["lc"]) == len(d["ld"]):
                for i, sil in enumerate(d['lc']):
                    name = d['ld'][i]
                    if sil not in d["sil"]:
                        child_d = {"sil": sil, "name": name,
                                   "champion": d["sil"]}
                        yield child_d

    def merge_dump_data(self, res_info, res_abstract):

        res_abstract_name_dict = dict([(d[u'name'], d) for d in res_abstract])
        for d1 in res_info:
            if d1['sil'] == [u'none'] or d1['sil'] == ['n/a']:
                continue
            if u'name' in d1 and d1[u'name'][0] in res_abstract_name_dict:
                d2 = res_abstract_name_dict[d1[u'name'][0]]
                d1[u'altname'] = d1.get(u'altname', []) + d2[u'altname']
            yield d1


def main():

    p = DbpediaDumpsParser()
    for d in p.parse():
        print repr(d)

if __name__ == "__main__":
    main()
