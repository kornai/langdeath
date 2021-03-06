from base_parsers import OfflineParser
import sys

class TSV_parser(OfflineParser):
    def parse(self, filen, field_target=None, true_key=None, encoding="utf-8"):
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
                fields = line.strip().decode(encoding).split('\t')
                for field_index, target in field_target.iteritems():
                    v = fields[field_index]
                    if v == "none":
                        v = False
                    elif v == "download":
                        v = True
                    lang[target] = v
                if true_key:
                    for key in true_key:
                        lang[key] = True
                yield lang


class L2Parser(TSV_parser):
    def __init__(self, fn):
        super(TSV_parser, self).__init__()
        self.fn = fn

    def parse(self):
        field_target = {0: "sil", 1: "speakers"}
        for res in super(L2Parser, self).parse(self.fn, field_target):
            res["speakers"] = [("ethnologue", "L2", res["speakers"])]
            yield res


class EthnologueDumpParser(TSV_parser):

    def __init__(self, fn):
        super(TSV_parser, self).__init__()
        self.fn = fn
    
    def parse(self):
        return self.parse_or_load()

    def parse_all(self):
        field_target = {0: "sil", 1: "name", 4: "country", 6:
                        'region_name',  8: "speakers",
                        13: 'latitude', 14: 'longitude',
                        15: "endangered_level"}
        header = True
        for res in super(EthnologueDumpParser, self).parse(
            self.fn, field_target):
            if header:
                header = False
                continue
            res["speakers"] = [("ethnologue", "L1", res["speakers"] if
                                res["speakers"] != '' else 0)]
            res["endangered_level"] = [("ethnologue", res["endangered_level"],
                                        None)]
            if len(res['latitude']) == 0:
                del res['latitude']
            else:    
                res['latitude'] = float(res['latitude'])
            if len(res['longitude']) == 0:
                del res['longitude']
            else:
                res['longitude'] = float(res['longitude'])
            yield res

class EthnologueMacroParser(TSV_parser):

    def __init__(self, fn):
        super(TSV_parser, self).__init__()
        self.fn = fn
    
    def parse(self):
        field_target = {0: "sil", 1: "speakers",
                        2: "endangered_level"}
        for res in super(EthnologueMacroParser, self).parse(
            self.fn, field_target):
            res["speakers"] = [("ethnologue", "L1", res["speakers"] if
                                res["speakers"] != '' else 0)]
            res["endangered_level"] = [("ethnologue", res["endangered_level"],
                                        None)]
            yield res


class UrielParser(OfflineParser):


    def __init__(self, fn):
        self.fn = fn

    def parse(self):
        return self.parse_or_load()
    
    def parse_all(self):
        fh = open(self.fn)
        header = fh.readline()
        for l in fh:
            data = l.strip().split(',')
            sil, values = data[0], data[1:]
            # Albanian
            if sil == 'alb':
                sil = 'sqi'
            yield {'sil': sil,
                   'uriel_feats': len(filter(lambda x: x!= '--', values))}

def main():

     a =  EthnologueDumpParser(sys.argv[1])
     for d in a.parse():
         print d

if __name__ == '__main__':
    main()
         

