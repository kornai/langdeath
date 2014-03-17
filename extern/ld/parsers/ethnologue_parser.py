import sys
import urllib2
import re

from base_parsers import OnlineParser
from ld.langdeath_exceptions import LangdeathException 


class EthnologueParser(OnlineParser):

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
            raise LangdeathException(
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
            raise LangdeathException(
                '{0} in EthnologueParser.parse_row(), at row\n{1} ' +
                    'sil:{2}'.format(type(e), row, self.sil))

    def get_title(self, string):
        try:
            return string.split('<h1 class="title" id="page-title">')[1]\
                .split('</h1>')[0]
        except Exception as e:
            raise LangdeathException(
            '{0} in EthnologueParser.get_title() sil:{1}'
                    .format(type(e), self.sil))

    def get_country(self, string):
        try:
            return string.split('<h2>')[1].split('>')[1].split('</a')[0]
        except Exception as e:
            raise LangdeathException(
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
            raise LangdeathException(
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
            raise LangdeathException(
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
            raise LangdeathException(
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
            raise LangdeathException(
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
            html = self.get_html(sil_code)
            dictionary = {}
            dictionary['Name'] = self.get_title(html)
            dictionary['Country'] = self.get_country(html)
            main_items = self.process_main_table_rows(html)
            if main_items is not None:
                for i in main_items:
                    key, value = i
                    dictionary[key] = value
            attachement_info = self.get_attachement_dict(html)
            if attachement_info is not None:
                t, dict_ = attachement_info
                dictionary[t] = dict_
            yield dictionary

    def get_html(self, sil_code):
        try:
            url = 'http://www.ethnologue.com/language/{0}'.format(sil_code)
            response = urllib2.urlopen(url)
            html = response.read()
            return html
        except Exception as e:
            raise LangdeathException(
            'Error {0} while downloading {1}\n'
            .format(e, url))

def main():

    sil_codes = sys.argv[1:]
    parser = EthnologueParser()
    for d in parser.parse(sil_codes):
        print d

if __name__ == "__main__":
    main()
