from collections import defaultdict


from tsv_parser import TSV_parser


class SoftwareSupportParser(TSV_parser):
    def __init__(self, resdir):
        self.resdir = resdir

    def parse(self):
        parser = TSV_parser()
        langs = defaultdict(lambda: {
            'mac_input': False,
            'mac_input_partial': False,
            'microsoft_pack': False})
        for langiter in [
            parser.parse('{0}/mac_input'.format(self.resdir),
                         true_key=['mac_input', 'mac_input_partial']),
            parser.parse('{0}/mac_input_partial_support'.format(self.resdir),
                         true_key=['mac_input_partial']),
            parser.parse('{0}/win8_pack'.format(self.resdir),
                         true_key=['microsoft_pack']),
            parser.parse('{0}/win8_input_option'.format(self.resdir),
                         true_key=['win8_input_method']),
            parser.parse('{0}/office_if_pack'.format(self.resdir),
                         field_target={0: 'name', 5: 'office_if_2013'})]:
            for lang in langiter:
                langs[lang['name']].update(lang)
        return langs
