import logging
import os
import sys
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
from ld.parsers.tsv_parser import L2Parser, EthnologueDumpParser, UrielParser


class ParserAggregator(object):
    """This class will go through every parser, calling them, merging
    the results, call any extra methods that will be required to merge
    two langauges (or any other data) that are possibly the same
    """
    
    def __init__(self, data_dump_dir, log_dir, pickle_dir, classname_to_fn):
        
        pickles, dump_dir = self.check_dirs(
            data_dump_dir, classname_to_fn, pickle_dir)
        res_dir = '{}/res'.format(os.path.dirname(sys.argv[0]))
        # initializing parsers which need data dumps
        parser_names = [
            'EthnologueDumpParser','LanguageArchivesOfflineParser',
            'UrielParser', 'DbpediaParserAggregator',
            'WikipediaAdjustedSizeCounter_WPExtractor',
            'WPIncubatorAdjustedSizeCounter',
            'EndangeredParser']
        eth_parser, la_parser, uriel_parser, dbpedia_parser,\
        wp_adjusted_parser, wpinc_adj_parser, endangered_parser = \
                self.init_dump_based_parsers(pickles, dump_dir, parser_names)
        #initializing all parsers
        self.parsers = [ParseISO639_3(), MacroWPParser(), uriel_parser, dbpedia_parser,
                        eth_parser, L2Parser(res_dir + "/" + "ethnologue_l2"),
                        CrubadanParser(), la_parser,
                        WalsInfoParser(res_dir), IndigenousParser(res_dir),
                        GoogleTranslateParser(res_dir),
                        WikipediaListOfLanguagesParser(res_dir),
                        WikipediaIncubatorsParser(res_dir),
                        wp_adjusted_parser,
                        endangered_parser, OmniglotParser(
                            '{0}/mappings/omniglot'.format(res_dir)),
                        FirefoxParser('{0}/mappings/firefox'.format(res_dir)),
                        SoftwareSupportParser(res_dir), wpinc_adj_parser]
        self.parsers = filter(lambda x:x != None, self.parsers)
        self.lang_db = LanguageDB()
        self.trusted_parsers = set([ParseISO639_3])
        self.parsers_needs_sil = set([EthnologueOfflineParser,
                                      EthnologueOnlineParser,
                                      LanguageArchivesOnlineParser])
        self.debug_dir = log_dir
        self.pickle_dir = pickle_dir

    def check_dirs(self, data_dump_dir, classname_to_fn, pickle_dir):
        
        dump_dir = {}
        pickle_fns = os.listdir(pickle_dir)
        pickled_pattern = re.compile('(.*?).pickle')
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
    
    def init_dump_based_parsers(self, pickles, dump_dir, parser_names):
        dummy_fn = 'dummy_fn'
        initialized_parsers = []
        for classname in parser_names:
            if classname in pickles:
                initialized_parsers.append(eval(classname)(dummy_fn))
            elif classname in dump_dir:
                if classname == 'EndangeredParser':
                    list_of_ids, endangered_dump_dir =\
                            dump_dir['EndangeredParser']
                    initialized_parsers.append(
                        EndangeredParser(list_of_ids, endangered_dump_dir))    
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
                    self.found_langs.append((lang, [tgt.name, tgt.sil]))
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
    

def get_args():
    parser = ArgumentParser()
    parser.add_argument('-d', '--data_dump_dir', help='directory of data dumps')
    parser.add_argument('-p', '--pickle_dir', help='directory of pickles')
    parser.add_argument('-l', '--log_dir', default='.',
                        help='directory for log files')
    parser.add_argument('-f', '--filename_mappings',
                        default='extern/ld/res/dump_filenames',
                        help='file mapping parser classnames to dumps')
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = get_args()
    classname_to_fn = dict([l.strip().split('\t')
                           for l in open(args.filename_mappings)])
    pa = ParserAggregator(args.data_dump_dir, args.pickle_dir, args.log_dir,
                          args.pickle_dir, classname_to_fn)
    pa.run()

if __name__ == "__main__":
    main()
