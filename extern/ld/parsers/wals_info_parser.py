import logging
import json

from base_parsers import OnlineParser
from utils import get_html


class WalsInfoParser(OnlineParser):

    def __init__(self):
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
                new_d["sil"] = sil
                yield new_d

    def parse(self):
        json_data = get_html(self.url)
        data = json.loads(json_data)
        for d in self.generate_dictionaries(data):
            yield d


def main():

    logging.basicConfig(level=logging.DEBUG)
    parser = WalsInfoParser()
    for d in parser.parse():
        print u"\t".join((unicode(v) for v in d.values())).encode("utf-8")

if __name__ == "__main__":
    main()
