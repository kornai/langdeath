from base_parsers import OfflineParser


class DbpediaNTBaseParser(OfflineParser):
    def __init__(self, basedir):
        self.basedir = basedir
        needed_fn = 'dbpedia_ontology_languages'
        self.needed_titles = set([l.strip('\n').decode('unicode_escape')
            for l in open('{0}/{1}'.format(self.basedir, needed_fn))])

    def parse_languages(self):
        actual_lang = {}
        for l in self.fh:
            if l[0] == "#":
                continue
            data = l.strip('\n').decode('unicode_escape').split(' ', 2)
            page, key, value = data
            page = page.split('/')[4].split('>')[0]
            if page not in self.needed_titles:
                if len(actual_lang) > 0:
                    yield actual_lang
                actual_lang = {}
                continue

            name = self.get_language_from_title(page)
            if len(actual_lang) == 0:
                actual_lang['name'] = name

            actual_lang.setdefault(key, []).append(value)
        if len(actual_lang) > 0:
            yield actual_lang

    def get_language_from_title(self, title):
        words = title.split('_')
        if words[-1] in ['language', 'languages']:
            return ' '.join(words[:-1])
        return ' '.join(words)


