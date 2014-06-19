# input: path containing files of parsed Wikipedias
import sys
from os import listdir
from os.path import isfile, join
from math import log
from collections import defaultdict
import re
import string
import gzip

from base_parsers import BaseParser


class WikipediaAdjustedSizeCounter(BaseParser):

    def __init__(self, path, basic_limit=2000, entropy_sample_lines=50000):

        self.numerals = set(string.digits)
        self.punctuation = set(string.punctuation)
        self.compile_regexes()
        self.basic_limit = basic_limit
        self.entropy_sample_lines = entropy_sample_lines
        self.path = path
        self.name_regex = re.compile('(.*?)wiki')

    def compile_regexes(self):

        self.title_pattern = re.compile('^%%#PAGE (.*)')

    def get_char_counts_of_all(self, data):

        d = defaultdict(int)
        for is_real, page in self.generate_pages(data, 0):
            for l in page:
                l = l.lower()
                for ch in l:
                    if ch not in self.numerals and ch not in self.punctuation:
                        d[ch] += 1
        return d

    def get_char_length_of_real(self, data, min_chars):

        c = 0
        stub_count = 0
        article_count = 0
        is_real = False
        for is_real, page in self.generate_pages(data, min_chars):
            if is_real is True:
                article_count += 1
                c += len(page)
            else:
                stub_count += 1
        return c, article_count, stub_count

    def generate_pages(self, data, min_chars):

        page = []
        for l in data:
            l = l.strip().decode('utf-8')
            title_matched = self.title_pattern.match(l)
            if title_matched is not None:
                char_counts = sum([len(l) for l in page])
                yield char_counts > min_chars, page
                l = title_matched.groups()[0]
                page = []
            page.append(l)
        char_counts = sum([len(l) for l in page])
        yield char_counts > min_chars, page

    def calculate_entropy(self, values):

        sum_ = sum(values)
        e = log(sum_)/log(2) - sum([v * (log(v)/log(2))/sum_
                                    for v in values])
        return e

    def get_sample(self, f):

        sample = []
        i = 0
        for l in f:
            sample.append(l)
            i += 1
            if i > self.entropy_sample_lines:
                return sample
        return sample    

    def count_wp_size_from_file(self, data_file, stub_limit):

        f = gzip.open(data_file)
        c, a, s = self.get_char_length_of_real(f, stub_limit)
        f.close()
        return c, a, s

    def count_entropy_from_file(self, data_file):

        f = gzip.open(data_file)
        f_sample = self.get_sample(f)
        d = self.get_char_counts_of_all(f_sample)
        values = d.values()
        e = self.calculate_entropy(values)
        stub_limit = self.basic_limit/e
        f.close()
        return e, stub_limit

    def count(self, data_file):

        e, stub_limit = self.count_entropy_from_file(data_file)
        wp_size, article_count, stub_count =\
            self.count_wp_size_from_file(data_file, stub_limit)
        adjusted_size = wp_size * e
        return {'wp_real_articles': article_count,
                'wp_adjusted_size': adjusted_size}

    def parse(self):
        return self.parse_or_load()

    def parse_all(self, **kwargs):
        # counts wp sizes for all dump file in self.path

        files = [f for f in listdir(self.path)
                 if isfile(join(self.path, f))]
        for fn in files:
            f = '{0}/{1}'.format(self.path, fn)
            c = self.name_regex.match(fn).groups()[0]
            d = self.count(f)
            d['wp_code'] = c
            yield d


def main():

    path = sys.argv[1]
    a = WikipediaAdjustedSizeCounter(path)
    for d in a.parse():
        print d

if __name__ == "__main__":
    main()
