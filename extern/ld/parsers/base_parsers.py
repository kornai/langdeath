import cPickle


class BaseParser(object):

    @property
    def pickle_fn(self):
        return type(self).__name__ + '.pickle'

    def load_from_file(self, ifn=None):
        fn = ifn if ifn else self.pickle_fn
        with open(fn) as f:
            return cPickle.load(f)

    def dump_to_file(self, ofn=None):
        fn = ofn if ofn else self.pickle_fn
        with open(fn, 'w') as f:
            lang_data = list(self.parse_all())
            f.write(cPickle.dumps(lang_data))

    def parse_all(self):
        return []


class OnlineParser(BaseParser):
    """Inherit this class if the parser will do everything on its own,
    downloading, parsing, no assistance, supplementary files are needed
    """


class OfflineParser(BaseParser):
    """Inherit this class if the parser will need some extern files that
    someone has to create. The creator should describe everything that is
    needed to make this parser work, like
    - download a file
    - unzip a file
    - run an external parser on the data before using this parser
    """
