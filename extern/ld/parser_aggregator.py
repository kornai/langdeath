import logging

from ld.lang_db import LanguageDB
from ld.langdeath_exceptions import UnknownLanguageException
from ld.parsers.iso_639_3_parser import ParseISO639_3
from ld.parsers.omniglot_parser import OmniglotParser


class ParserAggregator(object):
    """This class will go through every parser, calling them, merging
    the results, call any extra methods that will be required to merge
    two langauges (or any other data) that are possibly the same
    """
    def __init__(self):
        self.parsers = [ParseISO639_3(), OmniglotParser()]
        self.lang_db = LanguageDB()
        self.trusted_parsers = set([ParseISO639_3])

    def run(self):
        for parser in self.parsers:
            self.call_parser(parser)

    def call_parser(self, parser):
        c = 0
        for lang in parser.parse():
            c += 1
            if c % 100 == 0:
                logging.info("Added {0} langs from parser {1}".format(
                    c, type(parser)))

            candidates = self.lang_db.get_closest(lang)
            if len(candidates) > 1:
                best = self.lang_db.choose_candidate(candidates)
                self.lang_db.update_lang_data(best, lang)
            elif len(candidates) == 1:
                best = candidates[0]
                self.lang_db.update_lang_data(best, lang)
            elif len(candidates) == 0:
                if type(parser) in self.trusted_parsers:
                    self.lang_db.add_new_language(lang)
                else:
                    msg = "{0} parser produced a language with data " + \
                        "{1} that seems to be a new language, but" + \
                        "this parser is not a trusted parser"
                    raise UnknownLanguageException(msg)


def main():
    logging.basicConfig(level=logging.INFO)
    pa = ParserAggregator()
    pa.run()

if __name__ == "__main__":
    main()
