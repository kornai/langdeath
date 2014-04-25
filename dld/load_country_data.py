import urllib2
import contextlib

from dld.models import Country


def download_data():
    data = []
    u = "http://download.geonames.org/export/dump/countryInfo.txt"
    with contextlib.closing(urllib2.urlopen(u)) as f:
        for l in f:
            if l.startswith("#"):
                if l.startswith("#ISO\t"):
                    # header
                    l = l.lstrip("#").rstrip("\n")
                    header = l.split("\t")

            else:
                # data
                le = l.rstrip('\n').split("\t")
                if len(le) != len(header):
                    raise Exception("Wrong input data")
                d = {}
                for i in xrange(len(le)):
                    d[header[i]] = le[i]
                data.append(d)
    return data


def fill_data(data):
    for d in data:
        c = Country()
        c.iso = d["ISO"]
        c.iso3 = d["ISO3"]
        c.name = d["Country"]
        c.capital = d["Capital"]
        if len(d["Area(in sq km)"]) > 0:
            c.area = float(d["Area(in sq km)"])
        if len(d["Population"]) > 0:
            c.population = int(d["Population"])
        c.continent = d["Continent"]
        c.tld = d["tld"]
        c.save()


def main():
    data = download_data()
    fill_data(data)

if __name__ == "__main__":
    main()
