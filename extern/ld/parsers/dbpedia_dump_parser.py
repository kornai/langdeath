from base_parsers import OfflineParser
import re


class DbpediaDumpParser(OfflineParser):

    def __init__(self, basedir='dbpedia_dumps'):

        self.basedir = basedir
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

    def parse(self):

        for language, block in self.generate_language_blocks():

            d = self.make_dict(language, block)
            if len(d) > 0:
                yield d


def main():

    parser = DbpediaDumpParser()
    for d in parser.parse():
        print repr(d)


if __name__ == '__main__':
    main()
