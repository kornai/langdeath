from base_parsers import OfflineParser
import re

class DbpediaShortAbstractsParser(OfflineParser):

    def __init__(self, basedir='dbpedia_dumps'):
        
        self.basedir = basedir
        self.fh = open('{0}/short_abstracts_en.nt'\
                       .format(self.basedir))
        self.patterns = self.compile_patterns()
    
    def language_from_title(self, url):

        m = self.patterns['lang_in_url'].search(url)
        if m == None:
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
                               
        words_to_remove_from_pattern = \
                ['also', 'known', 'as', 'and', 'in', 'less', 'preciseley', 
                 'called', 'formerly', 'literally', 'spelled', 'often',
                 'abbreviated', 'script', 'transliterated', 
                 'rarely', 'sometimes', 'common', 'form', 'autonym', 
                 'after', 'a', 'particular', 'speakers',
                'dialect', 'precisely', 'alternatively', 'plural', 'archaically', 
                'many', 'other', 'spellings', 'see', 'below', 'proper', 
                'disambiguation', 'with', 'full', 'diactritics', 'written', 'names',
                'former', 'ruling', 'clan', 'by', 'linguistics', 'etc.', 'to'
                'be', 'exact']

        patterns['words_to_remove'] = \
                re.compile('|'.join(['([^A-Za-z]|^)'+ w + '([^A-Za-z]|$)'
                          for w in words_to_remove_from_pattern])) 
        
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
            l = self.multiple_replacement(l, self.patterns['words_to_remove'])
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

    
    def parse(self):

        for l in self.fh:

                data = l.strip('\n').decode('unicode_escape').split(' ')
                url, _, abstract = data[0], data[1], ' '.join(data[2:])
                language = self.language_from_title(url)
                if language is None:
                    continue
                alternatives = self.parse_alternatives(language, abstract)
                if len(alternatives) > 0:
                    yield {u'name': language, u'altnames': alternatives}
           
def main():

    parser = DbpediaShortAbstractsParser()
    for d in parser.parse():
        print repr(d)

if __name__ == '__main__':
    main()
