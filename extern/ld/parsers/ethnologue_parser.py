import sys
import re
from utils import get_html

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException
from ld.lang_db import LanguageUpdate


class EthnologueParser(OnlineParser):

    def __init__(self):

        self.base_url = 'http://www.ethnologue.com/language'
        self.compile_patterns()
        self.needed_keys = {
            'ISO 639-3': 'sil',
            'Name': 'name',
            'Country': 'country',
            'Language Status': 'eth_status',
            'Population': 'eth_population'
        }

    def strip_nonstring(self, string):

        while len(string) > 0 and string[0] == '<':
            string = string.split('>')[1].split('<')[0]
        return string
   
  
    def normalize_numstring(self, num_str):
        return int(num_str.replace(',', '').replace('.', ''))
   
    def normalize_lang_status(self, l):
        lang_status_res = self.matchers['language_status'].search(l)
        if lang_status_res is not None:
            return lang_status_res.groups()[0]
        else:
            raise ParserException(
                'error in EthnologueParser.normalize_lang_status')

    def normalize_population(self, orig_l):
        
        l = orig_l
        population_all_res = self.matchers['population_all'].search(l)
        if population_all_res is not None:
            num_str = population_all_res.groups()[0] 
            return self.normalize_numstring(num_str)
        if self.matchers['nospeaker'].search(l) is not None:
            return 0
        l = re.sub(self.matchers['bracket'], '', l)
        l = re.sub(self.matchers['ethnic_population'], '', l)
        nums = []
        num_res = self.matchers['numstring'].search(l)
        while num_res:
            num_str = num_res.groups()[0]
            rest = num_res.groups()[1]
            num = self.normalize_numstring(num_str) 
            if not (1990 < num < 2014 and str(num) == num_str): # year
                nums.append(num)
            num_res = self.matchers['numstring'].search(rest)
        if len(nums) == 0:
            sys.stderr.write('no num found in line {0}\n'.format(orig_l))
            return 0
        return sorted(nums, reverse = True)[0]   

            
    def compile_patterns(self):
    
        self.matchers = {}
        self.matchers['population_all'] = re.compile(
                r'(Population total all countries|total population):' +
                 '([0-9]+[0-9\.,]*)')
        self.matchers['bracket'] = re.compile('\(.*?\)')
        self.matchers['ethnic_population'] = re.compile(
                 'Ethnic population:.*?\.')
        self.matchers['nospeaker'] = re.compile(
                 '(No remaining speakers.|No known L1 speakers.)')
        self.matchers['numstring'] = re.compile('([0-9]+[0-9\.,]*)(.*)')
        self.matchers['language_status'] =\
                re.compile('([0-9]{1,2}[ab]{0,1})\s')


    def parse_attachment_block(self, block):
        try:
            inner_dictionary = {}
            for item in re.split('<strong class=.*?>', block)[1:]:
                matcher = re.compile(
                    '(.*?)</strong><span class=.*?>(.*?)</span>')
                matched = matcher.match(item)
                if matched is not None:
                    key, value = matched.groups()
                    inner_dictionary[key] = value
            return inner_dictionary
        except Exception as e:
            raise ParserException(
                '{0} in EthnologueParser.parse_attachment_block()' +
                ' sil:{1}'.format(type(e), self.sil))

    def parse_row(self, row):
        try:
            key = row.split('</div>')[0].strip()
            value_wrapped = '</div>'.join(row.split('</div>')[1:])
            if len(value_wrapped.split('<div class="field-item even">')) > 1:
                value_extras = value_wrapped.split(
                    '<div class="field-item even">')[1].split('</div>')[0]
            else:
                value_extras = value_wrapped.split(
                    '<div class="field-item">')[1].split('</div>')[0]
            value = self.strip_nonstring(value_extras).strip()
            return key, value
        except Exception as e:
            raise ParserException(
                '{0} in EthnologueParser.parse_row(), at row\n{1} ' +
                'sil:{2}'.format(type(e), row, self.sil))

    def get_title(self, string):
        try:
            return string.split('<h1 class="title" id="page-title">')[1]\
                .split('</h1>')[0]
        except Exception as e:
            raise ParserException(
                '{0} in EthnologueParser.get_title() sil:{1}'.format(
                    type(e), self.sil))

    def get_country(self, string):
        try:
            return string.split('<h2>')[1].split('>')[1].split('</a')[0]
        except Exception as e:
            raise ParserException(
                '{0} in EthnologueParser.get_country(), sil:{1}'.format(
                    type(e), self.sil))

    def process_main_table_rows(self, string):
        try:
            main_rows = string.split('<div class="field-label">')[1:-1]\
                + [string.split('<div class="field-label">')[-1].split(
                    '<div class="attachment attachment-after">')[0]]
            res = []
            for row in main_rows:
                res.append(self.parse_row(row))
            return res
        except Exception as e:
            raise ParserException(
                '{0} in EthnologueParser.process_main_table_rows()' +
                ' sil:{1}'.format(type(e), self.sil))

    def get_attachment_title(self, attachment):
        try:
            if not '<div class="view-header">' in attachment:
                return None
            else:
                attachment_title = attachment.split('<h3>')[1].split(
                    '</h3>')[0]
                return attachment_title
        except Exception as e:
            raise ParserException(
                '{0} in EthnologueParser.get_attachment_title()' +
                ' sil:{1}'.format(type(e), self.sil))

    def get_attachment(self, string):
        try:
            attachment = string.split(
                '<div class="attachment attachment-after">')[1].split(
                '<aside class="grid-6 region region-sidebar-second "id="' +
                'region-sidebar-second">')[0]
            return attachment
        except Exception as e:
            raise ParserException(
                '{0} in EthnologueParser.get_attachment(), sil:{1}'.format(
                    type(e), self.sil))

    def get_attachment_blocks_titles(self, attachment):
        try:
            attachment_blocks = attachment.split(
                '<legend><span class="fieldset-legend"><span>')[1:]
            attachment_titles = [block.split('</span')[0] for
                                 block in attachment_blocks]
            return attachment_blocks, attachment_titles
        except Exception as e:
            raise ParserException(
                '{0} in EthnologueParser.get_attachment_blocks_titles(),sil:{1}'.format(type(e), self.sil))  # nopep8

    def get_attachment_dict(self, string):
        attachment = self.get_attachment(string)
        attachment_title = self.get_attachment_title(attachment)
        if attachment_title is not None:
            return
        attachment_dict = {}
        blocks, titles = self.get_attachment_blocks_titles(attachment)
        for i, block in enumerate(blocks):
            block_title = titles[i]
            attachment_dict[block_title] = {}
            inner_dictionary = self.parse_attachment_block(block)
            for key in inner_dictionary:
                attachment_dict[block_title][key] = inner_dictionary[key]
        return attachment_title, attachment_dict

    def parse(self, sil_codes):
        errors = set()
        for sil_code in sil_codes:
            try:
                self.sil = sil_code
                url = '{0}/{1}'.format(self.base_url, self.sil)
                html = get_html(url)
                dictionary = LanguageUpdate()
                dictionary.sil = sil_code
                dictionary.name = self.get_title(html)
                dictionary.country = self.get_country(html)
                main_items = self.process_main_table_rows(html)
                if main_items is not None:
                    for key, value in main_items:
                        if key in self.needed_keys:
                            setattr(dictionary, self.needed_keys[key], value)
                        # TODO
                        # put this into needed keys when done
                        if key == 'Population':
                            dictionary.population = self.normalize_population(value)
                        elif key == 'Language Status':
                            dictionary.status = self.normalize_lang_status(value)
                yield dictionary
            except ParserException:
                errors.add(sil_code)

        if len(errors) > 0:
            raise ParserException("error with sils: {0}".format(errors))


def main():

    sil_codes = sys.argv[1:]
    parser = EthnologueParser()
    for d in parser.parse(sil_codes):
        print d 

if __name__ == "__main__":
    main()
