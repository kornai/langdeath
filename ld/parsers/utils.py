import re
import urllib2
from ld.langdeath_exceptions import ParserException

def get_html(url, encoding='utf-8'):

    try:
        response = urllib2.urlopen(url)
        html = response.read().decode(encoding)
        return html
    except:
        raise ParserException('Problem with downloading {}\n'.format(url))

def replace_html_formatting(string, additional_patterns = []):
    
    string = re.sub('<[/]{0,1}a.*?>', '', string)
    string = re.sub('<[/]{0,1}b>', '', string)
    for pattern in additional_patterns:
        string = re.sub(pattern, '', string)
    return string 
