from base_parsers import OfflineParser


class TSV_parser(OfflineParser):
    def parse(self, filen, field_target=None, true_key=None):
        if field_target is None:
            field_target = {0: 'name'}
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
