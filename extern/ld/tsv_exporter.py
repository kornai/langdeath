import sys

from dld.models import Language

default_eth_status = 7.7
na = "n/a"


def num_norm(value):
    return (na if not value else value)


def bool_norm(value):
    return (1 if value else 0)


def export_to_tsv(ofstream):
    header = ["sil", "eth_status", "eth_pop", "cru_docs", "cru_words",
              "cru_chars", "cru_splchk", "cru_wt", "cru_udhr", "omni",
              "la_primary_texts_online", "la_primary_texts_all",
              "la_lang_descr_online", "la_lang_descr_all",
              "la_lex_res_online", "la_lex_res_all",
              "la_res_in_online", "la_res_in_all",
              "la_res_about_online", "la_res_about_all",
              "la_oth_res_in_online", "la_oth_res_in_all",
              "la_oth_res_about_online", "la_oth_res_about_all",
              "mac_input", "mac_input_partial", "microsoft_pack",
              "win8_input_method", "office_if_pack",
              "wals_samples_100", "wals_samples_200",
              "indi_blogs", "indi_posts", "indi_words", "indi_users",
              "indi_tweets"]
    ofstream.write("#{0}\n".format("\t".join(header)))

    for lang in Language.objects.all():
        data = []

        data.append(lang.sil)

        eth_status = lang.eth_status
        if not eth_status:
            eth_status = default_eth_status
        else:
            eth_status = float(
                eth_status.replace("a", "").replace("b", ""))
        data.append(eth_status)

        data.append(num_norm(lang.eth_population))

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
        data.append(bool_norm(lang.office_if_pack))

        data.append(num_norm(lang.wals_samples_100))
        data.append(num_norm(lang.wals_samples_200))

        data.append(num_norm(lang.indi_blogs))
        data.append(num_norm(lang.indi_posts))
        data.append(num_norm(lang.indi_words))
        data.append(num_norm(lang.indi_users))
        data.append(num_norm(lang.indi_tweets))

        ofstream.write("{0}\n".format("\t".join(str(d) for d in data)))

def main():
    export_to_tsv(sys.stdout)


if __name__ == "__main__":
    main()
