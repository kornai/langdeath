import logging
from math import log
from collections import Counter
import pandas
import sqlite3

class Preproc:

    def __init__(self, sqlite_fn, train_dir, feat_dir, 
                 preprocessed_fn='preproc.tsv',
                 joined_fn='joined.tsv'):
        self.sqlite_fn = sqlite_fn
        self.preprocessed_fn = preprocessed_fn
        self.joined_fn = joined_fn
        self.train_dir = train_dir
        self.feat_dir = feat_dir
        self.get_seed_sets()
        self.get_feat_set()

    
    def get_seed_sets(self):

        self.t_set = [l.strip() for l in open('{}/t'.format(self.train_dir))]
        self.v_set = [l.strip() for l in open('{}/v'.format(self.train_dir))]
        self.h_set = [l.strip() for l in open('{}/h'.format(self.train_dir))]
        self.s_set = [l.strip() for l in open('{}/s_3900'.format(self.\
                                                                 train_dir))]
    
    def get_feat_set(self):

        self.needed = [l.strip() for l in open(
            '{}/needed_feats'.format(self.feat_dir))]
        self.log_needed = [l.strip() for l in open(
            '{}/log_needed'.format(self.feat_dir))]
        self.bool_needed = [l.strip() for l in open(
            '{}/bool_needed'.format(self.feat_dir))]
        self.individual_defaults = {'eth_status': 7,
                                    'endangered_aggregated_status': 5}

    def get_df(self):
        conn = sqlite3.connect(self.sqlite_fn)
        self.df = pandas.read_sql("SELECT * FROM dld_language", conn)
        self.speakers = pandas.read_sql("SELECT * FROM dld_speaker", conn)
        self.language_speakers =\
                pandas.read_sql("SELECT * FROM dld_language_speakers", conn)
        self.endangered_levels = pandas.read_sql(
            "SELECT * FROM dld_endangeredlevel", conn)
        self.language_endangered_levels =\
                pandas.read_sql(
                    "SELECT * FROM dld_language_endangered_levels", conn)
        self.join_speaker_counts()
        self.join_endangered_levels()
        self.df = self.df.set_index([u'sil'])
        
    
    def join_speaker_counts(self):
        
        aggreg = self.language_speakers.merge(
            self.speakers, left_on='speaker_id', right_on='id')

        l2_ag = aggreg[aggreg['l_type'] == 'L2'].\
                groupby(['language_id']).max()
        l2_tojoin = l2_ag.rename(columns={'num': 'L2'})[['L2']]
        
        self.df = self.df.merge(l2_tojoin, left_on='id',
                                right_index=True, how='left')

        l1_ag = aggreg[(aggreg.l_type == 'L1') & (aggreg.src.isin(
            ['ethnologue', 'aggregate']))].groupby(['language_id']).mean()
        l1_tojoin = l1_ag.rename(columns={'num': 'L1'})[['L1']]

        self.df = self.df.merge(l1_tojoin, left_on='id', right_index=True,
                               how='left')
    
    def join_endangered_levels(self):
        
        aggreg = self.language_endangered_levels.merge(
        self.endangered_levels, left_on="endangeredlevel_id", right_on="id",
            suffixes=("", "_e"))
        self.join_ethnologue_levels(aggreg)
        self.join_end_endangered_levels(aggreg)
    
    def join_ethnologue_levels(self, aggreg):
        aggreg['src_is_ethnologue'] = aggreg['src'] == 'ethnologue'
        eth_aggreg = aggreg[aggreg['src_is_ethnologue'] == True]
        aggreg["eth_status"] = 7.
        eth_aggreg.loc[:,'eth_status'] = (eth_aggreg['level'].map(
            lambda x:float(x.replace("a", ".0").replace(
            "b", ".5").replace('x', ''))))
        eth_tojoin = eth_aggreg[["language_id", "eth_status"]]

        self.df = self.df.merge(eth_tojoin, left_on="id",
                                right_on="language_id", how="left")

    def join_end_endangered_levels(self, aggreg):
        category_map = {'Safe': 8,
                         'At risk': 6,
                         'Vulnerable': 5,
                         'Threatened': 4,
                         'Endangered': 3,
                         'Severely endangered': 2,
                         'Critically endangered': 1,
                         'Dormant': 0,
                         'Awakening': 0,
                       }
        end_aggreg = aggreg.loc[aggreg['src_is_ethnologue'] == False]
        gr = end_aggreg.groupby("language_id")
        end_top_level = gr.agg({"level": lambda x: Counter(x).\
                                most_common(1)[0][0]})
        end_top_level["endangered_aggregated_status"]\
                = end_top_level["level"]\
                .map(lambda x: category_map[x])

        self.df = self.df.merge(
                end_top_level[["endangered_aggregated_status"]],
                left_on="id", right_index=True, how="left")
    
    def add_labels(self):
        
        self.df['seed_label'] = self.df.index.map(lambda x:
                                                  's' if x in self.s_set
                                                  else 'h' if x in self.h_set
                                                  else 'v' if x in self.v_set
                                                  else 't' if x in self.t_set
                                                  else '-')
        
        #self.df['seed_label_2class'] = self.df.seed_label\
        #        .map(lambda x:
        #             'sh' if x == 'm' or x == 'h'
        #             else 'tv' if x == 't' or x == 'v'
        #             else '-')     

    def numerical_preproc(self):
        
        self.df[self.bool_needed] = self.df[self.bool_needed].fillna(0)
        self.df[self.log_needed] = self.df[self.log_needed].fillna(0)
        self.df[self.log_needed] = self.df[self.log_needed].applymap(
            lambda x: log(x+1))
        for f in self.individual_defaults:
            self.df[f] = self.df[f].fillna(self.individual_defaults[f])

    def preproc_data(self):
        
        self.get_df()
        self.df.to_csv(self.joined_fn, sep='\t', encoding='utf-8')
        self.numerical_preproc()
        self.add_labels()
        self.df[self.needed + ['seed_label']].\
                to_csv(self.preprocessed_fn, sep='\t', encoding='utf-8')
        
def main():
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    fn = '/home/pajkossy/Proj/langdeath/langdeath.db.sqlite3'
    train_data_dir = '/home/pajkossy/Proj/langdeath/classification/seed_data/'
    feat_data_dir = '/home/pajkossy/Proj/langdeath/classification/feat_data/'
    a = Preproc(fn, train_data_dir, feat_data_dir)
    a.preproc_data()
    print a.df[a.needed + ['seed_label']].keys()

if __name__ == "__main__":
    main()
