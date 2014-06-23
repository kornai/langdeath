import sys

from dld.models import Language
from ld.parsers.endangered_utils import aggregate_category

default_eth_status = 7.7
na = "n/a"


def num_norm(value):
    return (na if not value else value)


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


def export_to_tsv(ofstream):
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
              "wp_real_articles", "wp_adjusted_size",
              "eth_status", "endangered_aggregated_status"]

    ofstream.write("#{0}\n".format("\t".join(header)))

    for lang in Language.objects.all():
        data = []

        data.append(lang.sil)

        l1s = lang.speakers.filter(l_type="L1").all()
        if len(l1s) == 0:
            l1 = na
        else:
            l1 = sum(l.num for l in l1s) / float(len(l1s))
        data.append(l1)
        l2s = lang.speakers.filter(l_type="L2").all()
        if len(l2s) == 0:
            l2 = na
        else:
            l2 = l2s[0].num
        data.append(l2)

        data.append(num_norm(lang.cru_docs))
        data.append(num_norm(lang.cru_words))
        data.append(num_norm(lang.cru_characters))
        data.append(bool_norm(lang.cru_floss_splchk))
        data.append(bool_norm(lang.cru_watchtower))
        data.append(bool_norm(lang.cru_udhr))
        data.append(bool_norm(lang.in_omniglot))

        data.append(num_norm(lang.la_primary_texts_online))
        data.append(num_norm(lang.la_primary_texts_all))
        data.append(num_norm(lang.la_lang_descr_online))
        data.append(num_norm(lang.la_lang_descr_all))
        data.append(num_norm(lang.la_lex_res_online))
        data.append(num_norm(lang.la_lex_res_all))
        data.append(num_norm(lang.la_res_in_online))
        data.append(num_norm(lang.la_res_in_all))
        data.append(num_norm(lang.la_res_about_online))
        data.append(num_norm(lang.la_res_about_all))
        data.append(num_norm(lang.la_oth_res_in_online))
        data.append(num_norm(lang.la_oth_res_in_all))
        data.append(num_norm(lang.la_oth_res_about_online))
        data.append(num_norm(lang.la_oth_res_about_all))

        data.append(bool_norm(lang.mac_input))
        data.append(bool_norm(lang.mac_input_partial))
        data.append(bool_norm(lang.microsoft_pack))
        data.append(bool_norm(lang.win8_input_method))
        data.append(bool_norm(lang.office13_if_pack))
        data.append(bool_norm(lang.office13_lp))

        data.append(hunspell_status_norm(lang.hunspell_status))
        data.append(num_norm(lang.hunspell_coverage))

        data.append(num_norm(lang.wals_samples_100))
        data.append(num_norm(lang.wals_samples_200))

        data.append(num_norm(lang.indi_blogs))
        data.append(num_norm(lang.indi_posts))
        data.append(num_norm(lang.indi_words))
        data.append(num_norm(lang.indi_users))
        data.append(num_norm(lang.indi_tweets))

        data.append(bool_norm(lang.firefox_lpack))
        data.append(bool_norm(lang.firefox_dict))

        data.append(num_norm(lang.wp_articles))
        data.append(num_norm(lang.wp_total))
        data.append(num_norm(lang.wp_edits))
        data.append(num_norm(lang.wp_admins))
        data.append(num_norm(lang.wp_users))
        data.append(num_norm(lang.wp_active_users))
        data.append(num_norm(lang.wp_images))
        data.append(num_norm(lang.wp_depth))
        data.append(bool_norm(lang.wp_inc))
        data.append(num_norm(lang.wp_real_articles))
        data.append(num_norm(lang.wp_adjusted_size))

        eth_statuses = lang.endangered_levels.filter(src="ethnologue").all()
        if len(eth_statuses) == 0:
            eth_status = default_eth_status
        else:
            eth_status = eth_statuses[0].level
            eth_status = float(
                eth_status.replace("a", "").replace("b", ""))
        data.append(eth_status)

        end_statuses = lang.endangered_levels.all()
        to_agg = []
        for es in end_statuses:
            if es.src == "ethnologue":
                continue
            to_agg.append((es.level, es.confidence))
        end_status, end_conf = aggregate_category(to_agg)
        data.append(end_status)

        ofstream.write("{0}\n".format("\t".join(str(d) for d in data)))


def main():
    export_to_tsv(sys.stdout)


if __name__ == "__main__":
    main()
