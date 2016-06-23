def get_data(list_):
    keys, other_codes = get_header(list_)
    value_list = get_lines(list_, keys, other_codes)
    return keys + other_codes, value_list

def write_out_new_langs(list_, fn):

    header_list, value_lists = get_data(list_)
    fh = open(fn, 'w')
    fh.write('{}\n'.format('\t'.join(header_list)))
    fh.write('\n')
    
    for value_list in value_lists:
        fh.write(u'{}\n'.format('\t'.join(value_list)).encode('utf-8'))

def write_out_found_langs(lists, fn):
    
    list_ = [l[0] for l in lists]
    merged_to_list = [l[1] for l in lists]
    header_list, value_lists = get_data(list_)
    fh = open(fn, 'w')
    keys, other_codes = get_header(list_)
    merged_to_header = ['lang_merged_name', 'merged_by']
    fh.write('{}\n'.format('\t'.join(keys + other_codes +
                                    merged_to_header)))
    fh.write('\n')
    
    for i, value_list in enumerate(
        get_lines(list_, keys, other_codes)):
        merged_to = merged_to_list[i]
        fh.write(u'{}\n'.format('\t'.join(value_list + merged_to))
                 .encode('utf-8'))

def get_lines(list_, keys, other_codes):
    all_ = []
    for d in list_:
        if 'sil' in d and d['sil'] == set([]):
            d['sil'] = ''
        for code in d.get('other_codes', {}):
            v = d['other_codes'][code]
            if type(v) == list:
                d['other_codes'][code] = ';'.join(v)
        all_.append([d.get(k, '') for k in keys]\
                + [d.get('other_codes', {}).get(k, '') for k in other_codes])
    return all_

def get_header(list_):    
    d = list_[0]
    keys = set([])
    other_codes = set([])
    for d in list_:
        if 'other_codes' in d:
            for k in d['other_codes']:
                other_codes.add(k)
        if 'name' in d:
            keys.add('name')
        if 'sil' in d:
            keys.add('sil')
    return list(keys), list(other_codes)        

def write_out_new_altnames(new_altnames, fn):
    fh = open(fn, 'w')
    # header
    fh.write(u'{}\t{}\t{}\n'.format('altname', 'altname_of', 'merged_to')\
             .encode('utf-8'))
    fh.write('\n')
    for t in new_altnames:
        fh.write(u'{}\t{}\t{}\n'.format(t[0], t[1], t[2]).encode('utf-8'))
