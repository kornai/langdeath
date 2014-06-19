from sys import stdin, argv, stderr
import re
import math

speaker_num_map = {
    'a few elderly speakers': 5,
    'hundreds': 400,
    'very small group': 20,
    'just a few elders': 5,
    'unclear': 30,
    '97000 speakers in india. 100190 speakers worldwide.': 100190,
    'not known': 30,
    'approx. 30': 30,
    'only a handful of speakers': 5,
    '0 extinct?': 0,
    'extinct (possibly)': 0,
    'approximately 12000': 12000,
    'extinct. unlikely any speakers remain': 0,
    'no fully fluent speakers remaining': 0,
    'unknown may be dormant': 0,
    'the last fluent speakers passed away in 2004.': 0,
    '6000 4000': 4900,
    'a few elders': 5,
    '18000 12000': 14700,
    '42000 30000': 35500,
    'unknown; possibly 0': 0,
    'approx 9500-10500 speakers in all countries': 10000,
    '230 in paraguay unknown in argentina': 300,
    'possibly extinct': 0,
    'fewer than 20': 5,
    'a few elderly speakers.': 5,
    'no known l1 speakers in italy': 0,
    '"unlikely any speakers remain"': 0,
    '"only a few elderly speakers"': 5,
    'approx. 50': 50,
    'none (second language only)': 0,
    '1300 in burkina faso': 1300,
    'up to 340': 340,
    'nearly extinct': 30,
    'a few elderly speakers': 5,
    'last known speaker passed away in 2003': 0,
    '90 households': 200,
    '42100.': 42100,
    '"practically extinct" (omo-murle dialect only)': 0,
    'about 1000 quite possibly less': 1000,
    '15? or extinct?': 10,
    'fewer than 100': 60,
    'about 20': 20,
    '"extinct. unlikely any speakers remain"': 0,
    'some in tanzania': 30,
    '24 nearly extinct': 24,
    'fewer than 100 families': 200,
    'a few elderly speakers': 5,
    '45 speakers and semispeakers?': 30,
    'nearly extinct': 5,
    'possibly 0': 0,
    'no known fluent speakers': 0,
    '200000 in namibia (2006). population total all countries: 251100': 251100,
    'not available': 30,
    '47800 in greenland (1995 m. krauss). 3000 east greenlandic 44000 west greenlandic 800 north greenlandic. population total all countries: 57800': 57800,
    '5800. 725 monolinguals (1990 census). ethnic population: 6300': 6300,
}
zeros = set([
    'no known l1 speakers',
    'no known speakers',
    'no known speakers.',
    'extinct',
    'extinct?',
    '"no remaining speakers"',
    'likely dormant',
    'unlikely any speakers remain',
    '0 extinct',
])
unknown = set([
    'no estimate available',
    'number of speakers unknown',
    'unknown',
    '?',
])
few = set([
    'few',
    'few?',
    'a few',
    'very few',
    'a handful',
    'some',
])
interval_re = re.compile(ur'~?(\d+)\s*[-\u2013]\s*(\d+)', re.UNICODE)
date_after_re = re.compile(r'^(\d+)\s*\(', re.UNICODE)
num_re = re.compile(r'^~?\s*(\d+)\??\+?$', re.UNICODE)


def get_average(fields):
    prod = 1.0
    for fd in fields:
        num = normalize_num(fd.strip().lower())
        if num == 0:
            num = 1
        prod *= num
    return nthroot(len(fields), prod, 0.1)


from decimal import getcontext


def nthroot(n, A, precision):
    getcontext().prec = precision
    x_0 = A / n  # step 1: make a while guess.
    x_1 = 1     # need it to exist before step 2
    while True:
        # step 2:
        x_0, x_1 = x_1, (1 / n)*((n - 1)*x_0 + (A / (x_0 ** (n - 1))))
        if x_0 == x_1:
            return x_1


def normalize_num(num):
    if num_re.match(num):
        return int(num_re.match(num).group(1))
    elif num.strip().lower() in zeros:
        return 0
    elif num.strip().lower() in unknown:
        return 30
    elif num.strip().lower() in few:
        return 30
    elif interval_re.match(num):
        m = interval_re.match(num)
        return geometric_mean(int(m.group(1)), int(m.group(2)))
    elif date_after_re.match(num):
        return int(date_after_re.match(num).group(1))
    elif 'few dozen' in num:
        return 30
    elif 'few hundred' in num:
        return 300
    elif 'few thousand' in num:
        return 3000
    elif 'several dozen' in num:
        return 60
    elif 'several hundred' in num:
        return 600
    elif 'several thousand' in num:
        return 6000
    elif num in speaker_num_map:
        return speaker_num_map[num]
    else:
        stderr.write('Unmatched {0}\n'.format(num.encode('utf8')))


def geometric_mean(n1, n2):
    return math.sqrt(n1 * n2)


def main():
    if len(argv) > 1:
        cut = int(argv[1])
    else:
        cut = 1
    for l in stdin:
        fd = l.decode('utf8').strip().split('\t')
        if len(fd) <= cut:
            #print(sil + '\t')
            continue
        avg = get_average(fd[cut:])
        print('{0}\t{1}'.format('\t'.join(i.encode('utf8') for i in fd[:cut]), avg))

if __name__ == '__main__':
    main()
