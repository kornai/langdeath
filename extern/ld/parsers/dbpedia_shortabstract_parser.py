"""This parser needs dbpedia dumps to be downloaded from
http://wiki.dbpedia.org/Downloads39
Two files are needed: short abstracts dump (nt)
to be put into @basedir, and
a file containing the titles (one per line) of dbpedia type Language,
(see Mapping Based Types Dump) which has to be put in
@basedir/@needed_fn (see constructor).
"""

import re
import sys

from dbpedia_base_parser import DbpediaNTBaseParser


class DbpediaShortAbstractsParser(DbpediaNTBaseParser):

    def __init__(self, basedir):
        super(DbpediaShortAbstractsParser, self).__init__(basedir)
        self.patterns = self.compile_patterns()

    def load_data_for_parsing(self):
        self.fh = open('{0}/short_abstracts_en.nt'.format(self.basedir))

    def compile_patterns(self):

        patterns = {}
        splitter_phrases =\
                ['in\s[A-Za-z]+\s', '[A-Z][a-z]*:', ';', ',', '/', '~',
                '[^A-Za-z]or[^A-Za-z]', '[^A-Za-z]\u2013[^A-Za-z]',
                'in\s.*?\sdialect', 'in\s.*?\sscript', 'in\s.*?\slanguage']
        patterns['splitters'] =\
                re.compile('|'.join([w for w in splitter_phrases]))
        words_to_remove_from_pattern1 = \
                ['also', 'known', 'as', 'and', 'in', 'less', 'preceisely',
                 'called', 'formerly', 'literally', 'spelled', 'often',
                 'abbreviated', 'script', 'transliterated', 'spelling',
                 'rarely', 'sometimes', 'common', 'form', 'autonym',
                 'after', 'a', 'particular', 'speakers', 'contrasting']
        words_to_remove_from_pattern2 = \
                ['dialect', 'precisely', 'alternatively', 'plural', 'name',
                'archaically', 'many', 'other', 'spellings', 'see', 'below',
                'proper', 'disambiguation', 'with', 'full', 'diactritics',
                'written', 'names', 'former', 'ruling', 'clan', 'by',
                'linguistics', 'etc.', 'to', 'be', 'exact', 'rendered',
                'of', 'the']
        words_to_remove_from_pattern3 = \
                ['all', 'alternate', 'anglicised', 'autoethnonym', 'commonly',
                 'dialects', 'earlier', 'easier', 'elsewhere',
                 'endonym', 'erroneously', 'ethnonym', 'from', 'house',
                 'including', 'just', 'local', 'locally', 'means',
                 'misspelled', 'native', 'natively', 'obsolete',
                 'otherwise', 'pronounced', 'recorded', 'referred', 'rendered',
                 's', 'spelt', 'their', 'variety', 'variously', 'we']
        patterns['words_to_remove1'] = \
                re.compile('|'.join(['([^A-Za-z]|^)' + w + '([^A-Za-z]|$)'
                          for w in words_to_remove_from_pattern1]))
        patterns['words_to_remove2'] = \
                re.compile('|'.join(['([^A-Za-z]|^)' + w + '([^A-Za-z]|$)'
                          for w in words_to_remove_from_pattern2]))
        patterns['words_to_remove3'] = \
                re.compile('|'.join(['([^A-Za-z]|^)' + w + '([^A-Za-z]|$)'
                          for w in words_to_remove_from_pattern3]))
        patterns['alt_name'] = re.compile(
            u'(^[\u03df-\u09FF\u0A01-\uffff]+)\s([\u0000-\u03DE]+)$|' +
            u'(^[\u0000-\u03DE]+)\s([\u03df-\u09FF\u0A01-\uffff]+)$')
        patterns['first_filter'] = re.compile(
            '(not\sto\sbe\sconfused\swith\s|contrasting|so named after the)' +
            '.*?([,;]|$)')
        patterns['language_of_the'] = re.compile(
            '(language\sof\sthe[A-Z][a-z]+|language\sof\s[A-Z][a-z]+)')
        return patterns

    def postprocess(self, found_langs, language):

        found_langs_2 = set([])
        for l in found_langs:
            if l[:3] == 'or ':
                l = l[3:]

            if self.patterns['language_of_the'].search(l) is not None:
                found_langs_2.add(self.patterns['language_of_the']
                                  .search(l).groups()[0])
                continue

            l = self.multiple_replacement(l, self.patterns['words_to_remove1'])
            l = self.multiple_replacement(l, self.patterns['words_to_remove2'])
            l = self.multiple_replacement(l, self.patterns['words_to_remove3'])
            l = re.sub('[0-9]*', '', l)
            l = l.strip()
            l = l.strip('"')

            if l != language and l != '' and len(l.split()) < 4 and\
               l != '{0} language'.format(language):
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
        first_or_pattern =\
                re.compile(language + u'\sor([A-Za-z\s]+)\sis')
        first_or = first_or_pattern.search(abstract)
        if first_or is not None:
            return [first_or.groups()[0]]
        first_bracket_pattern =\
                re.compile(language + '(\slanguage|\slanguages)' +
                           '{0,1}[\s]{0,1}\((.*?)\)')
        first_bracket = first_bracket_pattern.search(abstract)
        if first_bracket is not None:
            bracket_string = first_bracket.groups()[1]
            bracket_string = re.sub(self.patterns['first_filter'],
                                    '', bracket_string)
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

    def parse(self):
        # this is just an alias to work the same way as other parsers
        return self.parse_or_load()

    def parse_all(self):
        self.load_data_for_parsing()
        for lang in self.parse_languages():
            name = lang["name"]
            abstract = lang["<http://www.w3.org/2000/01/rdf-schema#comment>"][0]
            alternatives = self.parse_alternatives(name, abstract)
            if len(alternatives) > 0:
                yield {u'name': name, u'altname': alternatives}


def main():

    bd = sys.argv[1]
    parser = DbpediaShortAbstractsParser(bd)
    parser.parse_and_save()


if __name__ == '__main__':
    main()
