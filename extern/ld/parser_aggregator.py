from ld.lang_db import LanguageDB
from ld.langdeath_exceptions import UnknownLanguageException
from ld.parsers.iso_639_3_parser import ParseISO639_3


class ParserAggregator(object):
    """This class will go through every parser, calling them, merging
    the results, call any extra methods that will be required to merge
    two langauges (or any other data) that are possibly the same
    """
    def __init__(self):
        self.parsers = [ParseISO639_3()]
        self.lang_db = LanguageDB()
        self.trusted_parsers = set([])

    def run(self):
        for parser in self.parsers:
            self.call_parser(parser)

    def call_parser(self, parser):
        for lang in parser.parse():
            candidates = self.lang_db.get_closest(lang)
            if len(candidates) > 1:
                best = self.lang_db.choose_candidate(candidates)
                self.lang_db.update_lang_data(best, lang)
            elif len(candidates) == 1:
                best = candidates[0]
                self.lang_db.update_lang_data(best, lang)
            elif len(candidates) == 0:
                if parser.name in self.trusted_parsers:
                    self.lang_db.add_new_language(lang)
                else:
                    msg = "{0} parser produced a language with data " + \
                        "{1} that seems to be a new language, but" + \
                        "this parser is not a trusted parser"
                    raise UnknownLanguageException(msg)


def main():
    pa = ParserAggregator()
    pa.run()

if __name__ == "__main__":
    main()
