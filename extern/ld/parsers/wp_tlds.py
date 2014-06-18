import urllib2
from StringIO import StringIO
import gzip
import sys
from collections import defaultdict
import operator
import logging

from base_parsers import OnlineParser

class WikipediaToplevelDomainParser(OnlineParser):
    def parse(self):
        wp_codes = [ 
            'ar', 'az', 'bg', 'ca', 'cs', 'da', 'de', 'el', 'en', 'eo', 'es',
            'et', 'eu', 'fa', 'fi', 'fr', 'gl', 'he', 'hi', 'hr', 'hu', 'id',
            'it', 'ja', 'ka', 'kk', 'ko', 'la', 'li', 'lt', 'mg', 'mk', 'ms',
            'nl', 'no', 'oc', 'pa', 'pa', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl',
            'sr', 'sv', 'sw', 'th', 'tr', 'uk', 'vi', 'zh']
        for wp_code in wp_codes:
            tld_freq = defaultdict(int)
            url = 'http://dumps.wikimedia.org/'+wp_code+'wiki/latest/'+wp_code+'wiki-latest-externallinks.sql.gz'
            request = urllib2.Request(url)
            request.add_header('Accept-encoding', 'gzip')
            response = urllib2.urlopen(request)
            buf = StringIO( response.read())
            f = gzip.GzipFile(fileobj=buf)
            for line in f.readlines():
                # the following lines copied from
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
                            tld_freq[tld] += 1
                    except UnicodeDecodeError, ude:
                        sys.stderr.write(
                            "There is an encoding problem with a link:\n")
                        sys.stderr.write(
                            str(entry).decode("utf-8", "ignore") + "\n")
            total = sum(tld_freq.itervalues())
            tld_freq = dict(
                (k, v) 
                for k, v in tld_freq.iteritems() if 100 * v > total)
            yield {'wp_code': wp_code, 'wp_tlds': sorted(
                tld_freq.iteritems(), key=operator.itemgetter(1),
                reverse=True)}

def test():
    p = WikipediaToplevelDomainParser()
    logging.basicConfig(
        level=logging.DEBUG,
        format= "%(asctime)s : %(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    for lu in p.parse():
        logging.info(lu)
