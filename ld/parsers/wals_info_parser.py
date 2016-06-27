import logging
import json

from base_parsers import OnlineParser
from utils import get_html


class WalsInfoParser(OnlineParser):

    def __init__(self, resdir):
        self.url = "http://wals.info/languoid.geojson?sEcho=1&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc"  # nopep8
        self.needed_keys = {
            "longitude": "longitude",
            "latitude": "latitude",
            "iso_codes": "sil",
            "name": "name",
            "ascii_name": "alt_names",
            "samples_100": "wals_samples_100",
            "samples_200": "wals_samples_200"
        }
        self.get_mapping_dict('{0}/mappings/wals'.format(resdir))

    def get_mapping_dict(self, mapping_fn):
        self.mapping_dict = {}
        for l in open(mapping_fn):
            k, v = l.strip().decode('utf-8').split('\t')
            self.mapping_dict[k] = v

    def clean_dict(self, d):
        cd = {}
        for k in self.needed_keys:
            cd[self.needed_keys[k]] = d[k]
        cd[u'longitude'] = float(d[u'longitude'])
        cd[u'latitude'] = float(d[u'latitude'])

        return cd

    def generate_dictionaries(self, data):
        for d in data["features"]:
            cd = self.clean_dict(d["properties"]["language"])
            sils = [s.strip() for s in cd["sil"].split(",")]
            for sil in sils:
                new_d = dict(cd)
                if sil != '':
                    new_d["sil"] = sil
                else:
                    del new_d["sil"]
                yield new_d

    def parse(self):
        json_data = get_html(self.url)
        data = json.loads(json_data)
        for d in self.generate_dictionaries(data):
            if d['name'] in self.mapping_dict:
                d['name'] = self.mapping_dict[d['name']]
            yield d


def main():
    import sys
    logging.basicConfig(level=logging.DEBUG)
    parser = WalsInfoParser(sys.argv[1])
    for d in parser.parse():
        print d

if __name__ == "__main__":
    main()
