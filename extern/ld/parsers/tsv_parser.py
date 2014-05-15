from base_parsers import OfflineParser
from collections import defaultdict

class TSV_parser(OfflineParser):
    def parse(self, filen, field_target=None, true_key=None):
        if field_target == None:
            field_target = {0:'name'}
        """
        parses the tsv file 'filen'
        field_target = { field_index : target_key }
            The value in field # field_index in stroed to key target_key in
            the dictionary representing the language.
        Dictionaries will have key true_key with a True value.
        """
        with open(filen) as file_:
            for line in file_:
                lang = {}
                fields = line.strip().split('\t')
                for field_index, target in field_target.iteritems():
                    lang[target] = fields[field_index]
                if true_key:
                    for key in true_key:
                        lang[key] = True
                yield lang

def parse_os_support():
    parser = TSV_parser()
    langs = defaultdict(lambda: {
        'mac_input' : False, 
        'mac_input_partial' : False, 
        'microsoft_pack' : False})
    for langiter in [
        parser.parse('../res/mac_input', true_key=['mac_input',
                                                      'mac_input_partial']),
        parser.parse('../res/mac_input_partial_support',
                     true_key=['mac_input_partial']),
        parser.parse('../res/win8_pack',
                     true_key=['microsoft_pack']),
        parser.parse('../res/win8_input_method',
                     true_key=['win8_input_method']),
        parser.parse('../res/office_if_pack', 
                     field_target={0 : 'name', 5 : 'office_if_2013'})]:
        for lang in langiter:
            langs[lang['name']].update(lang)
    return langs

if __name__ == '__main__':
    for l in  sorted(parse_os_support().iteritems()):
        print l
