import logging
import re

from dld.models import normalize_alt_name, \
                       AlternativeName, \
                       Code, \
                       Coordinates, \
                       Country, \
                       CountryName, \
                       EndangeredLevel, \
                       Language, \
                       LanguageAltName, \
                       Parser, \
                       Speaker

from ld.langdeath_exceptions import LangdeathException

card_dir_p = re.compile("((east)|(west)|(north)|(south))")


class LanguageDB(object):
    def __init__(self):
        self.languages = []
        self.spec_fields = set(["other_codes",
                                "country",
                                "name",
                                "alt_names",
                                "champion",
                                "speaker",
                                "speakers",
                                "endangered_level",
                                "location",
                                "macrolangs",
                                "parser"])

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
        elif name == "native_name":
            self.add_native_name(data, lang)
        elif name == "alt_names":
            self.add_alt_name(data, lang)
        elif name == "champion":
            self.add_champion(data, lang)
        elif name == "endangered_level":
            self.add_endangered_levels(data, lang)
        elif name == "speaker" or name == "speakers":
            self.add_speakers(data, lang)
        elif name == "location":
            self.add_location(data, lang)
        elif name == "macrolangs":
            self.add_macrolang(data, lang)
        elif name == "parser":
            self.add_parser(data, lang)

    def add_name(self, data, lang):
        if lang.name == "":
            lang.name = data

        if data == lang.name:
            return

        self.add_alt_name(data, lang)

    def add_native_name(self, data, lang):
        if lang.native_name == "":
            lang.name = data

        if data == lang.native_name:
            return

        self.add_alt_name(data, lang)

    def add_alt_name(self, data, lang):
        lang.save()
        if type(data) == str or type(data) == unicode:
            data = normalize_alt_name(data)
            if len(lang.alt_name.filter(name=data)) > 0:
                # duplication, don't do anything
                return

            alts = AlternativeName.objects.filter(name=data).all()
            if len(alts) == 0:
                a = AlternativeName(name=data)
                a.save()
            elif len(alts) == 1:
                a = alts[0]
                a.save()
            else:
                logging.error(u"There are 2+ altnames with data {0}".format(
                    data))

            la = LanguageAltName(lang=lang, name=a)
            a.save(), lang.save(), la.save()

            if len(set(data.split()) &
                   set(["east", "west", "north", "south"])) > 0:
                data = card_dir_p.sub("\g<1>ern", data)
                self.add_alt_name(data, lang)

        elif type(data) == list or type(data) == set:
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
        
        if len(chs) == 0:
            msg = "champion code {}".format(lang.sil)
            msg += " is not in database, so this champion doesn't get added"
            raise LangdeathException(msg)

        if len(chs) > 1:
            msg = "champion field {0} is not deterministic".format(chs)
            msg += " for lang {0} with sil {1}".format(lang.sil, data)
            raise LangdeathException(msg)
        ch = chs[0]
        ch.save(), lang.save()
        lang.champion = ch
        ch.save(), lang.save()

    def add_macrolang(self, data, lang):
        d = list(data)[0] 
        mls = Language.objects.filter(sil=d)
        ml = mls[0]
        ml.save(), lang.save()
        lang.macrolang = ml
        ml.save(), lang.save()

    def add_endangered_levels(self, data, lang):
        for src, level, conf in data:
            el = EndangeredLevel(src=src[:90], level=level, confidence=conf)
            el.save()
            lang.save()
            lang.endangered_levels.add(el)
            el.save()
            lang.save()

    def add_location(self, data, lang):
        for src, lon, lat in data:
            c = Coordinates(src=src[:90], longitude=lon, latitude=lat)
            c.save()
            lang.save()
            lang.locations.add(c)
            c.save()
            lang.save()

    def add_speakers(self, data, lang):
        for src, type_, num in data:
            s = Speaker(src=src[:90], num=num, l_type=type_)
            s.save()
            lang.save()
            lang.speakers.add(s)
            s.save()
            lang.save()

    def add_parser(self, parser_name, lang):
        try:
          p = Parser.objects.get(classname=parser_name)
        except Parser.DoesNotExist:
          p = Parser.objects.create(classname=parser_name)

        lang.parsers.add(p)

    def add_new_language(self, lang):
        """Inserts new language to db"""
        if not isinstance(lang, dict):
            raise TypeError("LanguageDB.add_new_language " +
                            "got non-dict instance")

        l = Language.objects.create()
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
            if key == "id":
                continue
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
                            "got non-dict instance as @lang: {0}".format(
                                repr(lang)))

        if "sil" in lang:
            languages = Language.objects.filter(sil=lang['sil'])
            return languages, 'sil'

        if "other_codes" in lang:
            for src, code in lang["other_codes"].iteritems():
                languages = Language.objects.filter(code__code_name=src,
                                                    code__code=code)
                # Relationship-spanning filters may return redundant entries
                languages = languages.distinct()

                if len(languages) > 0:
                    return languages, 'other_codes'

        if "name" in lang:
            languages = Language.objects.filter(name=lang['name'])
            if len(languages) > 0:
                return languages, 'name'

            # native name
            languages = Language.objects.filter(native_name=lang['name'])
            if len(languages) > 0:
                return languages, 'native_name'

            # try with alternative names
            languages = Language.objects.filter(
                alt_name__name=normalize_alt_name(lang['name']))
            return languages, 'altname'

        return [], None

    def choose_candidates(self, lang, l):
        """TODO later proper candidate selection"""
        return l
