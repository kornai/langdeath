from base_parsers import OfflineParser

class TSV_parser(OfflineParser):
    def parse_file(filen, field_target={0:'name'}, true_key=None,
                   categ_map=None):
        """
        parses the tsv file 'filen'
        field_target = { field_index : target_key }
        """
        with open(filen) as file_:
            for line in file_:
                lang = {}
                fields = line.strip().split('\t')
                for field_index, target in field_target.iteritems():
                    value = fields[field_index]
                    if value in categ_map:
                        value = categ_map[value]
                    lang[target] = value
                if true_key:
                    lang[true_key] = True
                yield lang

def parse_os_support():
    parser = TSV_parser
    parser.parse_file('../res/mac_input', true_key='mac_input')
    parser.parse_file('../res/mac_input_partial_support',
                      true_key='mac_input_partial')
    parser.parse_file('../res/microsoft_pack', true_key='microsoft_pack')
    parser.parse_file(
        '../res/microsoft_if_pack', 
        field_target={0 : 'name', 5 : 'microsoft_if_2013'},
        categ_map = {'download' : 1, 'buy' : .5, 'none' : 0}
    )
