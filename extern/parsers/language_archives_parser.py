import sys
import urllib2

from base_parsers import OnlineParser

class LanguageArchivesParser(OnlineParser):

    def __init__(self, sil_code):
	self.sil_code = sil_code
	self.url = 'http://www.language-archives.org/language/{0}'\
		.format(self.sil_code) 
	self.dictionary = {}	

    def parse_table(self, table):
    
        rows = table.split('<li>')[1:]
        self.dictionary['All'] = len(rows)
        online_count = 0
        for row in rows:
            if '<span class="online_indicator">' in row:
                online_count += 1
        self.dictionary['Online'] = online_count
    
    def parse_table_list(self, table_list):
    
        for table in table_list:
            name = table.split('</h2>')[0]
            info_dict = self.parse_table(table.split('<ol>')[1]\
		    .split('</ol>')[0])
            self.dictionary[name] = info_dict 
    
    def fill_dictionary(self, string):
      
        name_wrapped = string.split('about the')[1].split('</title>')[0]
        if 'language'in name_wrapped:
            name = name_wrapped.split('language')[0].strip(' ')
        else:
            name = name_wrapped
        code = string.split('<p>ISO 639-3:')[1].split('>')[1].split('</a')[0]\
    	    .strip()
        dictionary_item_inputs = string.split('<h2>')[1:] 
        self.parse_table_list(dictionary_item_inputs)
        self.dictionary['Name'] = name
        self.dictionary['Code'] = code
        
    def get_attributes(self):
        
        try:
    	    response = urllib2.urlopen(self.url)
        except:
            sys.stderr.write('Error while downloading {0}\n'.format(self.url))
    	    quit()
        try: 	
            html = response.read()
            self.fill_dictionary(html)
    	    return self.dictionary
	except:	
            sys.stderr.write('Error while parsing {0}\n'.format(self.url))

def main():

    sil_code = sys.argv[1]
    parser = LanguageArchivesParser(sil_code)
    print repr(parser.get_attributes())

if __name__ == "__main__":
    main()
