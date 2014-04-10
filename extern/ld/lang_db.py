import logging

from dld.models import Language, Code, Country, LanguageCountry, \
    AlternativeName

from ld.langdeath_exceptions import LangdeathException


class LanguageUpdate(object):
    pass


class LanguageDB(object):
    def __init__(self):
        self.languages = []
        self.spec_fields = set(["other_codes", "country", "name"])

    def add_attr(self, name, data, lang):
        if name in self.spec_fields:
            self.add_spec_attr(name, data, lang)
        else:
            lang.__dict__[name] = data

    def add_spec_attr(self, name, data, lang):
        if name == "other_codes":
            self.add_codes(data, lang)
        elif name == "country":
            self.add_country(data, lang)
        elif name == "name":
            self.add_name(data, lang)

    def add_name(self, data, lang):
        if lang.name == "":
            lang.name = data
            return

        if data == lang.name:
            return

        # add alternative name
        AlternativeName(language=lang, name=data).save()

    def add_codes(self, data, lang):
        for src, code in data.iteritems():
            c = Code()
            c.code_name = src
            c.code = code
            c.language_id = lang
            c.save()

    def add_country(self, data, lang):
        cs = Country.objects.filter(name=data)
        if len(cs) == 0:
            raise LangdeathException("unknown country: {0}".format(data))
        LanguageCountry(language=lang, country=cs[0]).save()

    def add_new_language(self, lang):
        """Inserts new language to db"""
        if not isinstance(lang, LanguageUpdate):
            raise TypeError("LanguageDB.add_new_language " +
                            "got non-LanguageUpdate instance")

        # new Language instance from LanguageUpdate instance
        logging.debug("adding lang {0}".format(lang.sil))
        l = Language()
        self.update_lang_data(l, lang)
        self.languages.append(l)

    def update_lang_data(self, l, update):
        """Updates data for @tgt language"""
        if not isinstance(update, LanguageUpdate):
            raise TypeError("LanguageDB.update_lang_data " +
                            "got non-LanguageUpdate instance as @update")

        if not isinstance(l, Language):
            raise TypeError("LanguageDB.update_lang_data " +
                            "got non-Language instance as @tgt")

        for key in update.__dict__.iterkeys():
            if key.startswith("_"):
                continue
            try:
                self.add_attr(key, update.__dict__[key], l)
            except Exception as e:
                logging.exception(e)

        l.save()

    def get_closest(self, lang):
        """Looks for language that is most similar to lang"""
        if not isinstance(lang, LanguageUpdate):
            raise TypeError("LanguageDB.get_closest " +
                            "got non-LanguageUpdate instance as @lang")

        if "sil" in lang.__dict__:
            languages = Language.objects.filter(sil=lang.sil)
            return languages

        if "name" in lang.__dict__:
            languages = Language.objects.filter(name=lang.name)
            return languages

        return []
