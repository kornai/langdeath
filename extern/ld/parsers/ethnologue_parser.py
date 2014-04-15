import sys
import re

from base_parsers import OnlineParser
from ld.langdeath_exceptions import ParserException 
from utils import get_html


class EthnologueParser(OnlineParser):

    def __init__(self):

        self.base_url = 'http://www.ethnologue.com/language'
        self.compile_patterns()

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


    def parse_attachement_block(self, block):
        try:
            inner_dictionary = {}
            for item in re.split('<strong class=.*?>', block)[1:]:
                matcher = \
                re.compile('(.*?)</strong><span class=.*?>(.*?)</span>')
                matched = matcher.match(item)
                if matched is not None:
                    key, value = matched.groups()
                    inner_dictionary[key] = value
            return inner_dictionary
        except Exception as e:
            raise ParserException(
            '{0} in EthnologueParser.parse_attachement_block()' +
                ' sil:{1}'.format(type(e), self.sil))

    def parse_row(self, row):
        try:
            key = row.split('</div>')[0].strip()
            value_wrapped = '</div>'.join(row.split('</div>')[1:])
            if len(value_wrapped.split('<div class="field-item even">')) > 1:
                value_extras = value_wrapped.split(
                    '<div class="field-item even">')[1].split('</div>')[0]
            else:
                value_extras = value_wrapped.split('<div class="field-item">'
                )[1].split('</div>')[0]
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
            '{0} in EthnologueParser.get_title() sil:{1}'
                    .format(type(e), self.sil))

    def get_country(self, string):
        try:
            return string.split('<h2>')[1].split('>')[1].split('</a')[0]
        except Exception as e:
            raise ParserException(
            '{0} in EthnologueParser.get_country(), sil:{1}'
                .format(type(e), self.sil))

    def process_main_table_rows(self, string):
        try:
            main_rows = string.split('<div class="field-label">')[1:-1]\
                + [string.split('<div class="field-label">')[-1]
                .split('<div class="attachment attachment-after">')[0]]
            res = []
            for row in main_rows:
                res.append(self.parse_row(row))
            return res
        except Exception as e:
            raise ParserException(
            '{0} in EthnologueParser.process_main_table_rows()' +
                ' sil:{1}'.format(type(e), self.sil))

    def get_attachement_title(self, attachement):
        try:
            if not '<div class="view-header">' in attachement:
                return None
            else:
                attachement_title = attachement.split('<h3>')[1]\
                        .split('</h3>')[0]
                return attachement_title
        except Exception as e:
            raise ParserException(
            '{0} in EthnologueParser.get_attachement_title()' +
                ' sil:{1}'.format(type(e), self.sil))

    def get_attachement(self, string):
        try:
            attachement = string.split('<div class="attachment ' +
            'attachment-after">')[1].split('<aside class=' +
                     '"grid-6 region region-sidebar-second "id="' +
                                          'region-sidebar-second">')[0]
            return attachement
        except Exception as e:
            raise ParserException(
            '{0} in EthnologueParser.get_attachement(), sil:{1}'
                .format(type(e), self.sil))

    def get_attachement_blocks_titles(self, attachement):
        try:
            attachement_blocks = attachement.split('<legend><span class=' +
                                            '"fieldset-legend"><span>')[1:]
            attachment_titles = [block.split('</span')[0] for
                                 block in attachement_blocks]
            return attachement_blocks, attachment_titles
        except Exception as e:
            raise ParserException(
            '{0} in EthnologueParser.get_attachement_blocks_titles(),sil:{1}'
                .format(type(e), self.sil))

    def get_attachement_dict(self, string):
        attachement = self.get_attachement(string)
        attachement_title = self.get_attachement_title(attachement)
        if attachement_title is not None:
            return
        attachement_dict = {}
        blocks, titles =\
                self.get_attachement_blocks_titles(attachement)
        for i, block in enumerate(blocks):
            block_title = titles[i]
            attachement_dict[block_title] = {}
            inner_dictionary = self.parse_attachement_block(block)
            for key in inner_dictionary:
                attachement_dict[block_title][key]\
                        = inner_dictionary[key]
        return attachement_title, attachement_dict

    def parse(self, sil_codes):
        for sil_code in sil_codes:
            self.sil = sil_code
            url = '{0}/{1}'.format(self.base_url, self.sil)
            html = get_html(url)
            dictionary = {}
            dictionary['Name'] = self.get_title(html)
            dictionary['Country'] = self.get_country(html)
            main_items = self.process_main_table_rows(html)
            if main_items is not None:
                for i in main_items:
                    key, value = i
                    if key == 'Population':
                        dictionary[key] = self.normalize_population(value)
                    elif key == 'Language Status':
                        dictionary[key] = self.normalize_lang_status(value)
                    else:    
                        dictionary[key] = value
            attachement_info = self.get_attachement_dict(html)
            if attachement_info is not None:
                t, dict_ = attachement_info
                dictionary[t] = dict_
            yield dictionary


def main():

    sil_codes = sys.argv[1:]
    parser = EthnologueParser()
    for d in parser.parse(sil_codes):
        print d 

if __name__ == "__main__":
    main()
