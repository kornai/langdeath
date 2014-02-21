from collections import defaultdict
import urllib
import zipfile
import os

from base_parsers import OnlineParser


class LanguageUpdate():
    # this class definition should be somewhere else
    def __init__(self):
        self.marolangs = set()
        self.other_iso_codes = {}
        self.names = set()
        # TODO book which name is from which source
        # iso-639-3 itself is inconsistent
        self.inverted_names = set()


class ParseISO639_3(OnlineParser):
    '''
    self.lang_dict = { iso_code : LanguageUpdate }
    '''
    def __init__(self):
        self.lang_dict = defaultdict(LanguageUpdate)

    def parse(self):
        (iso_zip_filen, headers) = urllib.urlretrieve(
            'http://www-01.sil.org/iso639-3/iso-639-3_Code_Tables_20140203.zip')
        self.dir_ = 'iso-639-3_Code_Tables_20140203/'
        self.iso_zip_file = zipfile.ZipFile(iso_zip_filen, 'r')
        self.parse_main_table()
        self.parse_macrolangs()
        self.parse_inverted_name()
        self.parse_retirements()
        os.remove(iso_zip_filen)

    def parse_main_table(self):
        with self.iso_zip_file.open(
            self.dir_+'iso-639-3_20140203.tab') as main_iso_file:
            for line in main_iso_file:
                sil_code, part2b, part2t, part1, scope, language_type, \
                        ref_name, comment = line.split('\t')
                if sil_code == 'Id': 
                    # header 
                    continue
                if scope == 'S': 
                    # special situations
                    continue
                self.lang_dict[sil_code].iso_scope = scope
                self.lang_dict[sil_code].iso_type = language_type
                self.lang_dict[sil_code].names.add(ref_name)

    def parse_macrolangs(self):
        with self.iso_zip_file.open(
            self.dir_+'iso-639-3-macrolanguages_20140203.tab') as macro_file:
            for line in macro_file:
                macro, indiv, stat = line.split('\t')
                if stat == 'R':
                    continue
                if macro == 'M_Id': 
                    # header 
                    continue
                self.lang_dict[indiv].marolangs.add(macro)
                #self.lang_dict[indiv].iso_stat = stat

    def parse_inverted_name(self):
        with self.iso_zip_file.open(
            self.dir_+'iso-639-3_Name_Index_20140203.tab') as name_file:
            for line in name_file:
                sil_code, print_name, inverted_name = line.split('\t')
                if sil_code == 'Id': 
                    # header 
                    continue
                self.lang_dict[sil_code].inverted_names.add(inverted_name)

    def parse_retirements(self):
        with self.iso_zip_file.open(
            self.dir_+'iso-639-3_Retirements_20140203.tab') as old_code_file:
            for line in old_code_file:
                old_code,  ref_name, ret_reason, change_to, ret_remedy, \
                effective = line.split('\t')
                if change_to:
                    if old_code == 'Id':
                        # header
                        continue
                    if 'retired' not in self.lang_dict[change_to].other_iso_codes:
                        self.lang_dict[change_to].other_iso_codes['retired'] = set()
                    self.lang_dict[change_to].other_iso_codes['retired'].add(old_code)
