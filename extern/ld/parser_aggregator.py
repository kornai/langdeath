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
from ld.parsers.wpsize_counter import WikipediaAdjustedSizeCounter, \
    WPIncubatorAdjustedSizeCounter
from ld.parsers.endangered_parser import EndangeredParser
from ld.parsers.tsv_parser import L2Parser


class ParserAggregator(object):
    """This class will go through every parser, calling them, merging
    the results, call any extra methods that will be required to merge
    two langauges (or any other data) that are possibly the same
    """
    def __init__(self, eth_dump_dir='', la_dump_dir='', dbpedia_res_dir='',
                 wpdumps_dir='', wpinc_dump_fn='', res_dir='extern/ld/res'):
        eth_parser = (EthnologueOnlineParser() if not eth_dump_dir
                      else EthnologueOfflineParser(eth_dump_dir))
        la_parser = (LanguageArchivesOnlineParser() if not la_dump_dir
                     else LanguageArchivesOfflineParser(la_dump_dir))
        dbpedia_parser = DbpediaParserAggregator(basedir=dbpedia_res_dir)
        l2_parser = L2Parser(res_dir + "/" + "ethnologue_l2")
        wpinc_adj_parser = WPIncubatorAdjustedSizeCounter(wpinc_dump_fn)

        self.parsers = [ParseISO639_3(), MacroWPParser(), dbpedia_parser,
                        eth_parser, l2_parser, CrubadanParser(), la_parser,
                        WalsInfoParser(), IndigenousParser(),
                        WikipediaListOfLanguagesParser(),
                        WikipediaIncubatorsParser(),
                        WikipediaAdjustedSizeCounter(wpdumps_dir),
                        EndangeredParser(), OmniglotParser(), FirefoxParser(),
                        SoftwareSupportParser(res_dir),
                        wpinc_adj_parser]
        self.parsers = [wpinc_adj_parser]

        self.parsers_todo = [OmniglotParser(), SoftwareSupportParser(res_dir),
                             FirefoxParser()]
        self.lang_db = LanguageDB()
        self.trusted_parsers = set([ParseISO639_3, EthnologueOnlineParser,
                                   EthnologueOfflineParser, CrubadanParser,
                                   MacroWPParser, DbpediaParserAggregator,
                                   WikipediaListOfLanguagesParser])
        self.parsers_needs_sil = set([EthnologueOfflineParser,
                                      EthnologueOnlineParser,
                                      LanguageArchivesOnlineParser])
        self.new_lang_list = []

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
                self.new_langs.add(repr(lang)) 
                if type(self.parser) in self.trusted_parsers:
                    self.lang_db.add_new_language(lang)
                else:
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
        self.new_langs = set()
        if type(self.parser) in self.trusted_parsers:
             new_lang_label = 'New lang'
        else:
            new_lang_label = 'Not found'
        try:
            for lang in self.choose_parse_call(parser)():
                c += 1
                if c % 100 == 0:
                    logging.info("Added {0} langs from parser {1}".format(
                        c, type(parser)))
                self.add_lang(lang)

        except ParserException as e:
            logging.exception(e)
        if len(self.new_langs) > 0:
            logging.error("{0}: {1}, ".format(new_lang_label, len(self.new_langs)))
        self.new_lang_list.append((type(self.parser), new_lang_label,
                                   self.new_langs)) 

        transaction.commit()


def main():
    logging.basicConfig(level=logging.INFO)
    pa = ParserAggregator(*sys.argv[1:])
    pa.run()
    import cPickle
    f = open('new_languages_list', 'w')
    cPickle.dump(pa.new_lang_list, f)

if __name__ == "__main__":
    main()
