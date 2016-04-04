import logging
import pandas
import random
from collections import defaultdict, Counter
from sklearn.linear_model import LogisticRegression
from sklearn import cross_validation
from sklearn.feature_selection import SelectFromModel
import numpy
import argparse

class Classifier:

    def __init__(self, tsv, exp_count, classcount, limit, logger,
                out_fn):

        self.df = pandas.read_csv(tsv, sep='\t')
        series = ['crossval_res'] + self.df['sil'].tolist()
        self.df_res = pandas.DataFrame(index=series)
        self.df = self.df.set_index(u'sil')
        self.all_feats = self.df.drop('seed_label', axis=1)
        self.exp_count = exp_count
        self.classes = classcount
        self.limit = limit
        self.logger = logger
        self.out_fn = out_fn

    def shuffle_rows(self, df):
        index = list(df.index)
        random.shuffle(index)
        df = df.ix[index]
        df.reset_index()
        return df

    def get_train_df(self):
        
        d2 = {'-': '-', 's': 'sh', 'h': 'sh', 'v': 'vtg',
              't': 'vtg', 'g': 'vtg'}
        d3 = {'-': '-', 's': 'sh', 'h': 'sh', 'v': 'v', 't': 'tg',
              'g':'tg'}
        d4 = {'-': '-', 's': 's', 'h': 'h', 'v': 'v', 't': 'tg',
              'g':'tg'}
        g_data = self.df[self.df.seed_label == 'g'].sample(n=2)
        t_data = self.df[self.df.seed_label == 't'].sample(n=15)
        v_data = self.df[self.df.seed_label == 'v'].sample(n=15)
        h_data = self.df[self.df.seed_label == 'h'].sample(n=15)
        s_data = self.df[self.df.seed_label == 's'].sample(n=30)
        self.train_df = pandas.concat([g_data, t_data, v_data, h_data, s_data])
        if self.classes == 2:
            self.train_df.seed_label = self.train_df.seed_label.map(
                lambda x:d2[x])
            
        if self.classes == 3:
            self.train_df.seed_label = self.train_df.seed_label.map(
                lambda x:d3[x])

            
        if self.classes == 4:
            self.train_df.seed_label = self.train_df.seed_label.map(
                lambda x:d4[x])
        self.train_df = self.shuffle_rows(self.train_df)    
        self.feats = self.train_df.drop('seed_label', axis=1)
        self.labels = self.train_df.seed_label
        
    def train_crossval(self, selector=None):
        model = LogisticRegression()
        train_data = self.feats
        if selector is not None:
            train_data = selector.transform(train_data)
            logging.debug('number of feats after selection: {}'.format(
                train_data.shape[1]))
        scores = cross_validation.cross_val_score(
            model, train_data, self.labels, cv=5)
        logging.debug('crossval score:{}, average:{}'.format(
            scores, sum(scores)/5))
        return sum(scores)/5

    def get_selector(self):
        selector_model = LogisticRegression(penalty='l1')
        self.selector = SelectFromModel(selector_model)
        self.selector.fit(self.feats, self.labels)
        support = self.selector.get_support(indices=True)
        logging.debug('selected features:{}'.format(
            self.df.iloc[:, support].keys()))


    def train_label(self, crossval_res=0.0, selector=None,
                    label='exp'):
        model = LogisticRegression()
        train_data = self.feats
        all_data = self.all_feats
        if selector is not None:
            train_data = selector.transform(train_data)
            all_data = selector.transform(self.all_feats)
        model.fit(train_data, self.labels)
        self.df_res[label] = [crossval_res] +  list(model.predict(all_data))
        self.logger.debug('labelings:\n{}'.format(pandas.value_counts(
        self.df_res[label].values)))
    
    def map_values(self, d):

        d2 = defaultdict(int)
        for k in d:
            if k in ['s', 'h', 'sh']:
                d2['-'] += d[k]
            else:
                d2['+'] += d[k]
        if d2['-'] < 3:
            return 'living'
        if d2['+']  < 3:
            return 'still'
        else:
            return 'borderline'

    def train_classify(self):
        for i in range(self.exp_count):
            self.get_train_df()
            crossval_res = self.train_crossval()
            self.train_label(crossval_res=crossval_res,
                             label='exp_full_features_{0}'.format(i))
            self.get_selector()
            crossval_res = self.train_crossval(selector=self.selector)
            self.train_label(crossval_res=crossval_res, selector=self.selector,
                         label='exp_with_feature_sel_{0}'.format(i))
        self.df_res['status'] = self.df_res.apply(lambda x:Counter(x),
                                                  axis=1).apply(self.map_values)
        needed = self.df_res.iloc[0] > self.limit
        needed_list = numpy.where(needed.tolist())[0].tolist()
        self.best = self.df_res.iloc[:, needed_list]
        self.df_res['status_best'] = self.best.apply(lambda x:Counter(x), axis=1)\
                .apply(self.map_values)
        self.log_stats()
    
    def log_stats(self):
        
        crossval_res_all = pandas.to_numeric(self.df_res.iloc[0, :-2])
        crossval_res_best = pandas.to_numeric(self.best.iloc[0, :-2])
        self.logger.info('Crossvalidation results (all):\n{}'.\
                         format(crossval_res_all.describe()))
        self.logger.info(('Statuses based on all labelings:\n{}')\
                         .format(self.df_res.status.value_counts()))
        self.logger.info('Crossvalidation results (filtered by limit {1}):\n{0}'.\
                         format(crossval_res_best.describe(), self.limit))
        self.logger.info(('Statuses based on best labelings:\n{}')\
                         .format(self.df_res.status_best.value_counts()))
        self.logger.info('exporting dataframe to {}'.format(self.out_fn))
        self.df_res.to_csv(self.out_fn, sep='\t', encoding='utf-8')

      
def get_logger(fn):
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s : " +
                    "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    handler = logging.FileHandler(fn)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.INFO)
    logger.addHandler(streamhandler)
    return logger

def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', "--input_tsv", help="data file in tsv format",
                       default="preproc.tsv")
    parser.add_argument("-e", "--experiment_count", type=int,
                        help="number of experiments with random seed sets",
                        default=100)
    parser.add_argument("-c", "--class_counts", type=int, default=2,
                        choices=[1, 2, 3, 4, 5],
                        help="2 - still/living, 3 - still/vital/thriving,"+
                        "4 - still/historic/vital, thriving" +
                        "5 - still/historic/thriving/vital/global")
    parser.add_argument("-t", "--threshold", type=float, default=0.9, 
                       help="lower limit on cross-validation accuracy for counting" +
                        "statistics on 'filtered' labelings")
    parser.add_argument("-o", "--output_fn", default="labeled.tsv",
                       help="file for writing labelings")
    parser.add_argument("-l", "--log_file", default="classifier.log",
                       help="file for logging")
    return parser.parse_args()



def main():
    
    args = get_args()
    logger = get_logger(args.log_file)
    preprocessed_tsv = args.input_tsv
    exp_count = args.experiment_count
    classcount = args.class_counts
    limit = args.threshold
    out_fn = args.output_fn
    a = Classifier(preprocessed_tsv, exp_count, classcount, limit, logger,
                  out_fn)
    a.train_classify()

if __name__ == '__main__':
    main()
