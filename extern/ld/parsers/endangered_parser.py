from base_parsers import OfflineParser
from time import sleep
from contextlib import closing
from collections import defaultdict
from HTMLParser import HTMLParser
import urllib2
import csv
import logging

logging.getLogger().setLevel(logging.DEBUG)


class EndangeredParser(OfflineParser):

    def __init__(self, sils_fn=None):
        self.base_url = 'http://www.endangeredlanguages.com/lang/'
        self.sils = list()
        if sils_fn:
            with open(sils_fn) as f:
                self.sils = [l.strip() for l in f]
        self.lang_data = defaultdict(lambda: defaultdict(dict))
        self.html_parser = HTMLParser()
        self.sil_id_map = open('sil_id.map', 'w')
        self.needed_fields_csv = {
            'Codes.code_authorities': 'iso_type',
            'Codes.classification': 'family',
        }

    def parse_all(self):
        for d in self.parse_all_csv():
            yield d

    def parse_all_csv(self):
        for lang_csv, sil in self.download_csvs():
            yield self.parse_csv(lang_csv, sil)

    def download_csvs(self):
        for sil in self.sils:
            logging.debug('Downloading CSV: ' + sil)
            try:
                with closing(urllib2.urlopen(self.base_url + sil + '/csv')) as page:
                    text = page.readlines()
                    yield text, sil
            except urllib2.HTTPError:
                continue
            finally:
                sleep(2)

    def parse_csv(self, csv_text, id_):
        r = csv.reader(csv_text)
        head = dict()
        l = [i.decode('utf8') for i in r.next()]
        for i, fd in enumerate(l):
            head[i] = fd
        table = list()
        sources = list()
        for line_ in r:
            line = [i.decode('utf8') for i in line_]
            table.append(line)
            sources.append(line[11])
            sil = line[37]
        lang_data = dict()
        lang_data['sil'] = sil
        for i, data in enumerate(table):
            for j, fd in enumerate(data):
                if fd and bool(fd) and fd.lower() != 'none':
                    self.add_and_unify(lang_data, head[j], fd, sources[i])
                    #self.lang_data[sil][(sources[i], mapping[j])] = fd.replace('\n', ' ')
                    #print fd.replace('\n', ' ')

                    #print(u'{0}\t{1}\t{2}\t{3}\t{4}'.format(id_, sil, sources[i], mapping[j], fd.replace('\n', ' ')).encode('utf8', 'ignore'))
        return lang_data

    def add_and_unify(self, lang_data, key_, val, source):
        if not key_ in self.needed_fields_csv:
            return
        key = self.needed_fields_csv[key_]
        if not key in lang_data:
            lang_data[key] = val
            return

    def parse_all_html(self):
        self.setup_handlers()
        self.create_field_map()
        for sil in self.sils:
            logging.debug('Downloading HTML: ' + sil)
            real_sil = ''
            try:
                with closing(urllib2.urlopen(self.base_url + sil)) as page:
                    text = self.html_parser.unescape(page.read().decode('utf8'))
                    try:
                        real_sil = self.parse_html(text, self.base_url + sil)
                        for key, val in sorted(self.lang_data[real_sil].iteritems()):
                            if type(val) == list:
                                val_str = '\t'.join(val)
                            else:
                                val_str = val.strip() if val else ''
                            print(u'{0}\t{1}\t{2}\t{3}\t{4}'.format(sil, real_sil, key[0], key[1], val_str).encode('utf8', 'ignore'))
                    except IndexError:
                        logging.exception('Unable to parse a section in {0} HTML'.format(sil))
            except urllib2.HTTPError:
                logging.exception('Unable to download HTML {0}'.format(sil))
            else:
                self.sil_id_map.write('{0}\t{1}\n'.format(sil, real_sil))
            finally:
                sleep(2)

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

    def parse_html(self, text, url=''):
        lang_data = dict()
        lang_data['name'] = self.get_lang_name(text)
        self.parse_header(text, lang_data, url)
        lang_sect = filter(lambda x: 'Language metadata' in x,
                           text.split('<section>'))
        lang_data.update(self.get_lang_info(lang_sect[0]))
        sil = lang_data['sil'][0]
        for k, v in lang_data.iteritems():
            self.lang_data[sil][('html', k)] = v
        self.add_by_source(text, sil)
        self.add_location_info(text, sil)
        return sil

    def add_location_info(self, text, sil):
        part = text.split('LOCATION INFORMATION')[-1].split('END CAROUSEL')[0]
        for sect, source in self.get_sections(part):
            for p in sect.split('<td>')[1:]:
                if 'COORDINATES' in p:
                    continue
                if 'data-topic="Location"' in p:
                    fd = p.split('"Location">')[1].split('</a>')[0].strip()
                    self.lang_data[sil][('html - ' + source, 'location')] = fd
                else:
                    logging.debug('Location field not recognized: ' + p.encode('utf8'))

    def add_by_source(self, text, sil):
        try:
            part = text.split('<h4>Language information by source')[1].split('<h4>Samples</h4>')[0]
        except IndexError:
            return
        for sect, source in self.get_sections(part, 1):
            for field, fd_type in self.get_fields_from_subsection(sect):
                self.lang_data[sil][('html - ' + source, fd_type)] = field

    def get_sections(self, text, offset=0):
        sections = text.split('Information from:')[offset + 1:]
        for section in sections:
            source = section.split('\n')[0].strip().rstrip('</p>').strip()
            yield section, source

    def get_fields_from_subsection(self, section):
        fields = section.split('<h5')
        if len(fields) < 2:
            return
        for field in fields[1:]:
            stripped = field.split('</h5>')[0]
            if 'class="endangered_level"' in stripped:
                fd = stripped.split('>')[1].split('<')[0].strip()
                yield fd, 'endangered_level'
            elif 'data-topic="Speakers"' in stripped:
                num = stripped.split('<')[-2].split('>')[-1]
                yield num, 'speakers'
            else:
                logging.debug('<h5> field not recognized: ' + stripped.encode('utf8'))

    def parse_header(self, text, lang_data, url=''):
        subheader = text.split('<article class="subheader">')[1].split(
            '</article>')[0]
        family = self.get_family(subheader, url)
        if family:
            lang_data['family'] = family
        category = self.get_category(subheader, url)
        if category:
            lang_data['category'] = category

    def get_family(self, text, url=''):
        try:
            t = text.split('<em>')[0].split('<div>')[-1]
            t = t.split('<p>')[1].split('</p>')[0]
            return [t.strip().lstrip('Classification: ')]
        except (ValueError, IndexError) as e:
            logging.exception('While parsing language family on site {0}, {1}'.format(
                url, e))
            return None

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
    p.parse_all_csv()
    #for sil, data in p.lang_data.iteritems():
        #for key, val in sorted(data.iteritems()):
            #print(u'{0}\t{1}\t{2}\t{3}'.format(sil, key[0], key[1], val).encode('utf8', 'ignore'))
    #import json
    #print p.lang_data
    #print json.dumps(p.lang_data)
