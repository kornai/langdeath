import logging
import sys

from django.db import transaction

from dld.models import Language

from ld.lang_db import LanguageDB
from ld.langdeath_exceptions import UnknownLanguageException, \
    ParserException

# parsers
from ld.parsers.iso_639_3_parser import ParseISO639_3
from ld.parsers.omniglot_parser import OmniglotParser
from ld.parsers.ethnologue_parser import EthnologueOfflineParser, \
    EthnologueOnlineParser
from ld.parsers.crubadan_parser import CrubadanParser
from ld.parsers.language_archives_parser import \
    LanguageArchivesOfflineParser, LanguageArchivesOnlineParser
from ld.parsers.macro_wp_parser import MacroWPParser
from ld.parsers.software_support_parser import SoftwareSupportParser
from ld.parsers.wals_info_parser import WalsInfoParser
from ld.parsers.indigenous_parser import IndigenousParser
from ld.parsers.dbpedia_parser_aggregator import DbpediaParserAggregator
from ld.parsers.firefox_parser import FirefoxParser
from ld.parsers.list_of_wikipedia_parser import WikipediaListOfLanguagesParser
from ld.parsers.wikipedia_incubators_parser import WikipediaIncubatorsParser
from ld.parsers.wpsize_counter import WikipediaAdjustedSizeCounter


class ParserAggregator(object):
    """This class will go through every parser, calling them, merging
    the results, call any extra methods that will be required to merge
    two langauges (or any other data) that are possibly the same
    """
    def __init__(self, eth_dump_dir='', la_dump_dir='', dbpedia_res_dir='',
                 wpdumps_dir='', res_dir='extern/ld/res'):
        eth_parser = (EthnologueOnlineParser() if not eth_dump_dir
                      else EthnologueOfflineParser(eth_dump_dir))
        la_parser = (LanguageArchivesOnlineParser() if not la_dump_dir
                     else LanguageArchivesOfflineParser(la_dump_dir))
        dbpedia_parser = DbpediaParserAggregator(basedir=dbpedia_res_dir)

        self.parsers = [ParseISO639_3(), MacroWPParser(), dbpedia_parser,
                        eth_parser, CrubadanParser(), la_parser,
                        WalsInfoParser(), IndigenousParser(),
                        WikipediaListOfLanguagesParser(),
                        WikipediaIncubatorsParser(),
                        WikipediaAdjustedSizeCounter(wpdumps_dir)]
        #self.parsers = [OmniglotParser()]
        #self.parsers = [FirefoxParser()]
        #self.parsers = [SoftwareSupportParser(res_dir)]

        self.parsers_todo = [OmniglotParser(), SoftwareSupportParser(res_dir),
                             FirefoxParser()]
        self.lang_db = LanguageDB()
        self.trusted_parsers = set([ParseISO639_3, EthnologueOnlineParser,
                                   EthnologueOfflineParser, CrubadanParser,
                                   MacroWPParser, DbpediaParserAggregator,
                                   WikipediaListOfLanguagesParser])
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

    def add_lang(self, lang):
        try:
            candidates = self.lang_db.get_closest(lang)
            if len(candidates) > 1:
                tgts = self.lang_db.choose_candidates(lang, candidates)
                for tgt in tgts:
                    self.lang_db.update_lang_data(tgt, lang)
            elif len(candidates) == 1:
                best = candidates[0]
                self.lang_db.update_lang_data(best, lang)
            elif len(candidates) == 0:
                if type(self.parser) in self.trusted_parsers:
                    self.lang_db.add_new_language(lang)
                else:
                    self.unknown_langs.add(lang['sil'] if 'sil' in lang
                                           else repr(lang))
                    msg = "{0} parser produced a language with data" \
                        + " {1} that seems to be a new language, but" \
                        + " this parser is not a trusted parser"
                    raise UnknownLanguageException(msg.format(
                        type(self.parser), lang))
        except ParserException as e:
            logging.exception(e)
            return
        except UnknownLanguageException as e:
            return

    @transaction.commit_manually
    def call_parser(self, parser):
        c = 0
        self.parser = parser
        self.unknown_langs = set()
        try:
            for lang in self.choose_parse_call(parser)():
                c += 1
                if c % 100 == 0:
                    logging.info("Added {0} langs from parser {1}".format(
                        c, type(parser)))
                self.add_lang(lang)

        except ParserException as e:
            logging.exception(e)
        if len(self.unknown_langs) > 0:
            logging.error("Unknown_langs: {0}".format(self.unknown_langs))

        transaction.commit()


def main():
    logging.basicConfig(level=logging.INFO)
    pa = ParserAggregator(*sys.argv[1:])
    pa.run()

if __name__ == "__main__":
    main()
