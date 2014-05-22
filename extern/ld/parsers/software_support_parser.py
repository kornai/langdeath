from collections import defaultdict


from tsv_parser import TSV_parser


class SoftwareSupportParser(TSV_parser):
    def __init__(self, resdir):
        self.resdir = resdir

    def parse(self):
        parser = TSV_parser()
        langs = defaultdict(lambda: {'mac_input': False,
                                     'mac_input_partial': False,
                                     'microsoft_pack': False})

        parameters = [
            ('{0}/mac_input'.format(self.resdir),
             {"true_key": ['mac_input', 'mac_input_partial']}),
            ('{0}/mac_input_partial_support'.format(self.resdir),
             {"true_key": ['mac_input_partial']}),
            ('{0}/win8_pack'.format(self.resdir),
             {"true_key": ['microsoft_pack']}),
            ('{0}/win8_input_option'.format(self.resdir),
             {"true_key": ['win8_input_method']}),
            ('{0}/office13_lp'.format(self.resdir),
             {"true_key": ['office13_lp']}),
            ('{0}/office_if_pack'.format(self.resdir),
             {"field_target": {0: 'name', 5: 'office13_if_pack'}})
        ]
        for args in parameters:
            for lang in parser.parse(args[0], **args[1]):
                langs[lang['name']].update(lang)

        for lang in langs.itervalues():
            yield lang
