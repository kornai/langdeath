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
from ld.parsers.wpsize_counter import WikipediaAdjustedSizeCounter_WPExtractor, \
    WPIncubatorAdjustedSizeCounter
from ld.parser_aggregator_utils import write_out_new_langs,\
        write_out_found_langs, write_out_new_altnames
from ld.parsers.endangered_parser import EndangeredParser
from ld.parsers.tsv_parser import L2Parser, EthnologueDumpParser, UrielParser


class ParserAggregator(object):
    """This class will go through every parser, calling them, merging
    the results, call any extra methods that will be required to merge
    two langauges (or any other data) that are possibly the same
    """
    def __init__(self, eth_dump_dir='', la_dump_dir='', dbpedia_res_dir='',
                 wpdumps_dir='', wpinc_dump_fn='', res_dir='extern/ld/res',
                 endangered_dump_dir='', uriel_dump='', debug_dir=None):
        eth_parser = EthnologueDumpParser(eth_dump_dir)
        la_parser = (LanguageArchivesOnlineParser() if not la_dump_dir
                     else LanguageArchivesOfflineParser(la_dump_dir))
        uriel_parser = UrielParser(uriel_dump)
        dbpedia_parser = DbpediaParserAggregator(basedir=dbpedia_res_dir)
        l2_parser = L2Parser(res_dir + "/" + "ethnologue_l2")
        wpinc_adj_parser = WPIncubatorAdjustedSizeCounter(wpinc_dump_fn)
        firefox_mapping = '{0}/mappings/firefox'.format(res_dir)
        endangered_parser = EndangeredParser('{}/list_of_ids'.format(
            endangered_dump_dir), endangered_dump_dir)
        omniglot_parser = OmniglotParser('{0}/mappings/omniglot'.format(res_dir))
        self.parsers = [ParseISO639_3(), MacroWPParser(), uriel_parser, dbpedia_parser,
                        eth_parser, l2_parser, CrubadanParser(), la_parser,
                        WalsInfoParser(res_dir), IndigenousParser(res_dir),
                        WikipediaListOfLanguagesParser(res_dir),
                        WikipediaIncubatorsParser(res_dir),
                        WikipediaAdjustedSizeCounter_WPExtractor(wpdumps_dir),
                        endangered_parser, omniglot_parser,
                        FirefoxParser(firefox_mapping),
                        SoftwareSupportParser(res_dir), wpinc_adj_parser]
        self.parsers = [wpinc_adj_parser]
        self.parsers_todo = [omniglot_parser, SoftwareSupportParser(res_dir),
                             FirefoxParser(firefox_mapping)]
        self.lang_db = LanguageDB()
        self.trusted_parsers = set([ParseISO639_3])
        self.parsers_needs_sil = set([EthnologueOfflineParser,
                                      EthnologueOnlineParser,
                                      LanguageArchivesOnlineParser])
        self.debug_dir = debug_dir

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
                    self.found_langs.append((lang, [tgt.sil, tgt.name]))
                    if 'name' in lang and lang['name'] != tgt.name:
                        self.new_altnames.append((lang['name'], tgt.name))
            elif len(candidates) == 1:
                best = candidates[0]
                self.lang_db.update_lang_data(best, lang)
                self.found_langs.append((lang, [best.name, best.sil]))
                if 'name' in lang and lang['name'] != best.name:
                    self.new_altnames.append((lang['name'], best.name))
            elif len(candidates) == 0:
                self.new_langs.append(lang) 
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
        self.new_langs = []
        self.new_altnames = []
        self.found_langs = []
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
            logging.error("New langs/not found: {0}, ".format(
                len(self.new_langs)))
            if self.debug_dir != None:
                if len(self.new_langs) > 0:
                    write_out_new_langs(
                        self.new_langs, self.get_out_fn(new=True))
                if len(self.found_langs) > 0:    
                    write_out_found_langs(self.found_langs, self.get_out_fn())
                if len(self.new_altnames) > 0:    
                    write_out_new_altnames(
                    self.new_altnames, self.get_out_fn(altnames=True))
        transaction.commit()
    
    def get_out_fn(self, new=False, altnames=False):
        classname = str(type(self.parser)).split('.')[3].split("'")[0]
        if new:
            if type(self.parser) in self.trusted_parsers:
                new_lang_label = 'new_langs'
            else:
                new_lang_label = 'notfound_langs'
        else:        
            if altnames:
                new_lang_label = 'new_altnames'        
            else:
                new_lang_label = 'found_langs'
        return '{}/{}.{}'.format(self.debug_dir, classname, new_lang_label)    
    
  
def main():
    logging.basicConfig(level=logging.INFO)
    pa = ParserAggregator(*sys.argv[1:])
    pa.run()

if __name__ == "__main__":
    main()
