import os
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "langdeath.settings")

import sys
import logging
from argparse import ArgumentParser
import re

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
from ld.parsers.google_translate_parser import GoogleTranslateParser
from ld.parser_aggregator_utils import write_out_new_langs,\
        write_out_found_langs, write_out_new_altnames
from ld.parsers.endangered_parser import EndangeredParser
from ld.parsers.tsv_parser import L2Parser, EthnologueDumpParser, UrielParser,\
        EthnologueMacroParser
from ld.parsers.bible_org_parser import BiblesParser
from ld.parsers.list_parser import LeibzigCorporaParser, SirenLanguagesParser
from ld.parsers.treetagger_parser import TreeTaggerParser
from ld.parsers.find_bible_parser import FindBibleOfflineParser
from ld.parsers.glottolog_parser import GlottologParser
from ld.parsers.endangered_resources_parser import EndangeredResourcesParser


class ParserAggregator(object):
    """This class will go through every parser, calling them, merging
    the results, call any extra methods that will be required to merge
    two langauges (or any other data) that are possibly the same
    """
    
    def __init__(self, data_dump_dir, log_dir, pickle_dir, res_dir, extended):
        mappings_file = "/".join([res_dir, "dump_filenames"])
        mappings      = dict([l.strip().split('\t')
                                 for l in open(mappings_file)])

        pickles, dump_dir = self.check_dirs(
            data_dump_dir, mappings, pickle_dir)

        # initializing parsers which need data dumps
        parser_names = [
            'EthnologueDumpParser','LanguageArchivesOfflineParser',
            'UrielParser', 'DbpediaParserAggregator',
            'WikipediaAdjustedSizeCounter_WPExtractor',
            'WPIncubatorAdjustedSizeCounter',
            'EndangeredParser', 'FindBibleOfflineParser', 'CrubadanParser']
        eth_parser, la_parser, uriel_parser, dbpedia_parser,\
                wp_adjusted_parser, wpinc_adj_parser, endangered_parser,\
        find_bible_parser, crubadan_parser = \
                self.init_dump_based_parsers(pickles, dump_dir, parser_names,
                                             res_dir)
        #initializing all parsers
        self.parsers = [ParseISO639_3(extended), MacroWPParser(), uriel_parser, dbpedia_parser,
                        eth_parser, EthnologueMacroParser(res_dir + "/" + "ethnologue_macro"), 
                        GlottologParser(),
                        L2Parser(res_dir + "/" + "ethnologue_l2"),
                        crubadan_parser, la_parser,
                        WalsInfoParser(res_dir), IndigenousParser(res_dir),
                        BiblesParser(), EndangeredResourcesParser(),
                        LeibzigCorporaParser(res_dir + "/" + "leipzig_corpora"),
                        SirenLanguagesParser(res_dir + "/" + "siren_list"),
                        TreeTaggerParser(),
                        find_bible_parser,
                        WikipediaListOfLanguagesParser(res_dir),
                        WikipediaIncubatorsParser(res_dir),
                        wp_adjusted_parser,
                        endangered_parser, OmniglotParser(
                            '{0}/mappings/omniglot'.format(res_dir)),
                        FirefoxParser('{0}/mappings/firefox'.format(res_dir)),
                        SoftwareSupportParser(res_dir), wpinc_adj_parser]
        self.parsers = filter(lambda x:x != None, self.parsers)
        self.lang_db = LanguageDB()
        self.trusted_parsers = set([ParseISO639_3, GlottologParser, CrubadanParser,
                                    EndangeredParser])
        self.parsers_needs_sil = set([EthnologueOfflineParser,
                                      EthnologueOnlineParser,
                                      LanguageArchivesOnlineParser])
        self.debug_dir = log_dir
        self.pickle_dir = pickle_dir
        self.extended = extended

    def check_dirs(self, data_dump_dir, classname_to_fn, pickle_dir):
        
        dump_dir = {}
        pickle_fns = os.listdir(pickle_dir)
        pickled_pattern = re.compile('(.*?).pickle$')
        pickled = []
        for f in pickle_fns:
            matched = pickled_pattern.match(f)
            if matched != None:
                base = matched.groups()[0]
                logging.info('Parser {} will only load {}/{}'.format(
                    base, pickle_dir, f))
                pickled.append(base)
        files = os.listdir(data_dump_dir)
        for k, v in classname_to_fn.iteritems():
            if v in files:
                dump_dir[k] = '{}/{}'.format(data_dump_dir, v)
            elif v not in pickled:
                logging.info("Parser {} has no input, so it'll get skipped".format(
                base))
        return pickled, dump_dir
    
    def init_dump_based_parsers(self, pickles, dump_dir, parser_names, res_dir):
        dummy_fn = 'dummy_fn'
        initialized_parsers = []
        for classname in parser_names:
            if classname in pickles:
                initialized_parsers.append(eval(classname)(dummy_fn))
            elif classname in dump_dir:
                if classname == 'EndangeredParser':
                    endangered_dump_dir =\
                            dump_dir['EndangeredParser']
                    initialized_parsers.append(
                        EndangeredParser('{}/endangered_ids'.format(res_dir),
                                         endangered_dump_dir))   
                else:
                    initialized_parsers.append(eval(classname)(
                        dump_dir[classname]))
            else:
                if classname == 'LanguageArchivesOfflineParser':
                    initialized_parsers.append(
                        LanguageArchivesOnlineParser())
                else:    
                    initialized_parsers.append(None)
        return initialized_parsers

        
    def run(self):
        
        for parser in self.parsers:
            parser.pickle_dir = self.pickle_dir
            try:
                self.call_parser(parser)
            except:
                logging.exception("Parser {0} failed; continuing anyway".format(
                    type(parser)))
                

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
            candidates, clue = self.lang_db.get_closest(lang)
            if len(candidates) > 1:
                tgts = self.lang_db.choose_candidates(lang, candidates)
                for tgt in tgts:
                    self.lang_db.update_lang_data(tgt, lang)
                    self.add_data_to_loglists(lang, tgt.name, clue)
            elif len(candidates) == 1:
                best = candidates[0]
                self.lang_db.update_lang_data(best, lang)
                self.add_data_to_loglists(lang, best.name, clue)
            elif len(candidates) == 0:
                self.new_langs.append(lang) 
                if type(self.parser) == ParseISO639_3 or\
                (self.extended and type(self.parser) in self.trusted_parsers): 
                    if type(self.parser) != ParseISO639_3:
                        # assigning temporary code 
                        temporary_code = '{}.{}'.format(
                            self.parser.__class__.__name__, self.temp_code_index)
                        self.temp_code_index += 1
                        lang['sil'] = temporary_code    
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
                    
    def add_data_to_loglists(self, lang, name, clue):
        self.found_langs.append((lang, [name, clue]))
        if 'alt_names' in lang:
            a_l = lang['alt_names']
            if type(a_l) in [str, unicode]:
                a_l = [a_l]
            for a_n in a_l:
                self.new_altnames.append((a_n, lang.get('name', ''), name))
    
    def call_parser(self, parser):
        transaction.set_autocommit(False)
        c = 0
        self.parser = parser
        self.new_langs = []
        self.new_altnames = []
        self.found_langs = []
        if self.extended:
            self.temp_code_index = 0
        try:
            for lang in self.choose_parse_call(parser)():
                c += 1
                if c % 100 == 0:
                    logging.info("Added {0} langs from parser {1}".format(
                        c, type(parser)))

                lang['parser'] = str(type(parser))
                self.add_lang(lang)

        except ParserException as e:
            logging.exception(e)

        if len(self.new_langs) > 0:
            if type(self.parser) in self.trusted_parsers:
                logging.info("New languages added from {0}: {1}".format(
                               type(self.parser), len(self.new_langs)))
            else:
                logging.warning("New languages found but not added from" + \
                                " {0} (not a trusted parser): {1}".format(
                                  type(self.parser), len(self.new_langs)))

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
        transaction.set_autocommit(True)
    
    def get_out_fn(self, new=False, altnames=False):
        classname = self.parser.__class__.__name__
        if new:
            if type(self.parser) in self.trusted_parsers:
                new_lang_label = 'new_langs'
            else:
                new_lang_label = 'notfound_langs'
        else:        
            if altnames:
                new_lang_label = 'altnames'        
            else:
                new_lang_label = 'found_langs'
        return '{}/{}.{}'.format(self.debug_dir, classname, new_lang_label)    
    

def get_args():
    parser = ArgumentParser()

    parser.add_argument('data_dump_dir',
                        help='directory of data dumps')

    parser.add_argument('-p', '--pickle_dir',
                        help="directory of pickles (defaults to 'pickles/')",
                        default='pickles')

    parser.add_argument('-l', '--log_dir',
                        help="directory for log files (defaults to 'logs/')",
                        default='logs')

    parser.add_argument('-r', '--res_dir',
                        help="directory of required extra files (defaults to" +\
                        " 'res/')",
                        default='res')

    parser.add_argument('-e', '--extended',
                        action='store_true',
                        help='extended language set: includes languages with' +\
                        ' a retired sil code, possibly extended by languages' +\
                        ' found by trusted parsers')

    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = get_args()
    pa = ParserAggregator(args.data_dump_dir,
                          args.log_dir,
                          args.pickle_dir,
                          args.res_dir,
                          args.extended)
    pa.run()
    # after collecting all information on different codes, integrate
    logging.info('Integrating codes')
    pa.lang_db.integrate_codes()

if __name__ == "__main__":
    main()
