import logging

from dld.models import Language, Code, Country, LanguageCountry, \
    AlternativeName

from ld.langdeath_exceptions import LangdeathException


class LanguageDB(object):
    def __init__(self):
        self.languages = []
        self.spec_fields = set(["other_codes", "country", "name"])
        self.country_alternatives = {
            u'C\xf4te d\u2019Ivoire': 'Ivory Coast',
            u'Russian Federation': 'Russia',
            u'Viet Nam': 'Vietnam',
            u'S\xe3o Tom\xe9 e Princ\xedpe': 'Sao Tome e Principe',
            u'Congo': ['Democratic Republic of the Congo',
                       'Republic of the Congo'],
            u'Palestine': 'Palestinian Territory',
            u'Vatican State': 'Vatican',
            u'Korea, South': 'South Korea',
            u'Cape Verde Islands': 'Cape Verde',
            u'R\xe9union': 'Reunion',
        }

    def add_attr(self, name, data, lang):
        if name in self.spec_fields:
            self.add_spec_attr(name, data, lang)
        else:
            if data is not None:
                lang.__dict__[name] = data

    def add_spec_attr(self, name, data, lang):
        if name == "other_codes":
            self.add_codes(data, lang)
        elif name == "country":
            self.add_country(data, lang)
        elif name == "name":
            self.add_name(data, lang)
        elif name == "alt_names":
            self.add_name(data, lang)

    def add_name(self, data, lang):
        if lang.name == "":
            lang.name = data
            return

        if data == lang.name:
            return

        self.add_alt_name(data, lang)

    def add_alt_name(self, data, lang):
        if type(data) == str or type(data) == unicode:
            AlternativeName(language=lang, name=data).save()
        elif type(data) == list:
            for d in data:
                self.add_alt_name(d, lang)
        else:
            raise LangdeathException("LangDB.add_alt_name got unknown type")

    def add_codes(self, data, lang):
        for src, code in data.iteritems():
            c = Code()
            c.code_name = src
            c.code = code
            c.language_id = lang
            c.save()

    def add_country(self, data, lang):
        if data in self.country_alternatives:
            if type(self.country_alternatives[data]) is list:
                for d in self.country_alternatives[data]:
                    self.add_country(d, lang)
                return

            else:
                data = self.country_alternatives[data]
        cs = Country.objects.filter(name=data)
        if len(cs) == 0:
            raise LangdeathException("unknown country for sil {0}: {1}".format(
                lang.sil, repr(data)))
        LanguageCountry(language=lang, country=cs[0]).save()

    def add_new_language(self, lang):
        """Inserts new language to db"""
        if not isinstance(lang, dict):
            raise TypeError("LanguageDB.add_new_language " +
                            "got non-dict instance")

        logging.debug("adding lang {0}".format(lang['sil']))
        l = Language()
        self.update_lang_data(l, lang)
        self.languages.append(l)

    def update_lang_data(self, l, update):
        """Updates data for @tgt language"""
        if not isinstance(update, dict):
            raise TypeError("LanguageDB.update_lang_data " +
                            "got non-dict instance as @update")

        if not isinstance(l, Language):
            raise TypeError("LanguageDB.update_lang_data " +
                            "got non-Language instance as @tgt")

        for key in update.iterkeys():
            if key.startswith("_"):
                continue
            try:
                self.add_attr(key, update[key], l)
            except Exception as e:
                logging.exception(e)

        l.save()

    def get_closest(self, lang):
        """Looks for language that is most similar to lang"""
        if not isinstance(lang, dict):
            raise TypeError("LanguageDB.get_closest " +
                            "got non-dict instance as @lang")

        if "sil" in lang:
            languages = Language.objects.filter(sil=lang['sil'])
            return languages

        if "name" in lang:
            languages = Language.objects.filter(name=lang['name'])
            return languages

        return []
