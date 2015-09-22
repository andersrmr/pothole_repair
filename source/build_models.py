import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cross_validation import KFold
from sklearn.cross_validation import train_test_split
from sklearn.cross_validation import cross_val_score
import cPickle as pickle

def clean_prep_before_model():
    '''
    INPUT: None
    OUTPUT: df
    Read in pickled df with all features computed.  Do final cleaning,
    then pass cleaned df to model steps
    '''
    df = pd.read_pickle('df_1to1999_features.pkl')

    # Keep only rows with no Median_Value, neighborhood_label NaNs
    if np.any(pd.isnull(df['Median_Value'])):
    	df = df[np.isfinite(df['Median_Value'])]

    if np.any(pd.isnull(df['neighborhood_label'])):
        df = df[np.isfinite(df['neighborhood_label'])]

    # Keep only the columns for modeling
    df = df.ix[:, ['neighborhood_label','INIT_Quarter','INIT_month','days_end_FY',\
        'Median_Value','Queene_Anne_dist','Woodland_Park_dist','Space_Needle_dist',\
        'Seattle_dist','latitude','longitude','INITDT_dt','FLDENDDT_dt','DURATION',\
        'DURATION_td','Margin_of_Error','Convention_Center_dist','Pike_Place_dist']]

    if df.isnull().values.any():
    	print 'You still have NaNs'
    	return df

    df = pd.concat([df.ix[:, ['Queene_Anne_dist','Woodland_Park_dist','DURATION_td',\
        'Space_Needle_dist','Convention_Center_dist','Pike_Place_dist',\
        'Seattle_dist','latitude','longitude','Median_Value','Margin_of_Error']],\
        df_all.neighborhood_label.astype('category'),\
        df_all.INIT_Quarter.astype('category'),\
        df_all.INIT_month.astype('int')], axis=1)

    return df

def lr_model(df):
    '''
    INPUT: None
    OUTPUT: None
    Run a linear LinearRegression
    '''
    y = df.pop('DURATION_td')
    X = df
    


    



if __name__ == '__main__':
    