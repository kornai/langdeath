import logging

from dld.models import Language, Code, Country, AlternativeName, CountryName

from ld.langdeath_exceptions import LangdeathException


class LanguageDB(object):
    def __init__(self):
        self.languages = []
        self.spec_fields = set(["other_codes", "country", "name", "alt_names"])

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
            self.add_alt_name(data, lang)

    def add_name(self, data, lang):
        if lang.name == "":
            lang.name = data
            return

        if data == lang.name:
            return

        self.add_alt_name(data, lang)

    def add_alt_name(self, data, lang):
        if type(data) == str or type(data) == unicode:
            data = data.lower().strip()
            if len(lang.alt_name.filter(name=data)) > 0:
                # duplication, don't do anything
                return

            a = AlternativeName(name=data)
            a.save()
            lang.save()
            lang.alt_name.add(a)
            lang.save()
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
            c.save()
            lang.save()
            lang.code.add(c)
            lang.save()

    def add_country(self, data, lang):
        if data is None:
            return

        cs = Country.objects.filter(name=data)
        if len(cs) == 0:
            altnames = CountryName.objects.filter(name=data)
            if len(altnames) > 0:
                for altname in altnames:
                    cname = altname.country.name
                    self.add_country(cname, lang)
            else:
                raise LangdeathException(
                    "unknown country for sil {0}: {1}".format(
                        lang.sil, repr(data)))
        else:
            c = cs[0]
            lang.save()
            c.save()
            lang.country.add(c)
            lang.save()

    def add_champion(self, data, lang):
        chs = Language.objects.filter(sil=data)
        if len(chs) != 1:
            msg = "champion field {0} is not deterministic".format(chs)
            raise LangdeathException(msg)
        ch = chs[0]
        chs.save(), lang.save()
        lang.champion = ch
        chs.save(), lang.save()

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
