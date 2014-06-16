from base_parsers import OnlineParser
import urllib2
import re

class Office13IpFAQParser(OnlineParser):

    def parse(self):
        self.url = 'http://office.microsoft.com/en-us/language-packs/microsoft-office-language-packs-2013-faq-faqs-FX102897395.aspx'
        self.precontext = 'Individual Office Language Packs are available for the following languages:'
        response = urllib2.urlopen(self.url)
        html = response.read()
        iter_lines = iter(html.split('\n'))
        for line in iter_lines:
            if line.strip().startswith(self.precontext):
                for lang in re.split(
                    ', (?:and )?', iter_lines.next().strip().strip('.')):
                    yield {'native_name': lang.strip(), 'office13_lp': True}
                break

if __name__ == '__main__':
    p = Office13IpFAQParser()
    p.parse()
