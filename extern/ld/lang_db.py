from dld.models import Language


class LanguageUpdate(object):
    pass


class LanguageDB(object):
    def __init__(self):
        pass

    def add_new_language(self, lang):
        """Inserts new language to db
        """
        if not isinstance(lang, LanguageUpdate):
            raise TypeError("LanguageDB.add_new_language " +
                            "got non-LanguageUpdate instance")

        # TODO add language to db
        # new Language instance from LanguageUpdate instance

    def update_lang_data(self, tgt, update):
        """Updates data for @tgt language
        """
        if not isinstance(update, LanguageUpdate):
            raise TypeError("LanguageDB.update_lang_data " +
                            "got non-LanguageUpdate instance as @update")

        if not isinstance(tgt, Language):
            raise TypeError("LanguageDB.update_lang_data " +
                            "got non-Language instance as @tgt")

        # TODO update tgt's data with @update
