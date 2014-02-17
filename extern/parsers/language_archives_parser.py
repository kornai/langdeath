import sys
import urllib2

from base_parsers import OnlineParser

def parse_table(table):

    dictionary = {} 
    rows = table.split('<li>')[1:]
    dictionary['All'] = len(rows)
    online_count = 0
    for row in rows:
        if '<span class="online_indicator">' in row:
            online_count += 1
    dictionary['Online'] = online_count

    return dictionary


def parse_table_list(table_list):

    dictionary = {}
    for table in table_list:
        name = table.split('</h2>')[0]
        info_dict = parse_table(table.split('<ol>')[1].split('</ol>')[0])
        dictionary[name] = info_dict 
    
    return dictionary


def get_dictionary(string):
  
    dictionary = {}
    name_wrapped = string.split('about the')[1].split('</title>')[0]
    if 'language'in name_wrapped:
        name = name_wrapped.split('language')[0].strip(' ')
    else:
        name = name_wrapped
    code = string.split('<p>ISO 639-3:')[1].split('>')[1].split('</a')[0]\
	    .strip()
    dictionary_item_inputs = string.split('<h2>')[1:] 
    dictionary = parse_table_list(dictionary_item_inputs)
    dictionary['Name'] = name
    dictionary['Code'] = code
    
    return dictionary


def dictionary_print(dictionary):

    lista = ['Name', 'Code', 'Primary texts', 'Lexical resources',\
	    'Language descriptions', 'Other resources about the language',\
	    'Other resources in the language'] 

    string = '{0}\t{1}'.format(dictionary['Name'], dictionary['Code'])
    for item in lista[2:]:
        if item in dictionary:
	    string += "\t{0}\t{1}".format(dictionary[item]['All'],\
		    dictionary[item]['Online'])
        else:
            string +=  '\t{0}\t{0}'.format(0)
    print string
  
def get_lang_archive(sil_code):
    
    url = 'http://www.language-archives.org/language/{0}'.format(sil_code)
    parser = OnlineParser()
    try:
	response = urllib2.urlopen(url)
    except:
        sys.stderr.write('Error while downloading {0}\n'.format(url))
	quit()
    try:	
        html = response.read()
        dictionary = get_dictionary(html)
        dictionary_print(dictionary)
    except:	
        sys.stderr.write('Error while parsing {0}\n'.format(url))

def main():

    sil_code = sys.argv[1]
    get_lang_archive(sil_code)

if __name__ == "__main__":
    main()
