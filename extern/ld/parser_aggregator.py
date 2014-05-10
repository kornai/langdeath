import logging
import sys

from django.db import transaction

from dld.models import Language

from ld.lang_db import LanguageDB
from ld.langdeath_exceptions import UnknownLanguageException, \
    ParserException

# parsers
from ld.parsers.iso_639_3_parser import ParseISO639_3
from ld.parsers.ethnologue_parser import EthnologueOfflineParser, \
    EthnologueOnlineParser
from ld.parsers.crubadan_parser import CrubadanParser
from ld.parsers.language_archives_parser import \
    LanguageArchivesOfflineParser, LanguageArchivesOnlineParser


class ParserAggregator(object):
    """This class will go through every parser, calling them, merging
    the results, call any extra methods that will be required to merge
    two langauges (or any other data) that are possibly the same
    """
    def __init__(self, eth_dump_dir='', la_dump_dir=''):
        eth_parser = (EthnologueOnlineParser() if not eth_dump_dir
                      else EthnologueOfflineParser(eth_dump_dir))
        la_parser = (LanguageArchivesOnlineParser() if not la_dump_dir
                     else LanguageArchivesOfflineParser(la_dump_dir))

        self.parsers = [ParseISO639_3(), eth_parser, CrubadanParser()]
        self.parsers = [la_parser]
        self.lang_db = LanguageDB()
        self.trusted_parsers = set([ParseISO639_3, EthnologueOnlineParser,
                                   EthnologueOfflineParser, CrubadanParser])
        self.parsers_needs_sil = set([EthnologueOfflineParser,
                                      EthnologueOnlineParser,
                                      LanguageArchivesOfflineParser,
                                      LanguageArchivesOnlineParser])

    def run(self):
        for parser in self.parsers:
            self.call_parser(parser)

    def choose_parse_call(self, parser):
        parse_call = None
        if type(parser) in self.parsers_needs_sil:
            # keep only real sils, not the artificial ones coming from cru
            sils = filter(lambda x: len(x) == 3,
                          Language.objects.values_list("sil", flat=True))
            parse_call = lambda: parser.parse(sils)
        else:
            parse_call = lambda: parser.parse()
        return parse_call

    @transaction.commit_manually
    def call_parser(self, parser):
        c = 0
        unknown_langs = set()
        try:
            for lang in self.choose_parse_call(parser)():
                c += 1
                if c % 100 == 0:
                    logging.info("Added {0} langs from parser {1}".format(
                        c, type(parser)))

                try:
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
                            unknown_langs.add(lang['sil'] if 'sil' in lang
                                              else repr(lang))
                            msg = "{0} parser produced a language with data" \
                                + " {1} that seems to be a new language, but" \
                                + " this parser is not a trusted parser"
                            raise UnknownLanguageException(msg.format(
                                type(parser), lang))
                except ParserException as e:
                    logging.exception(e)
                    continue
                except UnknownLanguageException as e:
                    continue

        except ParserException as e:
            logging.exception(e)
        if len(unknown_langs) > 0:
            logging.error("Unknown_langs: {0}".format(unknown_langs))

        transaction.commit()


def main():
    logging.basicConfig(level=logging.INFO)
    pa = ParserAggregator(*sys.argv[1:])
    pa.run()

if __name__ == "__main__":
    main()
