import logging

from dld.models import Language, Code, Country, LanguageCountry


class LanguageUpdate(object):
    pass


class LanguageDB(object):
    def __init__(self):
        self.languages = []
        self.spec_fields = set(["other_codes", "country"])

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

    def add_codes(self, data, lang):
        for src, code in data.iteritems():
            c = Code()
            c.code_name = src
            c.code = code
            c.language_id = lang
            c.save()

    def add_country(self, data, lang):
        c = Country.objects.filter(name=data)
        LanguageCountry(language=lang, country=c).save()

    def add_new_language(self, lang):
        """Inserts new language to db"""
        if not isinstance(lang, LanguageUpdate):
            raise TypeError("LanguageDB.add_new_language " +
                            "got non-LanguageUpdate instance")

        # TODO add language to db
        # new Language instance from LanguageUpdate instance
        logging.debug("adding lang {0}".format(lang.sil))
        l = Language()
        for key in lang.__dict__.iterkeys():
            if key.startswith("_"):
                continue
            try:
                self.add_attr(key, lang.__dict__[key], l)
            except Exception as e:
                logging.exception(e)

        self.languages.append(l)
        l.save()

    def update_lang_data(self, tgt, update):
        """Updates data for @tgt language"""
        if not isinstance(update, LanguageUpdate):
            raise TypeError("LanguageDB.update_lang_data " +
                            "got non-LanguageUpdate instance as @update")

        if not isinstance(tgt, Language):
            raise TypeError("LanguageDB.update_lang_data " +
                            "got non-Language instance as @tgt")

        # TODO update tgt's data with @update

    def get_closest(self, lang):
        """Looks for language that is most similar to lang"""
        if not isinstance(lang, LanguageUpdate):
            raise TypeError("LanguageDB.get_closest " +
                            "got non-LanguageUpdate instance as @lang")

        return []
