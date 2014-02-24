import sys
import urllib2
import logging
import re

from base_parsers import OnlineParser

class EthnologueParser(OnlineParser):

    def __init__(self, sil_code):
        self.sil_code = sil_code
        self.url = 'http://www.ethnologue.com/language/{0}'.format(sil_code)
        self.dictionary = {}

    def strip_nonstring(self, string):
         
        while len(string) > 0 and string[0] == '<':
            string = string.split('>')[1].split('<')[0]
        return string
    
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
            logging.debug('{0} in EthnologueParser.parse_attachement_block()')\
                    .format(type(e))
     
    def parse_row(self, row):
        try: 
            key = row.split('</div>')[0].strip()
            value_wrapped = '</div>'.join(row.split('</div>')[1:])
            if len(value_wrapped.split('<div class="field-item even">')) > 1:
                value_extras = value_wrapped.split('<div class="field-item even">'
                )[1].split('</div>')[0]
            else:
                value_extras = value_wrapped.split('<div class="field-item">'
                )[1].split('</div>')[0]
            value = self.strip_nonstring(value_extras).strip()
            return key, value
        except Exception as e:
            logging.debug('{0} in EthnologueParser.parse_row(), at row\n{1}'\
                          .format(type(e), row))
            quit()
    
    def fill_title(self, string):
        try:
            title = string.split('<h1 class="title" id="page-title">')[1]\
                .split('</h1>')[0]
            self.dictionary['Name'] = title        
        except Exception as e:
            logging.debug('{0} in EthnologueParser.fill_title()'\
                    .format(type(e)))
            quit()

    def fill_country(self, string):
        try:
            country = string.split('<h2>')[1].split('>')[1].split('</a')[0]
            self.dictionary['Country'] = country
        except Exception as e:
            logging.debug('{0} in EthnologueParser.fill_country()'\
                    .format(type(e)))
            quit() 
    
    def fill_main_table_rows(self, string):
        try:
            main_rows = string.split('<div class="field-label">')[1:-1]\
                + [string.split('<div class="field-label">')[-1]\
                .split('<div class="attachment attachment-after">')[0]]
        except Exception as e:
            logging.debug('{0} in EthnologueParser.fill_main_table_rows()'\
                    .format(type(e)))
            quit()
            
        for row in main_rows:
            key, value = self.parse_row(row)
            self.dictionary[key] = value

    def get_attachement_title(self, attachement):
        
        try:
            if not '<div class="view-header">' in attachement:
                return None
            else:
                attachement_title = attachement.split('<h3>')\
                        [1].split('</h3>')[0]
                return attachement_title
        except Exception as e:
            logging.debug('{0} in EthnologueParser.get_attachement_title()'\
                          .format(type(e)))
            quit()

    def get_attachement(self, string):
        try:

            attachement = string.split('<div class="attachment ' +
            'attachment-after">')[1].split('<aside class=' + 
                     '"grid-6 region region-sidebar-second "id="' + 
                                          'region-sidebar-second">')[0]
            return attachement
        except Exception as e:
            logging.debug('{0} in EthnologueParser.get_attachement()'\
                          .format(type(e)))
            quit()

    def get_attachement_blocks_titles(self, attachement): 
        try:
            attachement_blocks = attachement.split('<legend><span class=' + 
                                            '"fieldset-legend"><span>')[1:]
            attachment_titles = [block.split('</span')[0] for \
                                 block in attachement_blocks]
            return attachement_blocks, attachment_titles
        except Exception as e:
            logging.debug(\
            '{0} in EthnologueParser.get_attachement_blocks_titles()'\
                          .format(type(e)))
            quit()

    def fill_attachement(self, string):
        attachement = self.get_attachement(string)
        attachement_title = self.get_attachement_title(attachement)
        if attachement_title == None:
            return
        self.dictionary[attachement_title] = {}
        attachement_blocks, attachment_titles = \
                self.get_attachement_blocks_titles(attachement)
        for i, block in enumerate(attachement_blocks):
            block_title = attachment_titles[i]
            self.dictionary[attachement_title][block_title] = {}
            inner_dictionary = self.parse_attachement_block(block)
            for key in inner_dictionary:
                self.dictionary[attachement_title][block_title][key]\
                        = inner_dictionary[key]

    def fill_dictionary(self, string):
        
        self.fill_title(string)
        self.fill_country(string)
        self.fill_main_table_rows(string)
        self.fill_attachement(string)

    def get_html(self):
        try:
            response = urllib2.urlopen(self.url)
            html = response.read()
            return html
        except Exception as e:
            logging.debug('Error {0} while downloading {1}\n'\
            .format(e, self.url))
            quit()

    def get_attributes(self):

        html = self.get_html()
        self.fill_dictionary(html)
        for key in self.dictionary:
            if len(key) > 50:
                logging.debug('Probably missparsed')

        return self.dictionary

def main():

    sil_code = sys.argv[1]
    logging.basicConfig(level=logging.DEBUG)
    parser = EthnologueParser(sil_code)
    print parser.get_attributes()

if __name__ == "__main__":
    main()
