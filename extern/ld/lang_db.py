import logging

from dld.models import Language


class LanguageUpdate(object):
    pass


class LanguageDB(object):
    def __init__(self):
        self.languages = []

    def add_new_language(self, lang):
        """Inserts new language to db"""
        if not isinstance(lang, LanguageUpdate):
            raise TypeError("LanguageDB.add_new_language " +
                            "got non-LanguageUpdate instance")

        # TODO add language to db
        # new Language instance from LanguageUpdate instance
        logging.debug("adding lang {0}".format(lang.sil))
        l = Language()
        for key in l.__dict__.iterkeys():
            try:
                l.__dict__[key] = lang.__dict__[key]
            except KeyError:
                pass
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

        if "name" in lang.__dict__:
            languages = Language.objects.filter(name=lang.name)
            return languages

        return []
