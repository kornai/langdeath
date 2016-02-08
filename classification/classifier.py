from sklearn.linear_model import LogisticRegression
from sklearn import cross_validation
from sklearn.feature_selection import SelectFromModel
from math import log
import pandas
import sqlite3
import sys

class Classifier:

    def __init__(self, sqlite_fn):
        self.df = self.get_df(sqlite_fn)
        self.selectors = {}
    
    def get_df(self, sqlite_fn):
        conk = sqlite3.connect(sqlite_fn)
        self.df = pandas.read_sql("SELECT * FROM dld_language", conk)
        self.df = self.df.set_index([u'sil'])
    
    def preproc_data(self, train_data_dir, feat_data_dir):
        self.numerical_preproc(feat_data_dir)
        self.add_labels(train_data_dir)

    def add_labels(self, train_data_dir):
        
        t_set = [l.strip() for l in open('{}/t'.format(train_data_dir))]
        v_set = [l.strip() for l in open('{}/v'.format(train_data_dir))]
        h_set = [l.strip() for l in open('{}/h'.format(train_data_dir))]
        s_set = [l.strip() for l in open('{}/s'.format(train_data_dir))]
        self.df['seed_label'] = self.df.index.map(lambda x:
                                                      's' if x in s_set
                                                       else 'h' if x in h_set
                                                       else 'v' if x in v_set 
                                                       else 't' if x in t_set
                                                       else '-')               
        self.df['seed_label_2class'] = self.df['seed_label'].map(lambda x: 
                                                      'sh' if x == 'm' or x == 'h'
                                                       else 'tv' if x == 't' or x == 'v'
                                                       else '-')     

    def numerical_preproc(self, feat_data_dir):
        self.needed = [l.strip() for l in open(
            '{}/needed_feats'.format(feat_data_dir))]
        log_needed = [l.strip() for l in open(
            '{}/log_needed'.format(feat_data_dir))]
        bool_needed = [l.strip() for l in open(
            '{}/bool_needed'.format(feat_data_dir))]
        self.df[bool_needed] = self.df[bool_needed].fillna(0)
        self.df[log_needed] = self.df[log_needed].fillna(0)
        self.df[log_needed] = self.df[log_needed].applymap(lambda x: log(x+1))
   
    def get_train_df(self):
        self.train_df = self.df.loc[self.df[
            'seed_label']=='t'].sample(n=15)
        self.train_df = self.train_df.append(
            self.df.loc[self.df['seed_label']=='v'].sample(n=30))
        self.train_df = self.train_df.append(
            self.df.loc[self.df['seed_label']=='h'].sample(n=10))
        self.train_df = self.train_df.append(
            self.df.loc[self.df['seed_label']=='s'].sample(n=50))
        self.train_df[self.needed + ['seed_label']]

    def train_crossval(self, selector=None):
        model = LogisticRegression()
        train_data = self.train_df[self.needed]
        if selector is not None:
            train_data = selector.transform(train_data)
        scores = cross_validation.cross_val_score(model,train_data,
                                                  self.train_df['seed_label'], cv=5)
        print scores, sum(scores)/5
    
    def get_selector(self, threshold=1):
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
        model.fit(train_data, label_data)
        self.df[label] = model.predict(label_data)

    def train_classify(self, train_data_dir, feat_data_dir):
        self.preproc_data(train_data_dir, feat_data_dir)
        self.get_train_df()
        self.train_crossval()
        self.train_label(label='exp_full_features')
        self.get_selector()
        self.train_crossval(selector=self.selector)
        self.train_label(selector=self.selector,
                         label='exp_with_feature_sel')

def main():

    fn = sys.argv[1]
    train_data_dir = '/home/pajkossy/Proj/langdeath/classification/seed_data/'
    feat_data_dir = '/home/pajkossy/Proj/langdeath/classification/feat_data/'
    a = Classifier(fn)
    a.train_classify(train_data_dir, feat_data_dir)

if __name__ == '__main__':
    main()
