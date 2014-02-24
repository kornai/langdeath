class BaseParser(object):
    pass

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
