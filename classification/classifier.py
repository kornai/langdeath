import sys
import logging
import pandas
from sklearn.linear_model import LogisticRegression
from sklearn import cross_validation
from sklearn.feature_selection import SelectFromModel

class Classifier:

    def __init__(self, tsv, exp_count, threshold):

        self.df = pandas.read_csv(tsv, sep='\t')
        self.df_res = self.df[['sil']].set_index('sil')
        self.df = self.df.set_index(u'sil')
        self.all_feats = self.df.drop('seed_label', axis=1)
        self.exp_count = exp_count
        self.thr = threshold

    def get_train_df(self):

        t_data = self.df[self.df.seed_label == 't'].sample(n=15)
        v_data = self.df[self.df.seed_label == 'v'].sample(n=40)
        h_data = self.df[self.df.seed_label == 'h'].sample(n=15)
        s_data = self.df[self.df.seed_label == 's'].sample(n=80)
        
        self.train_df = pandas.concat([t_data, v_data, h_data, s_data])
        self.feats = self.train_df.drop('seed_label', axis=1)
        self.labels = self.train_df.seed_label
        
    def train_crossval(self, selector=None):
        model = LogisticRegression()
        train_data = self.feats
        if selector is not None:
            train_data = selector.transform(train_data)
            logging.info('number of feats after selection: {}'.format(
                train_data.shape[1]))
        scores = cross_validation.cross_val_score(
            model, train_data, self.labels, cv=5)
        logging.info('crossval score:{}, average:{}'.format(
            scores, sum(scores)/5))

    def get_selector(self, threshold=2):
        model = LogisticRegression()
        self.selector = SelectFromModel(model, threshold=threshold)
        self.selector.fit(self.feats, self.labels)
        support = self.selector.get_support(indices=True)
        print self.df.iloc[:, support].keys()


    def train_label(self, selector=None, label='exp'):
        model = LogisticRegression()
        train_data = self.feats
        all_data = self.all_feats
        if selector is not None:
            train_data = selector.transform(train_data)
            all_data = selector.transform(self.all_feats)
        model.fit(train_data, self.labels)
        self.df_res[label] = model.predict(all_data)
        logging.info('labelings:\n{}'.format(pandas.value_counts(
        self.df_res[label].values)))

    def train_classify(self, out_fn):
        for i in range(self.exp_count):
            self.get_train_df()
            self.train_crossval()
            self.train_label(label='exp_full_features_{0}'.format(i))
            self.get_selector(threshold=self.thr)
            self.train_crossval(selector=self.selector)
            self.train_label(selector=self.selector,
                         label='exp_with_feature_sel_{0}'.format(i))
        if out_fn != None:
            logging.info('exporting dataframe to {}'.format(out_fn))  
            self.df_res.to_csv(out_fn, sep='\t', encoding='utf-8')

def main():
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    preprocessed_tsv = sys.argv[1]
    exp_count = int(sys.argv[2])
    threshold = float(sys.argv[3])
    out_fn = None
    if len(sys.argv) > 4:
        out_fn = sys.argv[4]
    a = Classifier(preprocessed_tsv, exp_count, threshold)
    a.train_classify(out_fn)

if __name__ == '__main__':
    main()
