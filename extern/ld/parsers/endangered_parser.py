from base_parsers import OfflineParser
from time import sleep
from contextlib import closing
from collections import defaultdict
from os import path
from HTMLParser import HTMLParser
import urllib2
import csv
import logging
import re

from endangered_utils import aggregate_l1

logging.getLogger().setLevel(logging.DEBUG)


class EndangeredParser(OfflineParser):

    def __init__(self, id_fn=None, offline_dir=''):
        self.base_url = 'http://www.endangeredlanguages.com/lang/'
        self.ids = list()
        if id_fn:
            with open(id_fn) as f:
                self.ids = [l.strip() for l in f]
        self.lang_data = defaultdict(lambda: defaultdict(dict))
        self.html_parser = HTMLParser()
        self.sil_id_map = open('sil_id.map', 'w')
        self.timeout = 2
        self.setup_handlers()
        self.offline_dir = offline_dir
        self.location_sep_re = re.compile(r'[,;]', re.UNICODE)
        self.set_fields = set(['altname', 'dialects', 'family', 'other_langs', 'scripts', 'places'])
        self.fields_to_unify = set(['iso_type', 'sil', 'name'])
        self.to_triplet = set(['endangered_level', 'speakers'])
        self.multiply_records = set(['location'])
        self.needed_fields_csv = {
            'Codes.code_authorities': 'iso_type',
            'Codes.classification': 'family',
            'Codes.code_authorities': 'iso_type',
            'Codes.code_val': 'sil',
            'Codes.dialect_varieties': 'dialects',
        }
        self.needed_fields_html = {
            'ALSO KNOWN AS': 'altname',
            'LANGUAGE CODE': 'sil',
            'CODE AUTHORITY': 'iso_type',
            'VARIANTS & DIALECTS': 'dialects',
            'location': 'location',
        }
        self.skip_h5 = set([
            'No samples have been submitted',
            'No documents have been added',
        ])

    def parse(self):
        return self.parse_or_load()

    def parse_all(self):
        for id_ in self.ids:
            logging.debug('Parsing: {0}'.format(id_))
            csv_data = self.download_and_parse_csv(id_)
            html_data = self.download_and_parse_html(id_)
            d = self.merge_dicts(csv_data, html_data)
            d['id'] = id_
            self.aggregate_numbers(d)
            yield d

    def aggregate_numbers(self, d):
        speakers = [i[2] for i in d.get('speakers', [])]
        aggr = aggregate_l1(speakers)
        d['speakers'].add(('aggregate', 'L1', aggr))

    def download_and_parse_csv(self, id_):
        offline_path = path.join(self.offline_dir, id_ + '.csv')
        if path.exists(offline_path):
            with open(offline_path) as f:
                return self.parse_csv(f.readlines(), id_)
        try:
            logging.debug('Downloading CSV: ' + str(id_))
            with closing(urllib2.urlopen(self.base_url + id_ + '/csv')) as page:
                lines = list(page)
                with open(offline_path, 'w') as f:
                    f.write(''.join(lines))
                return self.parse_csv(lines, id_)
        except urllib2.HTTPError:
            logging.warning('Unable to download CSV: ' + str(id_) + '. Perhaps this ID does not exist?')
            return {}
        finally:
            sleep(self.timeout)

    def download_and_parse_html(self, id_):
        offline_path = path.join(self.offline_dir, id_ + '.html')
        if path.exists(offline_path):
            with open(offline_path) as f:
                text = self.html_parser.unescape(f.read().decode('utf8'))
                try:
                    return self.parse_html(text, self.base_url + id_)
                except IndexError:
                    logging.exception('Unable to parse a section in {0} HTML'.format(id_))
                    raise
                    return {}
        try:
            with closing(urllib2.urlopen(self.base_url + id_)) as page:
                logging.debug('Downloading HTML: ' + str(id_))
                text = self.html_parser.unescape(page.read().decode('utf8'))
                with open(offline_path, 'w') as f:
                    f.write(text.encode('utf8'))
                try:
                    return self.parse_html(text, self.base_url + id_)
                except IndexError:
                    logging.exception('Unable to parse a section in {0} HTML'.format(id_))
                    return {}
        except urllib2.HTTPError:
            logging.exception('Unable to download HTML {0}'.format(id_))
            return {}
        finally:
            sleep(self.timeout)

    def parse_csv(self, csv_text, id_):
        r = csv.reader(csv_text)
        head = dict()
        headline = [i.decode('utf8') for i in r.next()]
        for i, fd in enumerate(headline):
            head[i] = fd
        table = list()
        sources = list()
        for line_ in r:
            line = [i.decode('utf8') for i in line_]
            table.append(line)
            sources.append(line[11])
        lang_data = dict()
        for i, data in enumerate(table):
            for j, fd in enumerate(data):
                if fd and bool(fd) and fd.lower() != 'none':
                    self.csv_add_and_unify(lang_data, head[j], fd, sources[i])
        return lang_data

    def csv_add_and_unify(self, lang_data, key_, val, source):
        if not key_ in self.needed_fields_csv:
            return
        key = self.needed_fields_csv[key_]
        val = [i.strip() for i in val.split(';') if i.strip()]
        lang_data[(source, key)] = val

    def merge_dicts(self, csv_data, html_data):
        lang_data = defaultdict(set)
        to_unify = defaultdict(list)
        self.add_values_from_dict(csv_data, lang_data, to_unify)
        self.add_values_from_dict(html_data, lang_data, to_unify)
        self.add_unifiable_fields(lang_data, to_unify)
        return lang_data

    def add_values_from_dict(self, src, tgt, to_unify):
        for (source, key), val in src.iteritems():
            if key in self.set_fields:
                if type(val) == unicode:
                    tgt[key].add(val)
                else:
                    tgt[key] |= set(val)
            elif key in self.to_triplet:
                tgt[key].add((source, val[0], val[1]))
            elif key in self.fields_to_unify:
                if type(val) == unicode:
                    to_unify[key].append(val)
                else:
                    to_unify[key].extend(val)
            elif key in self.multiply_records:
                for v in val:
                    tgt[key].add((source, v[0], v[1]))
            else:
                tgt[key].add((source, val))

    def add_unifiable_fields(self, data, to_unify):
        for key, vals in to_unify.iteritems():
            counts = dict()
            for v in set(vals):
                counts[v] = vals.count(v)
            max_ = max(counts.iteritems(), key=lambda x: x[1])
            data[key] = max_[0]

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
        lang_data[('html', 'name')] = self.get_lang_name(text)
        self.parse_header(text, lang_data, url)
        lang_sect = filter(lambda x: 'Language metadata' in x,
                           text.split('<section>'))
        lang_data.update(self.get_lang_info(lang_sect[0]))
        self.add_by_source(lang_data, text)
        self.add_location_info(lang_data, text)
        return lang_data

    def add_location_info(self, lang_data, text):
        part = text.split('LOCATION INFORMATION')[-1].split('END CAROUSEL')[0]
        for sect, source in self.get_sections(part):
            for p in sect.split('<td>')[1:]:
                if 'COORDINATES' in p:
                    continue
                if 'data-topic="Location"' in p:
                    fd = p.split('"Location">')[1].split('</a>')[0].strip()
                    locations = list(self.get_locations_from_field(fd))
                    lang_data[(source, 'location')] = locations
                else:
                    logging.debug('Location field not recognized: ' + p.encode('utf8'))

    def get_locations_from_field(self, fd):
        fd_clean = fd.replace(u'\u200e', '').rstrip('; ').replace('lat :', '').replace('. ', '.')
        numbers = list(self.location_sep_re.split(fd_clean))
        for i in range(0, len(numbers), 2):
            try:
                lon = float(numbers[i])
                lat = float(numbers[i + 1])
                yield float(lon), float(lat)
            except:
                logging.warning('Unable to parse location field: ' + fd.encode('utf8'))

    def add_by_source(self, lang_data, text):
        try:
            part = text.split('<h4>Language information by source')[1].split('<h4>Samples</h4>')[0].split('<!-- SAMPLES -->')[0]
        except IndexError:
            return
        for sect, source in self.get_sections(part, 1):
            for field, fd_type in self.get_fields_from_subsection(sect):
                lang_data[(source, fd_type)] = field
            for field, fd_type in self.get_subfields_from_subsection(sect):
                lang_data[(source, fd_type)] = field

    def get_subfields_from_subsection(self, section):
        fields = section.split('<dt')
        for field in fields[1:]:
            title = field.split('>')[1].split('</dt>')[0].split('<')[0].strip()
            if 'OTHER LANGUAGES USED BY THE COMMUNITY' in title:
                langs = list()
                for a in field.split('<a')[1:]:
                    l = a.split('Context">')[1].split('</a>')[0].strip().lstrip('and ')
                    langs.append(l)
                yield langs, 'other_langs'
            elif 'Scripts' in title:
                scripts = list()
                for a in field.split('<a')[1:]:
                    l = a.split('Other">')[1].split('</a>')[0].strip()
                    if not 'none' in l.lower():
                        scripts.append(l)
                if scripts:
                    yield scripts, 'scripts'
            elif 'PLACES' in title:
                places = list()
                for a in field.split('<a')[1:]:
                    l = a.split('Location')[1].split('>')[1].split('</a>')[0].strip()
                    places.extend([i.strip().replace('</a', '') for i in l.split(',')])
                if places:
                    yield places, 'places'

    def get_sections(self, text, offset=0):
        sections = text.split('Information from:')[offset + 1:]
        for section in sections:
            source = section.split('\n')[0].strip().rstrip('</p>').lstrip(u'\u201c').strip()
            yield section, source

    def get_fields_from_subsection(self, section):
        fields = section.split('<h5')
        if len(fields) < 2:
            return
        for field in fields[1:]:
            stripped = field.split('</h5>')[0]
            if 'class="endangered_level"' in stripped:
                fd = stripped.split('>')[1].split('<')[0].strip()
                try:
                    conf = field.split('<h6>')[1].split(' ')[0]
                except IndexError:
                    conf = 0
                yield (fd, int(conf)), 'endangered_level'
            elif 'data-topic="Speakers"' in stripped:
                num = stripped.split('<')[-2].split('>')[-1]
                yield ('L1', num.replace(',', '')), 'speakers'
            elif any(i in stripped for i in self.skip_h5):
                continue
            else:
                logging.debug('<h5> field not recognized: ' + stripped.encode('utf8'))

    def parse_header(self, text, lang_data, url=''):
        subheader = text.split('<article class="subheader">')[1].split(
            '</article>')[0]
        category = self.get_category(subheader, url)
        if category:
            lang_data[('html', 'family')] = [category]

    def get_family(self, text, url=''):
        try:
            t = text.split('<em>')[0].split('<div>')[-1]
            t = t.split('<p>')[1].split('</p>')[0]
            return t.strip().lstrip('Classification: ')
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
            return t.strip().lstrip('Classification: ')
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
            if label in self.needed_fields_html:
                lab = self.needed_fields_html[label]
                #if lab == 'category' and ('html', 'category') in lang_info:
                    #continue
                lang_info[('html', lab)] = self.field_handlers[label](part)
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
    p = EndangeredParser(argv[1], argv[2])
    p.parse_or_load()
