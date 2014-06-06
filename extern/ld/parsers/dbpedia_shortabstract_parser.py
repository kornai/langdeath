"""This parser needs dbpedia dumps to be downloaded from
http://wiki.dbpedia.org/Downloads39
Two files are needed: short abstracts dump (nt)
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
import cPickle

from base_parsers import OfflineParser


class DbpediaShortAbstractsParser(OfflineParser):

    def __init__(self, basedir='dbpedia_dumps', new_parse=False,
                 needed_fn='dbpedia_ontology_languages'):

        self.basedir = basedir
        self.def_result_fn = "saved_shortabstract_results.pickle"
        if new_parse is True:
            self.load_data_for_parsing()

    def load_data_for_parsing(self):
        self.fh = open('{0}/short_abstracts_en.nt'
                       .format(self.basedir))
        self.patterns = self.compile_patterns()
        self.needed_titles = set([l.strip('\n').decode('unicode_escape')
                                  for l in open(
                                      '{0}/{1}'
                                      .format(self.basedir, self.needed_fn))])

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

    def get_language_from_title(self, title):

        words = title.split('_')
        if words[-1] in ['language', 'languages']:
            return ' '.join(words[:-1])
        return ' '.join(words)

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

        l = self.fh.readline()
        for l in self.fh:
                if l[0] == '#':
                    continue
                data = l.strip('\n').decode('unicode_escape').split(' ')
                url, _, abstract = data[0], data[1], ' '.join(data[2:])
                title = url.split('/')[4].split('>')[0]
                if title not in self.needed_titles:
                    continue
                language = self.get_language_from_title(title)
                alternatives = self.parse_alternatives(language, abstract)
                if len(alternatives) > 0:
                    yield {u'name': language, u'altname': alternatives}


def main():

    parser = DbpediaShortAbstractsParser(new_parse=False)
    for d in parser.parse():
        print d


if __name__ == '__main__':
    main()
