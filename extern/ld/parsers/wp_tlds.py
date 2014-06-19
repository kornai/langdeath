import urllib2
from StringIO import StringIO
import gzip
import sys
from collections import defaultdict
import operator
import logging

from base_parsers import OnlineParser
from list_of_wikipedia_parser import WikipediaListOfLanguagesParser

class WikipediaToplevelDomainParser(OnlineParser):
    def get_file(self, wp_code):
        url = 'http://dumps.wikimedia.org/'+wp_code+'wiki/latest/'+wp_code+'wiki-latest-externallinks.sql.gz'
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request)
        buf = StringIO( response.read())
        self.file_ =  gzip.GzipFile(fileobj=buf)

    def count_links(self):
        self.tld_freq = defaultdict(int)
        for line in self.file_.readlines():
            # parts copied from
            # hunmisc/hunmisc/wikipedia/parse_insert_into_rows.py
            if not line.startswith("INSERT INTO"):
                continue
            
            line = line.decode("utf-8", "ignore").split("VALUES", 1)[1].strip().rstrip(";")
            entries = eval("( %s )" % line)
            for entry in entries:
                entry_elements = list(entry)
                entry_elements = [
                    str(ee) if type(ee) != str 
                    else ee.decode("utf-8") for ee in entry_elements]
                try:
                    ext_url = entry_elements[2]
                    if '//' in ext_url:
                        domain = ext_url.split('/')[2]
                        tld = domain.split('.')[-1]
                        self.tld_freq[tld] += 1
                except UnicodeDecodeError, ude:
                    sys.stderr.write(
                        "There is an encoding problem with a link:\n")
                    sys.stderr.write(
                        str(entry).decode("utf-8", "ignore") + "\n")

    def postproc_counts(self, wp_code):
        total = sum(self.tld_freq.itervalues())
        tld_freq = dict(
            (k, v) 
            for k, v in self.tld_freq.iteritems() if 100 * v > total)
        self.tld_freq = {'wp_code': wp_code, 'wp_tlds': sorted(
            tld_freq.iteritems(), key=operator.itemgetter(1),
            reverse=True)}

    def tlds(self, wp_code):
        """
        returns a language update with the Wikipedia code and the frequencies
        of top level domains (TLD) in external links in the corresponding
        Wikipedia. TLD cutoff: 1 % of all links
        """
        self.get_file(wp_code)
        self.count_links()
        self.postproc_counts(wp_code)
        return self.tld_freq

    def parse(self):
        list_parser = WikipediaListOfLanguagesParser()
        for lang_dict in list_parser.parse():
            wp_code = lang_dict['Wiki']
            try:
                yield self.tlds(wp_code)
            except urllib2.HTTPError as e:
                if e.code==404:
                    pass
                else:
                    raise e

def test():
    p = WikipediaToplevelDomainParser()
    logging.basicConfig(
        level=logging.DEBUG,
        format= "%(asctime)s : %(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    for lu in p.parse():
        logging.info(lu)
