import sys
import os

import subprocess as sub
import random
from maxent import MaxentModel
from math import ceil
from collections import defaultdict
from math import log


def orig_train(event_list):

    model = simple_train(event_list)
    crossval_res = tenfold(event_list)
    return model, crossval_res


def simple_train(event_list):
    m = MaxentModel()
    m.begin_add_event()
    for e in event_list:
        m.add_event(e[0], e[1])
    m.end_add_event()
    #maxent.set_verbose(1)
    m.train(30, 'lbfgs', 2)
    return m


def train_test(train, test):
    res = float(0)
    m = simple_train(train)
    for pair in test:
        feats, outcome = pair
        predicted = m.predict(feats)
        if predicted == outcome:
            res += 1
    return res/len(test)


def tenfold(event_list):

    random.shuffle(event_list)
    results = []
    tenth = int(ceil(float(len(event_list))/10))
    splitted_data = [event_list[i*tenth: (i+1)*tenth] for i in range(10)]
    for i, test in enumerate(splitted_data):
        train = event_list[:i*tenth] + event_list[(i+1)*tenth:]
        results.append(train_test(train, test))

    return sum(results)/10


def train_orig_models(c_f, v_f, h_f, m_f, contexts, seed_path):

    e_2 = [(contexts[i.strip()], 'cv') for i in c_f] +\
          [(contexts[i.strip()], 'cv') for i in v_f] +\
          [(contexts[i.strip()], 'mh') for i in h_f] +\
          [(contexts[i.strip()], 'mh') for i in m_f]

    e_3a = [(contexts[i.strip()], 'cv') for i in c_f] +\
           [(contexts[i.strip()], 'cv') for i in v_f] +\
           [(contexts[i.strip()], 'h') for i in h_f] +\
           [(contexts[i.strip()], 'm') for i in m_f]

    e_3b = [(contexts[i.strip()], 'c') for i in c_f] +\
           [(contexts[i.strip()], 'v') for i in v_f] +\
           [(contexts[i.strip()], 'mh') for i in h_f] +\
           [(contexts[i.strip()], 'mh') for i in m_f]

    e_4 = [(contexts[i.strip()], 'c') for i in c_f] +\
           [(contexts[i.strip()], 'v') for i in v_f] +\
           [(contexts[i.strip()], 'h') for i in h_f] +\
           [(contexts[i.strip()], 'm') for i in m_f]
    
    random.shuffle(e_2)
    random.shuffle(e_3a)
    random.shuffle(e_3b)
    random.shuffle(e_4)

    m_2, r_2 = orig_train(e_2)
    m_3a, r_3a = orig_train(e_3a)
    m_3b, r_3b = orig_train(e_3b)
    m_4, r_4 = orig_train(e_4)

    for i in 'm_2', 'm_3a', 'm_3b', 'm_4':
        eval(i).save('{0}/models/{1}_class'.format(seed_path, i[2:]))

    return m_2, m_3a, m_3b, m_4, e_2, e_3a, e_3b, e_4, r_2, r_3a, r_3b, r_4


def get_top_feats(saved_model_file):

    top_feats_set = set([])
    top_feats = []
    p = sub.Popen(['python', 'maxentRig.py', '1000'],stdout=sub.PIPE,
                  stderr=sub.PIPE, stdin=sub.PIPE)
    stdoutdata, stderr = p.communicate(input=open(saved_model_file).read())
    for l in stdoutdata.split('\n'):
        f = l.split('\t')[0]
        if f not in top_feats_set:
            top_feats.append(f)
            top_feats_set.add(f)
    return top_feats


def label(m, langs, features, path):

    a = open(path, 'w')
    for l in langs:
        context = features[l]
        pred = m.predict(context)
        a.write('{0}\t{1}\n'.format(l, pred))
    a.close()


def train_filtered_models(needed_feats, events):

    filtered_events = []
    for e in events:
        c, o = e
        filtered_c = []
        for pair in c:
            if pair[0] in needed_feats:
                filtered_c.append(pair)
        if len(filtered_c) > 0:
            filtered_events.append((filtered_c, o))
    return orig_train(filtered_events)

def get_features(ff):

    features = defaultdict(list)
    feat_list = ff[0].strip().split('\t')
    name_dict = dict([(i-1, n) for i, n in enumerate(feat_list)])
    for l in ff[1:]:
        name, feats = l.strip().split('\t')[0], l.strip().split('\t')[1:]
        for i, f in enumerate(feats):
            n = name_dict[i]
            if f == 'n/a':
                continue
            features[name].append((n, f))
            features[name].append((name_dict[i], float(f)))
    return features


def rounde(r):

    r = r * 100
    parts = str(r).split('.')
    if len(parts) > 1:
        egesz, resz = parts
        resz = resz[:4]
        egesz = '{}.'.format(egesz)
    else:
        egesz = r
        resz = ''
    return egesz, resz


def printout(res, seed_path):

    a = open('{}/results'.format(seed_path), 'w')
    for i in '2','3a','3b','4':
        r = res['e_{0}'.format(i)]['all'][0]
        egesz, resz = rounde(r)
        a.write('{0}_class\tall\t{1}{2}\n'.format(i, egesz, resz))
        for j in '6', '8', '10', '12', '14', '16', '18':
            max_res = max(res['e_{0}'.format(i)][j])
            egesz, resz = rounde(max_res)
            a.write('{0}_class\t{1}\t{2}{3}\n'.format(i, j, egesz, resz))
    a.close()


def write_items(f_list, path):

    a = open(path, 'w')
    for f in f_list:
        a.write('{0}\n'.format(f))
    a.close()


def process_seed(c, v, h, m, ff, seed_path):

    for p in '{0}'.format(seed_path), '{0}/labelings'.format(seed_path),\
    '{0}/models'.format(seed_path), '{0}/selected_feats'.format(seed_path),\
                '{0}/seed'.format(seed_path):
        if not os.path.exists(p):
            os.makedirs(p)
    for i in 'c', 'v', 'h', 'm':
        write_items(eval(i), '{0}/seed/{1}'.format(seed_path, i))
    features = get_features(ff)
    langs = [l.strip().split('\t')[0] for l in ff]
    res = defaultdict(lambda: defaultdict(list))

    m_2, m_3a, m_3b, m_4, e_2 ,e_3a, e_3b, e_4, r_2, r_3a, r_3b, r_4 = \
    train_orig_models(c, v, h, m, features, seed_path)

    for t in '2', '3a', '3b', '4':
        res['e_{0}'.format(t)]['all'].append(eval('r_{0}'.format(t)))
    for m in 'm_2', 'm_3a', 'm_3b', 'm_4':
        label(eval(m), langs, features, '{0}/labelings/{1}_class'
              .format(seed_path, m[2:]))
    fs_2 = get_top_feats('{0}/models/2_class'.format(seed_path))
    fs_3a = get_top_feats('{0}/models/3a_class'.format(seed_path))
    fs_3b = get_top_feats('{0}/models/3b_class'.format(seed_path))
    fs_4 = get_top_feats('{0}/models/4_class'.format(seed_path))

    for i in 'fs_2', 'fs_3a', 'fs_3b', 'fs_4':
        write_items(eval(i)[:18], '{0}/selected_feats/{1}_class_sel'
                    .format(seed_path, i[3:]))

    for task_name in ['e_2', 'e_3a', 'e_3b', 'e_4']:
        for count_name in ['6', '8', '10', '12', '14', '16', '18']:
            for fset_name in ['fs_2', 'fs_3a', 'fs_3b', 'fs_4']:
                m, r = train_filtered_models(set(eval(fset_name)
                                                 [:eval(count_name)]),
                                              eval(task_name))

                label(m, langs, features,
                      '{0}/labelings/{1}_class_{2}_from_{3}_sel'.format(
                        seed_path, task_name[2:], count_name, fset_name[3:]))
                res[task_name][count_name].append(r)
    printout(res, seed_path)


def random_select_seed_2(c_f, v_f, h_f, m_f):

    random.shuffle(c_f)
    random.shuffle(v_f)
    random.shuffle(h_f)
    random.shuffle(m_f)
    c = sorted(c_f[:10])
    c_2 = sorted(c_f[11:])
    h = sorted(h_f[:9])
    h_2 = sorted(h_f[10:])
    v = sorted(v_f[:40])
    v_2 = sorted(v_f[40:])
    m = sorted(m_f[:75])
    m_2 = sorted(m_f[76:151])

    return c, v, h, m, c_2, v_2, h_2, m_2


def exp(feature_file, c_f, v_f, h_f, m_f, index, path):

    seed_path_1 = '{0}/{1}'.format(path, index)
    seed_path_2 = '{0}/{1}_2'.format(path, index)
    c, v, h, m, c_2, v_2, h_2, m_2 = random_select_seed_2(c_f, v_f, h_f, m_f)
    process_seed(c, v, h, m, feature_file, seed_path_1)
    process_seed(c_2, v_2, h_2, m_2, feature_file, seed_path_2)


def main():

    c_f = [l .strip() for l in open(sys.argv[1]).readlines()]
    v_f = [l .strip() for l in open(sys.argv[2]).readlines()]
    h_f = [l .strip() for l in open(sys.argv[3]).readlines()]
    m_f = [l .strip() for l in open(sys.argv[4]).readlines()]
    feature_file = open(sys.argv[5]).readlines()
    path = sys.argv[6]
    exp_tag = sys.argv[7]
    sys.stderr.write('{0}\n'.format(exp_tag))
    exp(feature_file, c_f, v_f, h_f, m_f, exp_tag, path)

if __name__ == "__main__":
    main()
