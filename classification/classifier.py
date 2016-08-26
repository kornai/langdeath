import logging
import pandas
import random
from collections import defaultdict, Counter
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectFromModel
import numpy
import argparse
from sklearn.cross_validation import cross_val_score, cross_val_predict
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline

class Classifier:

    def __init__(self, tsv, exp_count, classcount, limit, logger,
                out_template, status_use):

        self.df = pandas.read_csv(tsv, sep='\t')
        series = self.df['integrated_code'].tolist()

        self.df_res          = pandas.DataFrame(index=series)
        self.df_res_crossval = pandas.Series()
        self.df_res_dprobas  = defaultdict(lambda: pandas.DataFrame(index=series))

        self.df = self.df.set_index(u'integrated_code')
        if not status_use:
            self.df = self.df.drop('eth_status', axis=1)\
                    .drop('endangered_aggregated_status', axis=1)
            logging.info('Dropping status features')
        self.all_feats = self.df.drop('seed_label', axis=1)
        self.exp_count = exp_count
        self.classes = classcount
        self.limit = limit
        self.logger = logger
        self.out_template = out_template
        self.status_use = status_use


    def shuffle_rows(self, df):
        index = list(df.index)
        random.shuffle(index)
        df = df.ix[index]
        df.reset_index()
        return df

    def get_train_df(self):
        d2 = {'-': '-',
              's': 'sh',
              'h': 'sh',
              'v': 'vtg',
              't': 'vtg',
              'g': 'vtg'}

        d3 = {'-': '-',
              's': 'sh',
              'h': 'sh',
              'v': 'v',
              't': 'tg',
              'g': 'tg'}

        d4 = {'-': '-',
              's': 's',
              'h': 'h',
              'v': 'v',
              't': 'tg',
              'g': 'tg'}

        g_data = self.df[self.df.seed_label == 'g'].sample(n=4)
        t_data = self.df[self.df.seed_label == 't'].sample(n=20)
        v_data = self.df[self.df.seed_label == 'v'].sample(n=20)
        h_data = self.df[self.df.seed_label == 'h'].sample(n=20)
        s_data = self.df[self.df.seed_label == 's'].sample(n=80)

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

        # if self.classes == 5 no grouping is necessary

        self.train_df = self.shuffle_rows(self.train_df)    
        self.feats = self.train_df.drop('seed_label', axis=1)
        self.labels = self.train_df.seed_label
        
    def train_crossval(self):
        scores = cross_val_score(self.pipeline, self.feats, self.labels, cv=5)
        predicted = cross_val_predict(self.pipeline, self.feats, self.labels, cv=5)
        error_indices = (predicted != self.labels).as_matrix()
        debug_df = pandas.DataFrame({'gold': self.labels[error_indices],
                                         'predicted': predicted[error_indices]})
        logging.debug('crossval score - average:{}'.format(
            sum(scores)/5))
        if not debug_df.empty:
            logging.debug('errors in classification:\n{}'.format(debug_df))
        return sum(scores)/5


    def get_pipeline(self):
        selector_model = LogisticRegression(penalty='l1', C=0.1)
        selector = SelectFromModel(selector_model)
        self.pipeline = Pipeline([('selector', selector),
            ('model', LogisticRegression())])


    def train_label(self, crossval_res=0.0, label='exp'):
        train_data = self.feats
        all_data = self.all_feats
        self.pipeline.fit(train_data, self.labels)
        support = self.pipeline.named_steps['selector']\
                .get_support(indices=True)
        logging.debug('selected features:{} {}'.format(len(support),
            self.df.iloc[:, support].keys()))
        probas = self.pipeline.predict_proba(all_data)
        categories = sorted(set(self.labels))

        self.df_res[label] = list(self.pipeline.predict(all_data))
        self.df_res_crossval[label] = crossval_res

        for index, category in enumerate(categories):
            self.df_res_dprobas[category][label] = probas[:, index]

        self.logger.debug('labelings:\n{}'.format(pandas.value_counts(
            self.df_res[label])))
    
    def map_borderline_values(self, d):
        d2 = defaultdict(int)

        for k in d:
            if k in ['s', 'h', 'sh']:
                d2['-'] += d[k]
            else:
                d2['+'] += d[k]

        all_ = d2['+'] + d2['-']        

        if d2['+'] > 0.95 * all_:
            return 'living'
        if d2['-']  > 0.95 * all_:
            return 'dead'
        else:
            return 'borderline'

    def map_stable_values(self, d):
        sort_values = sorted(d.iteritems(), key=lambda x:x[1], reverse=True)
        if sort_values[0][1] > sum(d.itervalues()) * 0.95:
            return sort_values[0][0]
        else:
            return '-' 

    def train_classify(self):
        for i in range(1, self.exp_count+1):
            self.get_train_df()
            self.get_pipeline()
            crossval_res = self.train_crossval()
            self.train_label(crossval_res=crossval_res,
                    label='exp_with_feature_sel_{0}'.format(i))

        status_series = self.df_res.apply(lambda x:Counter(x),
                                                  axis=1).apply(self.map_borderline_values)
        stable_series = self.df_res.apply(lambda x:Counter(x),
                                                  axis=1).apply(self.map_stable_values)
        self.df_res['status'] = status_series
        self.df_res['stable'] = stable_series

        needed = self.df_res_crossval > self.limit
        needed_list = numpy.where(needed.tolist())[0].tolist()

        if needed_list:
            self.best          = self.df_res.iloc[:, needed_list]
            self.best_crossval = self.df_res_crossval.iloc[needed_list]

            status_best_series = self.best.apply(lambda x:Counter(x), axis=1)\
                    .apply(self.map_borderline_values)
        
            stable_best_series = self.best.apply(lambda x:Counter(x), axis=1)\
                    .apply(self.map_stable_values)

            self.df_res['status_best'] = status_best_series
            self.df_res['stable_best'] = stable_best_series
        else:
          self.logger.warn("No experiment had crossvalidation accuracy higher " +\
                           "than the minimum threshold of %i" % (self.limit))

        self.log_stats()
    
    def log_stats(self):
        crossval_res_all = pandas.to_numeric(self.df_res_crossval)

        self.logger.debug('Crossvalidation results (all):\n{}'.\
                         format(crossval_res_all.describe()))
        self.logger.debug(('Statuses based on all labelings:\n{}')\
                          .format(self.df_res.status[1:].value_counts()))
        self.logger.debug(('Stable languages based on all labelings:\n{}')\
                          .format(self.df_res.stable[1:].value_counts()))

        if hasattr(self, "best"):
            crossval_res_best = pandas.to_numeric(self.best_crossval)

            self.logger.info('Crossvalidation results (filtered by limit {1}):\n{0}'.\
                             format(crossval_res_best.describe(), self.limit))

            self.logger.info(('Statuses based on labelings ' +
                              '(where crossvalidation exceeds limit):\n{}')\
                             .format(self.df_res.status_best[1:].value_counts()))
            self.logger.info(('Stable languages based on labelings ' +
                              '(where crossvalidation exceeds limit):\n{}')\
                             .format(self.df_res.stable_best[1:].value_counts()))

        df_filename       = self.out_template + ".tsv"
        crossval_filename = self.out_template + "-crossval.tsv"

        self.logger.info('exporting dataframe to {}'.format(df_filename))
        self.df_res.to_csv(df_filename, sep='\t', encoding='utf-8')

        self.logger.info('exporting crossvalidations to {}'.format(crossval_filename))
        self.df_res_crossval.to_csv(crossval_filename, sep='\t', encoding='utf-8')


        # The probabilities
        proba_filename_template = self.out_template + "-prob-"

        for category, df in self.df_res_dprobas.iteritems():
            proba_filename = proba_filename_template + category + ".tsv"

            self.logger.info('exporting probabilities to {}'.format(proba_filename))
            df.to_csv(proba_filename, sep='\t', encoding='utf-8')
      
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
    parser = argparse.ArgumentParser(description="""
        5-way Logistic Regression (Maximum Entropy) classifier for the
        langdeath language data. Three output files are created from the specified
        template: "template.tsv", classification results, (both per-experiment and
        summary); "template-prob.tsv", per-experiment classification probabilities;
        and "template-crossval.tsv", per-experiment crossvalidation values.""")

    parser.add_argument("input_tsv", help="data file in tsv format")
    parser.add_argument("output_template",
                       help="filename template for writing output files")
    parser.add_argument("-e", "--experiment_count", type=int,
                        help="number of experiments with random seed sets",
                        default=100)
    parser.add_argument("-c", "--class_counts", type=int, default=2,
                        choices=[2, 3, 4, 5],
                        help="2 - still/historic vs. vital/thriving/global, " +
                             "3 - still/historic vs. vital vs. thriving/global, " +
                             "4 - still vs. historic vs. vital vs. thriving/global, " +
                             "5 - still vs. historic vs. thriving vs. vital vs. global")
    parser.add_argument("-t", "--threshold", type=float, default=0.9, 
                       help="lower limit on cross-validation accuracy for counting " +
                        "statistics on 'filtered' labelings")
    parser.add_argument("-l", "--log_file", default="classifier.log",
                       help="file for logging")
    parser.add_argument('-s', '--status', action="store_true", help='use status features')
    return parser.parse_args()



def main():
    
    args = get_args()
    logger = get_logger(args.log_file)
    preprocessed_tsv = args.input_tsv
    exp_count = args.experiment_count
    classcount = args.class_counts
    limit = args.threshold
    out_template = args.output_template
    status_usage = args.status
    a = Classifier(preprocessed_tsv, exp_count, classcount, limit, logger,
                  out_template, status_usage)
    a.train_classify()

if __name__ == '__main__':
    main()
