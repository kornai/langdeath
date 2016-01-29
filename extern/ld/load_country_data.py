import sys
import urllib2
import contextlib
from collections import defaultdict

from dld.models import Country, CountryName


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


def read_alternative_names(istream):
    d = defaultdict(list)
    for l in istream:
        le = l.strip().decode("utf-8").split("\t")
        alt_name, orig_name = le
        d[alt_name].append(orig_name)
    return d


def add_kurdistan():
    k = Country()
    k.iso = "xk"
    k.iso3 = "xku"
    k.name = "Kurdistan"
    k.save()


def fill_countries(names):
    for d in names:
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
    add_kurdistan()


def fill_alt_names(alt_names):
    for a, cs in alt_names.iteritems():
        for c in cs:
            countries = Country.objects.filter(name=c)
            if len(countries) != 1:
                msg = "Alternative name data contains invalid country name"
                msg += ": {0} {1}".format(a, c)
                raise Exception(msg)
            country = countries[0]
            country.save()
            cn = CountryName(country=country, name=a)
            cn.save()
            country.save()


def fill_data(names, alt_names):
    fill_countries(names)
    fill_alt_names(alt_names)


def main():
    iso_names = download_data()
    alt_names = read_alternative_names(open(sys.argv[1]))
    fill_data(iso_names, alt_names)

if __name__ == "__main__":
    main()
