from sys import stdin, argv, stderr

category_map = {
    'At risk': 6,
    'Vulnerable': 5,
    'Threatened': 4,
    'Endangered': 3,
    'Severely endangered': 2,
    'Critically endangered': 1,
    'Dormant': 0,
    'Awakening': 0,
}


def main():
    if len(argv) > 1:
        cut = int(argv[1])
    else:
        cut = 1
    for l in stdin:
        fd = l.strip().split('\t')
        sil = fd[0]
        if len(fd) <= cut:
            print(sil + '\t')
            continue
        avg = 0
        not_zero = 0
        categories = list()
        for i in range(cut, len(fd), 2):
            categories.append((category_map[fd[i]], int(fd[i + 1])))
            avg += int(fd[i + 1])
            if not int(fd[i + 1]) == 0:
                not_zero += 1
        if not_zero == 0:
            stderr.write('Sum of weights is zero in line: ' + l)
            print(sil + '\t' + str(sum(i[0] for i in categories) / float(len(categories))))
            continue
        avg = float(avg) / not_zero
        score = 0.0
        weights = 0.0
        for cat, weight in categories:
            if weight == 0:
                weights += avg
                score += cat * avg
            else:
                weights += weight
                score += cat * weight
        print(sil + '\t' + str(score / weights))

if __name__ == '__main__':
    main()
