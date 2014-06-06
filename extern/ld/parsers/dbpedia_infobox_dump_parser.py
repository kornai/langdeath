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

import sys
import re
import cPickle

from base_parsers import OfflineParser


class DbpediaInfoboxParser(OfflineParser):

    def __init__(self, basedir='dbpedia_dumps', new_parse=False,
                 needed_fn='dbpedia_ontology_languages'):

        self.basedir = basedir
        self.def_result_fn = "saved_infobox_results.pickle"
        if new_parse is True:
            self.load_data_for_parsing()

    def load_data_for_parsing(self):

        self.needed_titles = set([l.strip('\n').decode('unicode_escape')
                                   for l in open(
                                       '{0}/{1}'
                                       .format(self.basedir, self.needed_fn))])
        self.fh = open('{0}/raw_infobox_properties_en.nt'
                        .format(self.basedir))
        self.needed_properties = set(['spokenIn', 'altname', 'iso',
                                      'lc', 'ld', 'name', 'nativename',
                                      'script', 'states', 'nation',
                                     'iso1', 'iso2', 'iso2b', 'iso2t'])
        self.multiple_properties = set(['spokenIn', 'altname', 'states'])
        self.splitters = re.compile('[,;]')

    def generate_language_blocks(self):

        l = self.fh.readline()
        i = 0
        block = []
        old_title = ''
        for l in self.fh:
            i += 1
            if i % 100000 == 0:
                print i
            if l[0] == '#':
                # last line
                yield old_title, block
                break
            l = l.strip('\n').decode('unicode_escape')
            url = l.split(' ')[0]
            title = url.split('/')[4][:-1]
            if title not in self.needed_titles:
                continue
            if title != old_title:
                if old_title != '':
                    yield old_title, block
                old_title = title
                block = []
            data = l.split(' ')
            block.append((data[1], ' '.join(data[2:-1])))

    def clean_value(self, value_, property_):

        if value_[-3:] == '@en':
            return value_[1:-4]
        return value_.split('/')[4][:-1]

    def update_lc_ld_list(self, lc_ld_list, value_):

        if len(lc_ld_list) == 0 or len(lc_ld_list[-1]) == 2:
            lc_ld_list.append([value_])
        else:
            lc_ld_list[-1].append(value_)
        return lc_ld_list

    def make_dict(self, language, block):

        d = {}
        iso1_codes = []
        iso23_codes = []
        lc_ld_list = []
        for pair in block:
            property_, value_ = pair
            property_ = property_.split('/')[4][:-1]
            if property_ not in self.needed_properties:
                continue
            value_ = self.clean_value(value_, property_)
            if property_[:3] == 'iso':
                if len(value_) == 2:
                    iso1_codes.append(value_)
                else:
                    iso23_codes.append(value_)
            elif property_ in ['lc', 'ld']:
                lc_ld_list = self.update_lc_ld_list(lc_ld_list, value_)
            elif property_ in self.multiple_properties:
                if property_ not in d:
                    d[property_] = []
                for v in self.splitters.split(value_):
                    v_stripped = v.strip()
                    if v_stripped != '':
                        d[property_].append(v_stripped)
            else:
                d[property_] = value_

        d['iso1_codes'] = iso1_codes
        d['lc_ld'] = lc_ld_list
        for sil in self.choose_sil(iso23_codes, lc_ld_list, language):
            d['sil'] = sil
            yield d
        if self.check_lc_ld_list(lc_ld_list, language) == 'False':
            sys.stderr.write('{0}\n'.format(repr(block)))

    def check_lc_ld_list(self, lc_ld_list, language):
        for i in lc_ld_list:
            if len(i) != 2:
                return False
        return True

    def choose_sil(self, iso23_codes, lc_ld_list, language):

        if len(lc_ld_list) == 0 and len(iso23_codes) == 0:
            return ['n/a']
        if len(lc_ld_list) == 0:
            return [iso23_codes[-1]]
        if len(iso23_codes) == 0:
            return [sorted(lc_ld_list[0], key=lambda x:len(x))[0]]

        intersect = list(set(iso23_codes).intersection([i[0]
                                                        for i in lc_ld_list]))
        if len(intersect) == 0:  # macrolanguage
            return [iso23_codes[-1]]
        if len(intersect) > 1:
            sys.stderr.write('more than one SIL code for language {0}'
                             .format(language))
        return intersect

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

        for language, block in self.generate_language_blocks():
            for d in self.make_dict(language, block):
                if len(d) > 0:
                    yield d


def main():

    parser = DbpediaInfoboxParser(new_parse=False)
    for d in parser.parse():
        if d[u'sil'] == 'ger':
            print repr(d)


if __name__ == '__main__':
    main()
