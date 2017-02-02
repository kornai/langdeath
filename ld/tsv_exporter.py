import sys
from collections import defaultdict
from math import log

from dld.models import Language
from ld.parsers.endangered_utils import aggregate_category, geometric_mean

na = "n/a"


def simple_num_norm(value):
    return (1 if not value else round(value, 2))


def log_num_norm(value):
    return (1 if not value else round(log(value + 1), 2))


def bool_norm(value):
    return (1 if value else 0)


def hunspell_status_norm(value):
    if value == "yes":
        return 1.0
    elif value == "some tool":
        return 0.5
    elif value == "no need":
        return 0.0
    else:
        return 0.0

class TSVExporter():

    def __init__(self):

        self.prior_calculations()
    
    def prior_calculations(self):

        self.sil_eth_status_dict = {}
        self.sil_eth_status_dict = \
                self.calculate_category_average_values(
                    self.get_eth_status, average_function=lambda x:
                    round(sum(x)/len(x)))
        self.value_dicts = {}
        self.value_dicts['l1'] = \
                self.calculate_category_average_values(
                    self.get_l1_value)


    def get_eth_status(self, lang):
    
        eth_statuses = lang.endangered_levels.filter(src="ethnologue").all()
        if len(eth_statuses) == 0:
            return
        eth_status = eth_statuses[0].level
        eth_status = float(
            eth_status.replace("a", ".0").replace("b", ".5"))
        return float(eth_status)    
    
    def get_l1_value(self, lang):
    
            l1s = [l1 for l1 in lang.speakers.filter(l_type="L1").all()
                   if l1.src != "aggregate" and l1.num is not None]
            if len(l1s) == 0:
                return
            l1 = geometric_mean([l.num + 1 for l in l1s])
            return l1    
    
    def get_l2_value(self, lang):

        l2s = [l2 for l2 in lang.speakers.filter(l_type="L2").all()
               if l2.src != "aggregate" and l2.num is not None]
        if len(l2s) == 0:
            return
        else:
            l2 = l2s[0].num
            return l2
   
    def get_end_status(self, lang):

        end_statuses = lang.endangered_levels.all()
        to_agg = []
        for es in end_statuses:
            if es.src == "ethnologue":
                continue
            to_agg.append((es.level, es.confidence))
        end_status, end_conf = aggregate_category(to_agg)
        return end_status

    def calculate_category_average_values(self, lookup_function, 
                                          average_function=lambda x:
                                          geometric_mean([i+1 for i in x])):
        status_values = defaultdict(list)
        sil_values = {}
        for lang in Language.objects.all():
            sil = lang.sil
            v = lookup_function(lang)
            if v != None:
                status_values['_ALL_'].append(v)
                if sil in self.sil_eth_status_dict:
                    status_values[self.sil_eth_status_dict[sil]].append(v)
                sil_values[sil] = v
        for k in status_values:
            sil_values[k] = average_function(status_values[k])
        return sil_values
    
    def lookup_category_average(self, attr_name, sil):
        
        dictionary = self.value_dicts[attr_name]
        if sil in dictionary:
            return dictionary[sil]
        if sil in self.sil_eth_status_dict:
            return dictionary[self.sil_eth_status_dict[sil]]
        return dictionary['_ALL_']

    def export_to_tsv(self, ofstream):
    
        header = ["sil", "l1", "l2", "cru_docs", "cru_words",
                  "cru_chars", "cru_splchk", "cru_wt", "cru_udhr", "omni",
                  "la_primary_texts_online", "la_primary_texts_all",
                  "la_lang_descr_online", "la_lang_descr_all",
                  "la_lex_res_online", "la_lex_res_all",
                  "la_res_in_online", "la_res_in_all",
                  "la_res_about_online", "la_res_about_all",
                  "la_oth_res_in_online", "la_oth_res_in_all",
                  "la_oth_res_about_online", "la_oth_res_about_all",
                  "mac_input", "mac_input_partial", "microsoft_pack",
                  "win8_input_method", "office13_if_pack", "office13_lp",
                  "hunspell_status", "hunspell_coverage",
                  "wals_samples_100", "wals_samples_200",
                  "indi_blogs", "indi_posts", "indi_words", "indi_users",
                  "indi_tweets", "firefox_lpack", "firefox_dict",
                  "wp_articles", "wp_total", "wp_edits", "wp_admins", "wp_users",
                  "wp_active_users", "wp_images", "wp_depth", "wp_inc",
                  "wp_real_articles", "wp_adjusted_size", "wp_real_ratio",
                  "eth_status", "endangered_aggregated_status"]
        ofstream.write("#{0}\n".format("\t".join(header)))
    
        for lang in Language.objects.all():
            data = []
            data.append(lang.sil)
            data.append(log_num_norm(
                self.lookup_category_average("l1", lang.sil)))
            
            data.append(log_num_norm(self.get_l2_value(lang)))

            data.append(log_num_norm(lang.cru_docs))
            data.append(log_num_norm(lang.cru_words))
            data.append(log_num_norm(lang.cru_characters))
            data.append(bool_norm(lang.cru_floss_splchk))
            data.append(bool_norm(lang.cru_watchtower))
            data.append(bool_norm(lang.cru_udhr))
            data.append(bool_norm(lang.in_omniglot))
    
            data.append(log_num_norm(lang.la_primary_texts_online))
            data.append(log_num_norm(lang.la_primary_texts_all))
            data.append(log_num_norm(lang.la_lang_descr_online))
            data.append(log_num_norm(lang.la_lang_descr_all))
            data.append(log_num_norm(lang.la_lex_res_online))
            data.append(log_num_norm(lang.la_lex_res_all))
            data.append(log_num_norm(lang.la_res_in_online))
            data.append(log_num_norm(lang.la_res_in_all))
            data.append(log_num_norm(lang.la_res_about_online))
            data.append(log_num_norm(lang.la_res_about_all))
            data.append(log_num_norm(lang.la_oth_res_in_online))
            data.append(log_num_norm(lang.la_oth_res_in_all))
            data.append(log_num_norm(lang.la_oth_res_about_online))
            data.append(log_num_norm(lang.la_oth_res_about_all))
    
            data.append(bool_norm(lang.mac_input))
            data.append(bool_norm(lang.mac_input_partial))
            data.append(bool_norm(lang.microsoft_pack))
            data.append(bool_norm(lang.win8_input_method))
            data.append(bool_norm(lang.office13_if_pack))
            data.append(bool_norm(lang.office13_lp))
    
            data.append(hunspell_status_norm(lang.hunspell_status))
            data.append(simple_num_norm(lang.hunspell_coverage))
    
            data.append(log_num_norm(lang.wals_samples_100))
            data.append(log_num_norm(lang.wals_samples_200))
    
            data.append(log_num_norm(lang.indi_blogs))
            data.append(log_num_norm(lang.indi_posts))
            data.append(log_num_norm(lang.indi_words))
            data.append(log_num_norm(lang.indi_users))
            data.append(log_num_norm(lang.indi_tweets))
    
            data.append(bool_norm(lang.firefox_lpack))
            data.append(bool_norm(lang.firefox_dict))
    
            data.append(log_num_norm(lang.wp_articles))
            data.append(log_num_norm(lang.wp_total))
            data.append(log_num_norm(lang.wp_edits))
            data.append(log_num_norm(lang.wp_admins))
            data.append(log_num_norm(lang.wp_users))
            data.append(log_num_norm(lang.wp_active_users))
            data.append(log_num_norm(lang.wp_images))
            data.append(log_num_norm(lang.wp_depth))
            data.append(bool_norm(lang.wp_inc))
            data.append(log_num_norm(lang.wp_real_articles))
            data.append(log_num_norm(lang.wp_adjusted_size))
            try:
                data.append(log_num_norm(
                    lang.wp_real_articles/(lang.wp_articles + 1)))
            except TypeError:
                data.append(0)
            
            eth_status =\
                    self.sil_eth_status_dict.get(
                        lang.sil, self.sil_eth_status_dict['_ALL_'])
            data.append(eth_status)
            
            end_status = self.get_end_status(lang)
            if end_status == None:
                print lang.sil
                quit()
            data.append(end_status)
    
            ofstream.write("{0}\n".format("\t".join(str(d) for d in data)))
    
    
def main():
    a = TSVExporter()
    a.export_to_tsv(sys.stdout)
    
    
if __name__ == "__main__":
    main()
