import sys
import logging
from math import log
import pandas
import sqlite3
from sklearn.linear_model import LogisticRegression
from sklearn import cross_validation
from sklearn.feature_selection import SelectFromModel

class Classifier:

    def __init__(self, sqlite_fn, train_dir, feat_dir):
        self.get_df(sqlite_fn)
        self.get_seed_sets(train_dir)
        self.get_feat_set(feat_dir)
        self.preproc_data(train_dir, feat_dir)

    def get_seed_sets(self, train_dir):

        self.t_set = [l.strip() for l in open('{}/t'.format(train_dir))]
        self.v_set = [l.strip() for l in open('{}/v'.format(train_dir))]
        self.h_set = [l.strip() for l in open('{}/h'.format(train_dir))]
        self.s_set = [l.strip() for l in open('{}/s'.format(train_dir))]
    
    def get_feat_set(self, feat_dir):

        self.needed = [l.strip() for l in open(
            '{}/needed_feats'.format(feat_dir))]
        self.log_needed = [l.strip() for l in open(
            '{}/log_needed'.format(feat_dir))]
        self.bool_needed = [l.strip() for l in open(
            '{}/bool_needed'.format(feat_dir))]

    def get_df(self, sqlite_fn):
        conk = sqlite3.connect(sqlite_fn)
        self.df = pandas.read_sql("SELECT * FROM dld_language", conk)
        self.df = self.df.set_index([u'sil'])


    def preproc_data(self, train_dir, feat_dir):
        self.numerical_preproc(feat_dir)
        self.add_labels(train_dir)

    def add_labels(self, train_data_dir):
        
        self.df['seed_label'] = self.df.index.map(lambda x:
                                                  's' if x in self.s_set
                                                  else 'h' if x in self.h_set
                                                  else 'v' if x in self.v_set
                                                  else 't' if x in self.t_set
                                                  else '-')
        self.df['seed_label_2class'] = self.df['seed_label']\
                .map(lambda x:
                     'sh' if x == 'm' or x == 'h'
                     else 'tv' if x == 't' or x == 'v'
                     else '-')     

    def numerical_preproc(self, feat_data_dir):
        
        self.df[self.bool_needed] = self.df[self.bool_needed].fillna(0)
        self.df[self.log_needed] = self.df[self.log_needed].fillna(0)
        self.df[self.log_needed] = self.df[self.log_needed].applymap(
            lambda x: log(x+1))

    def get_train_df(self):

        t_data = self.df.loc[self.df['seed_label']=='t'].sample(n=15)
        v_data = self.df.loc[self.df['seed_label']=='v'].sample(n=30)
        h_data = self.df.loc[self.df['seed_label']=='h'].sample(n=10)
        s_data = self.df.loc[self.df['seed_label']=='s'].sample(n=50)
        self.train_df = pandas.concat([t_data, v_data, h_data, s_data])

    def train_crossval(self, selector=None):
        model = LogisticRegression()
        train_data = self.train_df[self.needed]
        if selector is not None:
            train_data = selector.transform(train_data)
            logging.info('number of feats after selection: {}'.format(
                train_data.shape[1]))
        scores = cross_validation.cross_val_score(
            model, train_data, self.train_df['seed_label'], cv=5)
        logging.info('crossval score:{}, average:{}'.format(
            scores, sum(scores)/5))

    def get_selector(self, threshold=1.5):
        model = LogisticRegression()
        self.selector = SelectFromModel(model, threshold=threshold)
        self.selector.fit(self.df[self.needed], self.df['seed_label'])

    def train_label(self, selector=None, label='exp'):
        model = LogisticRegression()
        train_data = self.train_df[self.needed]
        label_data = self.df[self.needed]
        if selector is not None:
            train_data = selector.transform(train_data)
            label_data = selector.transform(label_data)
        model.fit(train_data, self.train_df['seed_label'])
        self.df[label] = model.predict(label_data)
        logging.info('labelings:\n{}'.format(pandas.value_counts(
        self.df[label].values)))

    def train_classify(self, out_fn):
        self.get_train_df()
        self.train_crossval()
        self.train_label(label='exp_full_features')
        self.get_selector()
        self.train_crossval(selector=self.selector)
        self.train_label(selector=self.selector,
                         label='exp_with_feature_sel')
        if out_fn != None:
            logging.info('exporting dataframe to {}'.format(out_fn))  
            self.df.to_csv(out_fn, sep='\t', encoding='utf-8')

def main():
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    fn = sys.argv[1]
    train_data_dir = '/home/pajkossy/Proj/langdeath/classification/seed_data/'
    feat_data_dir = '/home/pajkossy/Proj/langdeath/classification/feat_data/'
    out_fn = None
    if len(sys.argv) > 2:
        out_fn = sys.argv[2]
    a = Classifier(fn, train_data_dir, feat_data_dir)
    a.train_classify(out_fn)

if __name__ == '__main__':
    main()
