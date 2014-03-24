import urllib2
from ld.langdeath_exceptions import ParserException

def get_html(url, encoding='utf-8'):

    try:
        response = urllib2.urlopen(url)
        html = response.read().decode(encoding)
        return html
    except:
        raise ParserException('Problem with downloading {}\n'.format(url))
