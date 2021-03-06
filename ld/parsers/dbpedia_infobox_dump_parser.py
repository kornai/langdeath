"""This parser needs dbpedia dump to be downloaded from
http://wiki.dbpedia.org/Downloads39
Three files are needed: Raw Infobox Properties, nt, cleaned mapping properties
to be put into @basedir, and
a file containing the titles (one per line) of dbpedia type Language,
(see Mapping Based Types Dump) which has to be put in
@basedir/@needed_fn (see constructor).
"""

import re
import sys

from dbpedia_base_parser import DbpediaNTBaseParser


class DbpediaRawInfoboxParser(DbpediaNTBaseParser):

    def __init__(self, basedir):
        super(DbpediaRawInfoboxParser, self).__init__(basedir)

    def load_data_for_parsing(self):
        self.fh = open('{0}/raw_infobox_properties_en.nt'.format(self.basedir))

    def clean_dict(self, lang):
        d = {}
        d['name'] = lang['name']
        lang = dict((k.split("/")[-1].rstrip(">"), v)
                     for k, v in lang.iteritems())
        if 'glotto' in lang and lang['glotto'] != [u'none']:
            d['other_codes'] = {}
            d['other_codes']['glotto'] = lang['glotto']
        if 'linglist' in lang and lang['linglist'] != [u'none']:
            if 'other_codes' not in d:
                d['other_codes'] = {}
            d['other_codes']['linglist'] = lang['linglist']
        if (len(lang.get('lc', [])) > 0 and
                len(lang.get('lc', [])) == len(lang.get('ld', []))):
            d['lc_ld'] = zip(lang['lc'], lang['ld'])
        if 'other_codes' in d or 'lc_ld' in d:
            yield d

    def parse(self):
        return self.parse_or_load()

    def parse_all(self):
        self.load_data_for_parsing()
        for lang in self.parse_languages():
            for d in self.clean_dict(lang):
                if len(d) > 0:
                    yield d


class DbpediaMapPropertiesParser(DbpediaNTBaseParser):

    def __init__(self, basedir):
        super(DbpediaMapPropertiesParser, self).__init__(basedir)
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

    def parse(self):
        # this is just an alias to work the same way as other parsers
        return self.parse_or_load()

    def parse_all(self):
        self.load_data_for_parsing()
        for lang in self.parse_languages():
            for d in self.clean_dict(lang):
                if len(d) > 0 and "sil" in d and len(d["sil"]) == 1:
                    d["sil"] = d["sil"][0]
                    yield d


def main():

    bd = sys.argv[1]
    parser = DbpediaRawInfoboxParser(bd)
    #for d in parser.parse():
    #    print d
    #parser = DbpediaMapPropertiesParser(bd)
    for d in parser.parse_or_load():
        print d

if __name__ == '__main__':
    main()
