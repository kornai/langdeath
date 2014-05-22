"""This parser needs dbpedia short abstract dump (nt) to be downloaded from
http://wiki.dbpedia.org/Downloads39
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


class DbpediaShortAbstractsParser(OfflineParser):

    def __init__(self, basedir='dbpedia_dumps'):

        self.basedir = basedir
        self.fh = open('{0}/short_abstracts_en.nt'
                       .format(self.basedir))
        self.patterns = self.compile_patterns()
        self.def_result_fn = "saved_shortabstract_results.pickle"

    def language_from_title(self, url):

        m = self.patterns['lang_in_url'].search(url)
        if m is None:
            return
        return m.groups()[0]

    def compile_patterns(self):

        patterns = {}
        patterns['lang_in_url'] = re.compile(r'.*/(.*?)_language>')

        splitter_phrases =\
                ['in\s[A-Za-z]+\sscript', 'in\s[A-Za-z]+\sdialect',
                           '[A-Z][a-z]*:', ';', ',', '/', '~',
                           '[^A-Za-z]or[^A-Za-z]', '[^A-Za-z]\u2013[^A-Za-z]']
        patterns['splitters'] =\
                re.compile('|'.join([w for w in splitter_phrases]))

        words_to_remove_from_pattern1 = \
                ['also', 'known', 'as', 'and', 'in', 'less', 'preceisely',
                 'called', 'formerly', 'literally', 'spelled', 'often',
                 'abbreviated', 'script', 'transliterated',
                 'rarely', 'sometimes', 'common', 'form', 'autonym',
                 'after', 'a', 'particular', 'speakers']

        words_to_remove_from_pattern2 = \
                ['dialect', 'precisely', 'alternatively', 'plural',
                'archaically', 'many', 'other', 'spellings', 'see', 'below',
                'proper', 'disambiguation', 'with', 'full', 'diactritics',
                'written', 'names', 'former', 'ruling', 'clan', 'by',
                'linguistics', 'etc.', 'to', 'be', 'exact']

        patterns['words_to_remove1'] = \
                re.compile('|'.join(['([^A-Za-z]|^)' + w + '([^A-Za-z]|$)'
                          for w in words_to_remove_from_pattern1]))

        patterns['words_to_remove2'] = \
                re.compile('|'.join(['([^A-Za-z]|^)' + w + '([^A-Za-z]|$)'
                          for w in words_to_remove_from_pattern2]))

        patterns['alt_name'] = re.compile(
            u'(^[\u03df-\u09FF\u0A01-\uffff]+)\s([\u0000-\u03DE]+)$|' +
            u'(^[\u0000-\u03DE]+)\s([\u03df-\u09FF\u0A01-\uffff]+)$')

        patterns['post_filter'] = re.compile('not\sto\sbe\sconfused\swith')
        return patterns

    def postprocess(self, found_langs, language):

        found_langs_2 = set([])
        for l in found_langs:
            if l[:3] == 'or ':
                l = l[3:]
            l = self.multiple_replacement(l, self.patterns['words_to_remove1'])
            l = self.multiple_replacement(l, self.patterns['words_to_remove2'])
            l = re.sub('[0-9]*', '', l)
            l = l.strip()
            l = l.strip('"')
            if l != language and l != '' and \
               self.patterns['post_filter'].match(l) is None\
               and len(l.split()) < 4:
                found_langs_2.add(l)
        return found_langs_2

    def multiple_replacement(self, orig_string, pat):

        m = pat.search(orig_string)
        string = orig_string
        while m is not None:
            string = re.sub(pat, ' ', string)
            m = pat.search(string)
        return string

    def parse_alternatives(self, language, abstract):

        found_langs = set([])
        first_bracket_pattern =\
                re.compile(language + '(\slanguage){0,1}[\s]{0,1}\((.*?)\)')
        first_bracket = first_bracket_pattern.search(abstract)
        if first_bracket is not None:
            bracket_string = first_bracket.groups()[1]
            for lang in re.split(self.patterns['splitters'], bracket_string):
                lang = lang.strip()
                m = self.patterns['alt_name'].search(lang)
                if m is not None:
                    for i in m.groups():
                        if i is not None:
                            found_langs.add(i.strip())
                else:
                    found_langs.add(lang)
            found_langs = self.postprocess(found_langs, language)
            return list(found_langs)
        else:
            return []

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

        for l in self.fh:

                data = l.strip('\n').decode('unicode_escape').split(' ')
                url, _, abstract = data[0], data[1], ' '.join(data[2:])
                language = self.language_from_title(url)
                if language is None:
                    continue
                alternatives = self.parse_alternatives(language, abstract)
                if len(alternatives) > 0:
                    yield {u'name': language, u'altname': alternatives}


def main():

    parser = DbpediaShortAbstractsParser(sys.argv[1])
    parser.parse_and_save()

if __name__ == '__main__':
    main()
