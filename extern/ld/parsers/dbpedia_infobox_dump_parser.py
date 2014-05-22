"""This parser needs dbpedia dump to be downloaded from
http://wiki.dbpedia.org/Downloads39
The file needed is Raw Infobox Properties, nt
file has to be put into @basedir, see constructor
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

    def __init__(self, basedir='dbpedia_dumps'):

        self.basedir = basedir
        self.def_result_fn = "saved_infobox_results.pickle"
        self.fh = open('{0}/raw_infobox_properties_en.nt'
                       .format(self.basedir))
        self.needed_properties = set(['spokenIn', 'altname', 'iso',
                                      'lc', 'ld', 'name', 'nativename',
                                      'script', 'states', 'nation', 'comment'])
        self.multiple_properties = set(['spokenIn', 'altname', 'states'])
        self.splitters = re.compile('[,;]')

    def generate_language_blocks(self):

        l = self.fh.readline()
        block = []
        old_lang_name = ''
        for l in self.fh:
            if l[0] == '#':
                yield block
                break
            url = l.split(' ')[0]
            url = url.split('/')[4][:-1]
            if url[-9:] != '_language':
                continue
            lang_name = url[:-9]
            if lang_name != old_lang_name:
                if old_lang_name != '':
                    yield old_lang_name, block
                old_lang_name = lang_name
                block = []
            data = l.decode('unicode_escape').strip().split(' ')
            block.append((data[1], ' '.join(data[2:-1])))

    def make_dict(self, language, block):

        d = {}
        for pair in block:
            property_, value_ = pair
            property_ = property_.split('/')[4][:-1]
            if property_ not in self.needed_properties:
                continue
            value_ = value_[1:-4]
            if property_ in self.multiple_properties:
                if property_ not in d:
                    d[property_] = []
                for v in self.splitters.split(value_):
                    v_stripped = v.strip()
                    if v_stripped != '':
                        d[property_].append(v_stripped)
            else:
                d[property_] = value_
        return d

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

            d = self.make_dict(language, block)
            if len(d) > 0:
                yield d


def main():

    parser = DbpediaInfoboxParser(sys.argv[1])
    parser.parse_and_save()


if __name__ == '__main__':
    main()
