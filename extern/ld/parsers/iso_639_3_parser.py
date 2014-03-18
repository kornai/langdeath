from collections import defaultdict
import urllib
import zipfile
import os

from base_parsers import OnlineParser
from ld.lang_db import LanguageUpdate

class ParseISO639_3(OnlineParser):
    """
    self.lang_dict = { iso_code : LanguageUpdate }
    """
    def __init__(self):
        self.lang_dict = defaultdict(LanguageUpdate)
        self.url = 'http://www-01.sil.org/iso639-3/iso-639-3_Code_Tables_20140203.zip'

    def parse(self):
        (iso_zip_filen, headers) = urllib.urlretrieve(self.url)
        self.dir_ = self.url.rsplit('/',1)[1].split('.')[0]+'/'
        self.iso_zip_file = zipfile.ZipFile(iso_zip_filen, 'r')
        self.parse_main_table()
        self.parse_macrolangs()
        self.parse_inverted_name()
        self.parse_retirements()
        os.remove(iso_zip_filen)
        for lang_upd in self.lang_dict.itervalues():
            if lang_upd.iso_scope == 'S': 
                # special situations
                continue
            yield lang_upd

    def parse_main_table(self):
        """
        Meaning of fileds in the original file:
        Id          The three-letter 639-3 identifier
        Part2B      Equivalent 639-2 identifier of the bibliographic
                    applications code set, if there is one
        Part2T      Equivalent 639-2 identifier of the terminology applications
                    code set, if there is one
        Part1       Equivalent 639-1 identifier, if there is one    
        Scope       I(ndividual), M(acrolanguage), S(pecial)
        Type        A(ncient), C(onstructed),  E(xtinct), H(istorical),
                    L(iving), S(pecial)
        Ref_Name    Reference language name 
        Comment     Comment relating to one or more of the columns 
        """
        with self.iso_zip_file.open(
            self.dir_+'iso-639-3_20140203.tab') as main_iso_file:
            for line in main_iso_file:
                sil_code, part2b, part2t, part1, scope, language_type, \
                        ref_name, comment = line.strip('\n\r').split('\t')
                if sil_code == 'Id': 
                    # header 
                    continue
                d = self.lang_dict[sil_code]
                d.name = ref_name.decode("utf-8")
                d.sil = sil_code
                if part1:
                    d.other_codes = {'iso-639-1': [part1]}

                d.iso_scope = scope
                d.iso_type = language_type

    def parse_macrolangs(self):
        """
        Meaning of fileds in the original file:
        M_Id        The identifier for a macrolanguage
        I_Id        The identifier for an individual language that is a member
                    of the macrolanguage
        I_Status    A (active) or R (retired) indicating the status of the
                    individual code element
        """
        with self.iso_zip_file.open(
            self.dir_+'iso-639-3-macrolanguages_20140203.tab') as macro_file:
            for line in macro_file:
                macro, indiv, stat = line.strip('\n\r').split('\t')
                if stat == 'R':
                    continue
                if macro == 'M_Id': 
                    # header 
                    continue
                self.lang_dict[indiv].macrolangs = set([macro])
                #self.lang_dict[indiv].iso_stat = stat

    def parse_inverted_name(self):
        """
        Meaning of fileds in the original file:
        Id                The three-letter 639-3 identifier
        Print_Name        One of the names associated with this identifier 
        Inverted_Name     The inverted form of this Print_Name form   
        """
        with self.iso_zip_file.open(
            self.dir_+'iso-639-3_Name_Index_20140203.tab') as name_file:
            for line in name_file:
                sil_code, print_name, inverted_name = line.strip('\n\r').split('\t')
                if sil_code == 'Id': 
                    # header 
                    continue
                self.lang_dict[sil_code].inverted_names = set([inverted_name])

    def parse_retirements(self):
        """
        Meaning of fileds in the original file:
        Id              The three-letter 639-3 identifier
        Ref_Name        reference name of language
        Ret_Reason      code for retirement: C (change), D (duplicate), 
                        N (non-existent), S (split), M (merge)
        Change_To       the cases of C, D, and M, the identifier to which all
                        instances of this Id should be changed
        Ret_Remedy      The instructions for updating an instance of the
                        retired (split) identifier
        Effective date  Te date the retirement became effective
        """
        with self.iso_zip_file.open(
            self.dir_+'iso-639-3_Retirements_20140203.tab') as old_code_file:
            for line in old_code_file:
                old_code,  ref_name, ret_reason, change_to, ret_remedy, \
                effective = line.strip('\n\r').split('\t')
                if change_to:
                    if old_code == 'Id':
                        # header
                        continue
                    elif change_to == old_code:
                        # data error with language yuu
                        continue
                    elif change_to not in self.lang_dict:
                        # data error, lcq --> ppr insted of ppr --> lcq
                        continue
