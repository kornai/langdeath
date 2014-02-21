from collections import defaultdict
import urllib
import zipfile
import warnings


class LanguageUpdate():
    # this class definition should be somewhere else
    def __init__(self):
        self.marolangs = set()
        self.other_iso_codes = {}
        self.names = set()
        # TODO book which name is from which source
        # iso-639-3 itself is inconsistent
        self.inverted_names = set()


#def assert_name(lang_dict, iso_code, name):
#    # TODO compare name with the name obtained from iso-639-3_20140203.tab?
#    if name not in lang_dict[iso_code].names:
#        warnings.warn('names for {}  differ in iso files'.format(iso_code))
#        raise Exception((name,lang_dict[iso_code].names))


if __name__ == '__main__':
    (iso_zip_filen, headers) = urllib.urlretrieve(
        'http://www-01.sil.org/iso639-3/iso-639-3_Code_Tables_20140203.zip')
    lang_dict = defaultdict(LanguageUpdate)
    dir_ = 'iso-639-3_Code_Tables_20140203/'
    with zipfile.ZipFile(iso_zip_filen, 'r') as iso_zip_file:
        with iso_zip_file.open(
            dir_+'iso-639-3_20140203.tab') as main_iso_file:
            for line in main_iso_file:
                sil_code, part2b, part2t, part1, scope, language_type, \
                ref_name, comment = line.split('\t')
                if sil_code == 'Id': 
                    # header 
                    continue
                if scope == 'S': 
                    # special situations
                    continue
                lang_dict[sil_code].iso_scope = scope
                lang_dict[sil_code].iso_type = language_type
                lang_dict[sil_code].names.add(ref_name)
                #if part2b:
                #    lang_dict[sil_code].other_iso_codes[
                #        '639-2_bibliographic'] = part2b
                #if part2t:
                #    lang_dict[sil_code].other_iso_codes[
                #        '639-2_terminology'] = part2t
                #if part1:
                #    lang_dict[sil_code].other_iso_codes[
                #        '639-1'] = part1
        with iso_zip_file.open(
            dir_+'iso-639-3-macrolanguages_20140203.tab') as macro_file:
            for line in macro_file:
                macro, indiv, stat = line.split('\t')
                if stat == 'R':
                    continue
                if macro == 'M_Id': 
                    # header 
                    continue
                lang_dict[indiv].marolangs.add(macro)
                #lang_dict[indiv].iso_stat = stat
        with iso_zip_file.open(
            dir_+'iso-639-3_Name_Index_20140203.tab') as name_file:
            for line in name_file:
                sil_code, print_name, inverted_name = line.split('\t')
                if sil_code == 'Id': 
                    # header 
                    continue
                #assert_name(lang_dict, sil_code, print_name)
                lang_dict[sil_code].inverted_names.add(inverted_name)
        with iso_zip_file.open(
            dir_+'iso-639-3_Retirements_20140203.tab') as old_code_file:
            for line in old_code_file:
                old_code,  ref_name, ret_reason, change_to, ret_remedy, \
                effective = line.split('\t')
                if change_to:
                    #assert_name(lang_dict, change_to, ref_name)
                    if 'retired' not in lang_dict[change_to].other_iso_codes:
                        lang_dict[change_to].other_iso_codes['retired'] = set()
                    lang_dict[change_to].other_iso_codes['retired'].add(old_code)
