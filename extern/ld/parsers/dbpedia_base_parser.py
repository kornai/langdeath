import urllib

from base_parsers import OfflineParser


class DbpediaNTBaseParser(OfflineParser):
    def __init__(self, basedir):
        self.basedir = basedir

    def parse_languages(self):
        needed_fn = 'dbpedia_ontology_languages'
        self.needed_titles = set([l.strip('\n')
            for l in open('{0}/{1}'.format(self.basedir, needed_fn))])
        actual_lang = {}
        for l in self.fh:
            if l[0] == "#":
                continue
            data = l.strip('\n').decode('unicode_escape').split(' ', 2)
            page, key, value = data
            value = self.clean_value(value)
            key = self.clean_key(key)
            page = page.split('/')[4].split('>')[0]
            page_utf = urllib.unquote(page.encode('utf-8'))
            #print repr(page), repr(key), repr(value), repr(actual_lang)
            if page_utf not in self.needed_titles:
                if len(actual_lang) > 0:
                    yield actual_lang
                actual_lang = {}
                continue
            name = self.get_language_from_title(page_utf)
            if len(actual_lang) == 0:
                actual_lang['name'] = name
            else:
                if name != actual_lang['name']:
                    yield actual_lang
                    actual_lang = {}
                    actual_lang['name'] = name

            actual_lang.setdefault(key, []).append(value)
        if len(actual_lang) > 0:
            yield actual_lang

    def get_language_from_title(self, title_utf):
        words = title_utf.split('_')
        if words[-1] in ['language', 'languages']:
            return urllib.unquote(' '.join(words[:-1])).decode('utf-8')
        return urllib.unquote(' '.join(words)).decode('utf-8')

    def clean_key(self, key):
        if "<http://dbpedia.org/ontology/" in key:
            return urllib.unquote(key.split("/")[-1].split(">")[0])
        else:
            return key
    
    def clean_value(self, value):
        if "@en" in value:
            return value[1:-6]
        elif "http://dbpedia.org/resource/" in value:
            return self.get_language_from_title(
                urllib.unquote(value.split("/")[-1].split(">")[0]).encode('utf-8'))
        elif "<http://www.w3.org/2001/XMLSchema#string>" in value:
            return value.split('"')[1]
        else:
            return value


