# input: parsed(!) Wikipedia
import sys

from math import log
from collections import defaultdict
import re
import string


class WikipediaAdjustedSizeCounter():

    def __init__(self, min_chars=50):

        self.numerals = set(string.digits)
        self.punctuation = set(string.punctuation)
        self.compile_regexes()
        self.min_chars = min_chars

    def compile_regexes(self):

        self.title_pattern = re.compile('^%%#PAGE (.*)')

    def get_char_counts(self, data):

        d = defaultdict(int)
        for real_page in self.generate_real_pages(data):
            for l in real_page:
                l = l.lower()
                for ch in l:
                    if ch not in self.numerals and ch not in self.punctuation:
                        d[ch] += 1
        return d

    def generate_real_pages(self, data):

        page = []
        for l in data:
            l = l.strip().decode('utf-8')
            title_matched = self.title_pattern.match(l)
            if title_matched is not None:
                char_counts = sum([len(l) for l in page])
                if char_counts > self.min_chars:
                    yield page
                l = title_matched.groups()[0]
                page = []
            page.append(l)
        char_counts = sum([len(l) for l in page])
        if char_counts > self.min_chars:
            yield page

    def calculate_entropy(self, values):

        sum_ = sum(values)
        entropy = log(sum_)/log(2) - sum([v * (log(v)/log(2))/sum_
                                          for v in values])
        return entropy

    def count(self, data):

        d = self.get_char_counts(data)
        char_freqs = d.values()
        wp_size = sum(char_freqs)
        char_entropy = self.calculate_entropy(char_freqs)
        adjusted_size = wp_size * char_entropy
        return wp_size, char_entropy, adjusted_size


def main():

    data = sys.stdin
    a = WikipediaAdjustedSizeCounter()
    size, entropy, adjusted_size = a.count(data)
    print size, entropy, adjusted_size

if __name__ == "__main__":
    main()
