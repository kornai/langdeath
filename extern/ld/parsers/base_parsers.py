import cPickle
from os import path

from ld.langdeath_exceptions import ParserException


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
        with open(fn, 'wb') as f:
            lang_data = list(self.parse_all())
            f.write(cPickle.dumps(lang_data))

    def parse_or_load(self, pickle_fn=None, **kwargs):
        fn = pickle_fn if pickle_fn else self.pickle_fn
        if hasattr(self, 'pickle_dir'):
            fn = '{}/{}'.format(self.pickle_dir, fn)
        print fn, path.exists(fn)    
        if path.exists(fn):
            with open(fn, 'rb') as f:
                for res in cPickle.load(f):
                    yield res
        else:
            d = []
            try:
                for data in self.parse_all(**kwargs):
                    yield data
                    d.append(data)
                with open(fn, 'wb') as f:
                    f.write(cPickle.dumps(d))
            except ParserException as e:
                if len(d) > 0:
                    with open(fn, 'wb') as f:
                        f.write(cPickle.dumps(d))
                raise e

    def parse_all(self, **kwargs):
        raise NotImplementedError()


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
