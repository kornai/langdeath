import sys



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


def get_dictionary(file_handler):
  
    string = file_handler.read()
    dictionary = {}
    name_wrapped = string.split('about the')[1].split('</title>')[0]
    if 'language'in name_wrapped:
        name = name_wrapped.split('language')[0]
    else:
        name = name_wrapped
    code = string.split('<p>ISO 639-3:')[1].split('>')[1].split('</a')[0].strip()
    dictionary_item_inputs = string.split('<h2>')[1:] 
    dictionary = parse_table_list(dictionary_item_inputs)
    dictionary['Name'] = name
    dictionary['Code'] = code
    
    return dictionary


def dictionary_print(dictionary):

#    print 'Name\tCode\tPrimary_texts_All\tPrimary_texts_Online\tLexical_Resources_All\tLexical_Resources_Online\tLanguage_descriptions_All\tLanguage_descriptions_Online\tOther_resources_about_the_language_All\tOther_resources_about_the_language_Online\tOther_resources_in_the_language_All\tOther_resources_in_the_language_Online'
     
    lista = ['Name', 'Code', 'Primary texts', 'Lexical resources', 'Language descriptions', 'Other resources about the language', 'Other resources in the language'] 

    string = '{0}\t{1}'.format(dictionary['Name'], dictionary['Code'])
    for item in lista[2:]:
        if item in dictionary:
            string = string + '\t' + str(dictionary[item]['All']) + '\t' + str(dictionary[item]['Online'])
        else:
            string = string + '\t' + str(0) + '\t' + str(0)
    print string
  
    
def main():

    dictionary = get_dictionary(open(sys.argv[1]))
    dictionary_print(dictionary)

main()
