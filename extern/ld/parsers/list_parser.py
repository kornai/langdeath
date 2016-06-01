from base_parsers import OfflineParser

class ListParser(OfflineParser):
    
    def __init__(self, fn, key, attrib):
        self.fh = open(fn)
        self.key = key
        self.attrib = attrib
    
    def parse(self):
        for l in self.fh:
            l = l.strip('\n').decode('utf-8')
            yield {self.key: l, self.attrib: True}
            
class LeibzigCorporaParser(ListParser):

    def __init__(self, fn):
        super(LeibzigCorporaParser, self).__init__(
            fn, 'name', 'in_leipzig_corpora')

class SirenLanguagesParser(ListParser):
    def __init__(self, fn):
        super(SirenLanguagesParser, self).__init__(
            fn, 'name', 'in_siren_project')

        
def main():
    import sys
    a = SirenLanguagesParser(sys.argv[1])
    for d in a.parse():
        print d

if __name__ == '__main__':
    main()
