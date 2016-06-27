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
        if type(data) == str or type(data) == unicode:
            name = normalize_alt_name(data)

            # Truth checking for blank strings: '' resolves to False
            if not name or not data:
                raise LangdeathException("Empty alt_name: original " + \
                  "`{0}', normalized `{1}'".format(data, name))

            try:
                alt = AlternativeName.objects.get(name=name)
            except AlternativeName.DoesNotExist:
                alt = AlternativeName.objects.create(name=name)

            # adding an object that already is associated is a no-op
            lang.alt_name.add(alt)

            if len(set(name.split()) &
                   set(["east", "west", "north", "south"])) > 0:
                name = card_dir_p.sub("\g<1>ern", name)
                self.add_alt_name(name, lang)

        elif type(data) == list or type(data) == set:
            for d in data:
                self.add_alt_name(d, lang)
        else:
            raise LangdeathException("LangDB.add_alt_name got unknown type")

    def add_codes(self, data, lang):
        for src, code in data.iteritems():
            if type(code) == list:
                for c in code:
                    self.add_code(src, c, lang)
            else:
                self.add_code(src, code, lang)
    
    def add_code(self, src, code, lang):             
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
            lang.country.add(c)

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
        lang.champion = ch

    def add_macrolang(self, data, lang):
        d = list(data)[0] 
        mls = Language.objects.filter(sil=d)
        ml = mls[0] 
        lang.macrolang = ml

    def add_endangered_levels(self, data, lang):
        for src, level, conf in data:
            el = EndangeredLevel(src=src[:90], level=level, confidence=conf)
            el.save()
            lang.endangered_levels.add(el)

    def add_location(self, data, lang):
        for src, lon, lat in data:
            c = Coordinates(src=src[:90], longitude=lon, latitude=lat)
            c.save()
            lang.locations.add(c)

    def add_speakers(self, data, lang):
        for src, type_, num in data:
            s = Speaker(src=src[:90], num=num, l_type=type_)
            s.save()
            lang.speakers.add(s)

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
            except LangdeathException as e:
                logging.warning(e)
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

    def compile_name_pattern(self):
        self.pname_pattern = re.compile('(Online|Offline){0,1}Parser')

    def format_integrated_code(self, code, notation):
        '''
        Currently all codes are padded to 16 characters
        (which is the size of the top-size code occured)
        '''
        if notation == 'M':
            return '{}M'.format(code.split(',')[0].ljust(16, '_'))
        elif notation == 'O':
            pname = re.split(self.pname_pattern, code)[0][:12]
            index = code.split('.')[1]
            return '{}{}O'.format(pname, index.ljust(16-len(pname), '_'))
        else:
            return '{}{}'.format(code.ljust(16, '_'), notation)

    def get_other_code(self, codes, code_type):
        filtered_codes = codes.filter(code_name=code_type).all()
        if len(filtered_codes) == 0:
            return
        co = [pair.code for pair in filtered_codes]
        return max(set(co), key=co.count)

    def get_indi_code_mapping(self):
        '''
        sil codes in sil clusters (returned by EndangeredParser)
        get code specified here
        '''
        ms = [c.code for c in Code.objects.all()
              .filter(code_name='multiple_sils')]
        self.indi_codes = dict(
            sum([[(sil, '{}{}{}'.format(cluster.split(',')[0], sil, i))
                  for i, sil in enumerate(cluster.split(','))]
                 for cluster in ms], []))

    def integrate_codes(self):
        self.compile_name_pattern()
        self.get_indi_code_mapping()
        for lang in Language.objects.all():
            sil = lang.sil
            found = False
            if len(sil) == 3:
                # sil code; active or retired
                found = True
                if sil not in self.indi_codes:
                    code = sil
                    if lang.iso_active:
                        notation = 'A'
                    else:
                        notation = 'R'
                else:
                    code = self.indi_codes[sil]
                    if lang.iso_active:
                        notation = 'a'
                    else:
                        notation = 'r'
            else:
                # look for other code
                other_codes = lang.code.all()\
                        .exclude(code=None).exclude(code='none')
                for code_type, notation in [('multiple_sils', 'M'),
                                            ('linglist', 'L'),
                                            ('glotto', 'G'),
                                            ('bcp_47', 'B')]:
                    code = self.get_other_code(other_codes, code_type)
                    if code:
                        found = True
                        break
            if not found:
                # integrated code is just the temporary (ParserName_{index})
                code = sil
                notation = 'O'
            formatted = self.format_integrated_code(code, notation)
            lang.integrated_code = formatted
            lang.save()
