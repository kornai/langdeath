import urllib2
from StringIO import StringIO
import gzip
import sys
from collections import defaultdict
import operator
import logging

from base_parsers import OnlineParser

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
        wp_codes = [
            'aa', 'ab', 'ace', 'af', 'ak', 'als', 'am', 'an', 'ang', 'ar',
            'arc', 'arz', 'as', 'ast', 'av', 'ay', 'az', 'ba', 'bar',
            'bat-smg', 'bcl', 'be', 'be-x-old', 'bg', 'bh', 'bi', 'bjn', 'bm',
            'bn', 'bo', 'bpy', 'br', 'bs', 'bug', 'bxr', 'ca', 'cbk-zam',
            'cdo', 'ce', 'ceb', 'ch', 'cho', 'chr', 'chy', 'ckb', 'co', 'cr',
            'crh', 'cs', 'csb', 'cu', 'cv', 'cy', 'da', 'de', 'diq', 'dsb',
            'dv', 'dz', 'ee', 'el', 'eml', 'en', 'eo', 'es', 'et', 'eu',
            'ext', 'fa', 'ff', 'fi', 'fiu-vro', 'fj', 'fo', 'fr', 'frp',
            'frr', 'fur', 'fy', 'ga', 'gag', 'gan', 'gd', 'gl', 'glk', 'gn',
            'got', 'gu', 'gv', 'ha', 'hak', 'haw', 'he', 'hi', 'hif', 'ho',
            'hr', 'hsb', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig', 'ii',
            'ik', 'ilo', 'io', 'is', 'it', 'iu', 'ja', 'jbo', 'jv', 'ka',
            'kaa', 'kab', 'kbd', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn',
            'ko', 'koi', 'kr', 'krc', 'ks', 'ksh', 'ku', 'kv', 'kw', 'ky',
            'la', 'lad', 'lb', 'lbe', 'lez', 'lg', 'li', 'lij', 'lmo', 'ln',
            'lo', 'lt', 'ltg', 'lv', 'map-bms', 'mdf', 'mg', 'mh', 'mhr',
            'mi', 'min', 'mk', 'ml', 'mn', 'mo', 'mr', 'mrj', 'ms', 'mt',
            'mus', 'mwl', 'my', 'myv', 'mzn', 'na', 'nah', 'nap', 'nds',
            'nds-nl', 'ne', 'new', 'ng', 'nl', 'nn', 'no', 'nov', 'nrm',
            'nso', 'nv', 'ny', 'oc', 'om', 'or', 'os', 'pa', 'pag', 'pam',
            'pap', 'pcd', 'pdc', 'pfl', 'pi', 'pih', 'pl', 'pms', 'pnb',
            'pnt', 'ps', 'pt', 'qu', 'rm', 'rmy', 'rn', 'ro', 'roa-rup',
            'roa-tara', 'ru', 'rue', 'rw', 'sa', 'sah', 'sc', 'scn', 'sco',
            'sd', 'se', 'sg', 'sh', 'si', 'simple', 'sk', 'sl', 'sm', 'sn',
            'so', 'sq', 'sr', 'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw',
            'szl', 'ta', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl', 'tn',
            'to', 'tpi', 'tr', 'ts', 'tt', 'tum', 'tw', 'ty', 'tyv', 'udm',
            'ug', 'uk', 'ur', 'uz', 've', 'vec', 'vep', 'vi', 'vls', 'vo',
            'wa', 'war', 'wo', 'wuu', 'xal', 'xh', 'xmf', 'yi', 'yo', 'za',
            'zea', 'zh', 'zh-classical', 'zh-min-nan', 'zh-yue', 'zu']
        for wp_code in wp_codes:
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
