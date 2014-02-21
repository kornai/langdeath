import sys
import urllib2

from base_parsers import OnlineParser

class EthnologueParser(OnlineParser):

    def __init__(self, sil_code):
	self.sil_code = sil_code
	self.url = 'http://www.ethnologue.com/language/{0}'.format(sil_code)

    def strip_nonstring(self, string):
    
        while len(string) > 0 and string[0] == '<':
            string = string.split('>')[1].split('<')[0]
        return string
    
    def get_value_dictionary(self, list_):
    
        dictionary = {}
        for item in list_:
            key = item.split('>')[1].split('</')[0].strip()
            values = item.split('<span class="field-content">')
            if len(values) > 1:
                value = item.split('<span class="field-content">')[1].split(
    		    '</span>')[0].strip()
            else:
                value = item.split('<div class="field-content">')[1].split(
    		    '</div>')[0].strip()
            dictionary[key] = value
        return dictionary 
    
    def parse_attachement(self, attachement_rows):
    
        dictionary = {}
        for row in attachement_rows:
            key_extras = row.split('<div class="field-content">'
    		)[1].split('</div>')[0]
            key = self.strip_nonstring(key_extras).strip()
            value_list = row.split("<strong class=")[1:] 
            value_dictionary = self.get_value_dictionary(value_list)
            dictionary[key] = value_dictionary
        return dictionary    
    
    def parse_rows(self, table):
    
        dictionary = {}
        for row in table:
            key = row.split('</div>')[0].strip()
            value_wrapped = '</div>'.join(row.split('</div>')[1:])
            if len(value_wrapped.split('<div class="field-item even">')) > 1:
                value_extras = value_wrapped.split('<div class="field-item even">'
    		    )[1].split('</div>')[0]
            else:
                value_extras = value_wrapped.split('<div class="field-item">'
    		    )[1].split('</div>')[0]
            value = self.strip_nonstring(value_extras).strip()
            dictionary[key] = value
        return dictionary    
    
    def get_dictionary(self, string):
    
        title = string.split('<h1 class="title" id="page-title">')[1]\
    	    .split('</h1>')[0]
        country_whole = string.split('<h2>')[1].split('>')[1]
        
        country = country_whole.split('</a')[0]
        first_table_rows = string.split('<div class="field-label">')[1:-1]\
        + [string.split('<div class="field-label">')[-1]\
        .split('<div class="attachment attachment-after">')[0]]
        dictionary = self.parse_rows(first_table_rows)
        dictionary['Name'] = title
        dictionary['Country'] = country
        attachement = string.split('<div class="attachment attachment-after">')\
        [1].split('<aside class="grid-6 region region-sidebar-second"id="\
        region-sidebar-second">')[0]
    
        if  '<div class="view-header">' in attachement:
            attachement_title = attachement.split('<h3>')[1].split('</h3>')[0]
            attachement_rows = attachement.split('<div class=\
            "views-field views-field-field-country views-accordion-header">')[1:]
            dictionary_2 = self.parse_attachement(attachement_rows) 
            dictionary[attachement_title] = dictionary_2
        return dictionary
    
    def dictionary_print(self, dictionary, depth):
    
        for key in dictionary:
            string = ''
            for i in xrange(depth):
                string = string + '\t'
            if type(dictionary[key]) == dict:
                print string + key 
                self.dictionary_print(dictionary[key], depth + 1)
            else:
                print string + key + ':\t ' + dictionary[key]     
    
    def get_attributes(self):
        try:
    	    response = urllib2.urlopen(self.url)
        except:
            sys.stderr.write('Error while downloading {0}\n'.format(self.url))
    	    quit()
        try:	
            html = response.read()
            dictionary = self.get_dictionary(html)
    	    return dictionary
        except:	
            sys.stderr.write('Error while parsing {0}\n'.format(self.url))

def main():

    sil_code = sys.argv[1]
    parser = EthnologueParser(sil_code)
    dictionary = parser.get_attributes()
    parser.dictionary_print(dictionary, 0)

if __name__ == "__main__":
    main()
