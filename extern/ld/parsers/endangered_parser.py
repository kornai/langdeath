from base_parsers import OfflineParser
from os import listdir, path
from time import sleep
from contextlib import closing
import re
import urllib2
import logging


class EndangeredParser(OfflineParser):

    """ Parser class for http://www.endangeredlanguages.com/
    The search result pages needs to be downloaded manually.
    Keep pressing "More results" on this page until all languages are listed:
    http://www.endangeredlanguages.com/lang/search/#/?endangerment=U,S,AR,V,T,E,CE,SE,AW,D&sample_types=N,A,V,D,I,G,L&locations=known,unknown&q=&type=code
    Save the HTML in one or more pieces and provide the directory
    where it's located as the first argument of the parser class.
    """

    def __init__(self, category_pages=None):
        self.base_url = 'http://www.endangeredlanguages.com/'
        self.lang_url_prefix = 'lang/'
        self._category_pages = None
        if not category_pages:
            self.category_pages_basedir = 'html/'
        else:
            self.category_pages_basedir = category_pages
        self.lang_url_re = re.compile("a href=\"/lang/(.+)\"", re.UNICODE)
        self.setup_handlers()
        self.create_field_map()

    def create_field_map(self):
        self.field_map = {
            'ALSO KNOWN AS': 'alternative name',
            'LANGUAGE CODE': 'sil',
            'CODE AUTHORITY': 'iso_type',
            'VARIANTS & DIALECTS': 'dialects',
        }

    def setup_handlers(self):
        url_fields = [
            'ALSO KNOWN AS',
            'CLASSIFICATION',
            'ORTHOGRAPHY',
            'ADDITIONAL COMMENTS',
        ]
        simple_fields = [
            'CODE AUTHORITY',
            'LANGUAGE CODE',
        ]
        table_fields = [
            'VARIANTS & DIALECTS'
        ]
        self.skip_fields = set([
            'DOWNLOAD',
            'MORE RESOURCES',
        ])
        self.field_handlers = dict([
            (url_field, self.url_field_handler) for url_field in url_fields])
        self.field_handlers.update([
            (simple_field, self.simple_field_handler)
            for simple_field in simple_fields])
        self.field_handlers.update([
            (table_field, self.table_field_handler) for table_field in table_fields])

    @property
    def category_pages(self):
        """ The language lists can be downloaded by category which might be
        easier to do manually than handling the whole page.
        They need to be stored in the same directory.
        This property filters all files in a given directory to html files.
        """
        if not self._category_pages:
            self._category_pages = [path.join(self.category_pages_basedir, i)
                                    for i in
                                    filter(lambda x: x.endswith('.html'),
                                           listdir(self.category_pages_basedir))]
        return self._category_pages

    def parse_pages(self):
        for lang_url in self.lang_urls():
            with closing(urllib2.urlopen(lang_url)) as page:
                text = page.read().decode('utf8')
                d = self.parse_lang_page(text, lang_url)
                yield d
            sleep(0.5)

    def parse_lang_page(self, text, url=''):
        lang_data = dict()
        lang_data['name'] = self.get_lang_name(text)
        self.parse_header(text, lang_data, url)
        lang_sect = filter(lambda x: 'Language metadata' in x,
                           text.split('<section>'))
        lang_data.update(self.get_lang_info(lang_sect[0]))
        return lang_data

    def parse_header(self, text, lang_data, url=''):
        subheader = text.split('<article class="subheader">')[1].split(
            '</article>')[0]
        lang_data['family'] = self.get_family(subheader, url)
        lang_data['category'] = self.get_category(subheader, url)

    def get_family(self, text, url=''):
        try:
            t = text.split('<em>')[0].split('<div>')[-1]
            t = t.split('<p>')[1].split('</p>')[0]
            return [t.strip().lstrip('Classification: ')]
        except ValueError as e:
            logging.exception('While parsing language family on site {0}, {1}'.format(
                url, e))

    def get_category(self, text, url=''):
        if not '<em>' in text:
            return None
        try:
            t = text.split('<em>')[0].split('<div>')[-1]
            t = text.split('</div>')[0]
            t = t.split('<p>')[1].split('</p>')[0]
            return t.strip()
        except ValueError as e:
            logging.exception('While parsing language category on site {0}, {1}'.format(
                url, e))

    def get_lang_name(self, text, url=''):
        try:
            title_text = text.split('<title>')[1].split('</title>')[0]
            langname = title_text.split('Endangered Languages Project -')[1].strip()
            return langname
        except ValueError as e:
            logging.exception('While parsing language name on site {0}, {1}'.format(
                url, e))

    def get_lang_info(self, text):
        parts = text.split('<label>')
        lang_info = dict()
        for part in parts[1:]:
            label = part.split('</label>')[0].strip()
            if label in self.skip_fields:
                continue
            if not label in self.field_handlers:
                logging.warning('Invalid field: {0}'.format(label))
                continue
            if label in self.field_map:
                lang_info[self.field_map[label]] = self.field_handlers[label](part)
        return lang_info

    def url_field_handler(self, field):
        p = field.split('<p class="smaller">')[1]
        p = p.split('<a href')[1]
        p = p.split('</a>')[0]
        p = p.split('>')[1].strip()
        return [i.strip() for i in p.split(',')]

    def simple_field_handler(self, field):
        p = field.split('<p class="smaller">')[1]
        p = p.split('</p>')[0].strip()
        return [i.strip() for i in p.split(',')]

    def table_field_handler(self, field):
        p = field.split('<ul class="square">')[1]
        li = p.split('<li>')
        fields = list()
        for l in li[1:]:
            l2 = l.split('<a href')[1]
            l2 = l.split('</a>')[0]
            fields.append(l2.split('>')[2].strip())
        return fields

    def lang_urls(self):
        for fn in self.category_pages:
            for url in self.iter_urls_in_file(fn):
                yield self.base_url + self.lang_url_prefix + url

    def iter_urls_in_file(self, fn):
        with open(fn) as f:
            for url in self.lang_url_re.finditer(f.read()):
                yield url.group(1)


if __name__ == '__main__':
    from sys import argv
    p = EndangeredParser(argv[1])
    cnt = 0
    import pprint
    for lang in p.parse_pages():
        pprint.pprint(lang)
        break
