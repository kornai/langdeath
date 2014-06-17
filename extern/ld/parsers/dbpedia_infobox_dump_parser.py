"""This parser needs dbpedia dump to be downloaded from
http://wiki.dbpedia.org/Downloads39
Two files are needed: Raw Infobox Properties, nt
to be put into @basedir, and
a file containing the titles (one per line) of dbpedia type Language,
(see Mapping Based Types Dump) which has to be put in
@basedir/@needed_fn (see constructor).
Since dump is quite big, parsing is a little slow, so there is a
parse_and_save() method, that will pickle results to a file, and
read_results() method, that will read results from that file and return
in the same format as parse() does.
"""

import re
import sys
import cPickle

from dbpedia_base_parser import DbpediaNTBaseParser


class DbpediaRawInfoboxParser(DbpediaNTBaseParser):

    def __init__(self, basedir, new_parse=False):
        super(DbpediaRawInfoboxParser, self).__init__(basedir)
        self.def_result_fn = "saved_raw_infobox_results.pickle"
        if new_parse is True:
            self.load_data_for_parsing()

    def load_data_for_parsing(self):

        self.fh = open('{0}/raw_infobox_properties_en.nt'.format(self.basedir))

    def clean_dict(self, lang):
        d = {}
        d['name'] = lang['name']
        lang = dict((k.split("/")[-1].rstrip(">"), v)
                     for k, v in lang.iteritems())
        if (len(lang.get('lc', [])) > 0 and
                len(lang.get('lc', [])) == len(lang.get('ld', []))):

            d['lc_ld'] = zip(lang['lc'], lang['ld'])
            yield d

    def parse_and_save(self, ofn=None):
        if ofn is None:
            ofn = self.basedir + "/" + self.def_result_fn
        of = open(ofn, "wb")
        res = list(self.parse_dump())
        cPickle.dump(res, of, -1)

    def read_results(self, ifn=None):
        if ifn is None:
            ifn = self.basedir + "/" + self.def_result_fn
        ifile = open(ifn)
        return cPickle.load(ifile)

    def parse(self):
        # this is just an alias to work the same way as other parsers
        return self.read_results()

    def parse_dump(self):

        for lang in self.parse_languages():
            for d in self.clean_dict(lang):
                if len(d) > 0:
                    yield d


class DbpediaMapPropertiesParser(DbpediaNTBaseParser):

    def __init__(self, basedir='dbpedia_dumps', new_parse=False):
        super(DbpediaMapPropertiesParser, self).__init__(basedir)
        self.def_result_fn = "saved_map_properties_results.pickle"
        if new_parse is True:
            self.load_data_for_parsing()
        self.needed_keys = {
            "name": "name",
            "iso6393Code": "sil",
            # TODO
            # "spokenIn", "iso6391Code", "iso6393Code"
        }

    def load_data_for_parsing(self):

        self.fh = open('{0}/mappingbased_properties_cleaned_en.nt'.format(
            self.basedir))
        self.splitters = re.compile('[,;]')

    def generate_comma_sep_values(self, value_):

        for v in self.splitters.split(value_):
            v = v.strip()
            if v != '':
                yield v

    def clean_dict(self, lang):

        d = {}
        for k in lang.keys():
            if k in self.needed_keys:
                d[self.needed_keys[k]] = lang[k]
        yield d

    def parse_and_save(self, ofn=None):
        if ofn is None:
            ofn = self.basedir + "/" + self.def_result_fn
        of = open(ofn, "wb")
        res = list(self.parse_dump())
        cPickle.dump(res, of, -1)

    def read_results(self, ifn=None):
        if ifn is None:
            ifn = self.basedir + "/" + self.def_result_fn
        ifile = open(ifn)
        return cPickle.load(ifile)

    def parse(self):
        # this is just an alias to work the same way as other parsers
        return self.read_results()

    def parse_dump(self):
        for lang in self.parse_languages():
            for d in self.clean_dict(lang):
                if len(d) > 0:
                    yield d


def main():

    bd = sys.argv[1]
    parser = DbpediaRawInfoboxParser(bd, new_parse=True)
    parser.parse_and_save()
    #parser = DbpediaMapPropertiesParser(bd, new_parse=True)
    #parser.parse_and_save()

if __name__ == '__main__':
    main()
