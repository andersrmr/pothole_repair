import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cross_validation import KFold
from sklearn.cross_validation import train_test_split
from sklearn.cross_validation import cross_val_score
import cPickle as pickle

def clean_before_model():
    '''
    INPUT: None
    OUTPUT: df
    Read in pickled df with all features computed.  Do final cleaning,
    then pass cleaned df to model steps
    '''
    df = pd.read_pickle('df_1to1999_features.pkl')

    return df

def lr_model(df):
    '''
    INPUT: None
    OUTPUT: None
    Run a linear LinearRegression
    '''
    

    # Assemble feature data
    df = pd.concat([df.ix[:, ['Queene_Anne_dist','Woodland_Park_dist',\
        'Space_Needle_dist','Seattle_dist','latitude','longitude']],\
        df.neighborhood_cat.astype('category'),\
        df.INIT_Quarter.astype('category'),\
        df.days_end_FY.astype('category')], axis=1)



if __name__ == '__main__':
    