""" Get fields from a list of dictionaries """
import cPickle
from sys import argv


def main():
    fields = argv[2:]
    with open(argv[1]) as f:
        data = cPickle.load(f)
    for lang in data:
        val = u''
        for fd in fields:
            d = lang.get(fd, '')
            if type(d) == set:
                for i in d:
                    #val += i[0] + '\t'
                    if type(i[1]) == tuple:
                        val += '\t'.join(str(j) for j in i[1]) + '\t'
                    else:
                        val += i[1] + '\t'
            elif type(d) == list:
                val += '\t'.join(d) + '\t'
            else:
                val += d + '\t'
            #val += '\t'
        print(u'{0}\t{1}'.format(lang['sil'], val).encode('utf8'))

if __name__ == '__main__':
    main()
