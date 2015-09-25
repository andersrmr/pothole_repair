import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cross_validation import KFold
from sklearn.cross_validation import train_test_split
from sklearn.cross_validation import cross_val_score
import cPickle as pickle

def clean_prep_before_model(flag=True):
    '''
    INPUT: None
    OUTPUT: df
    Read in pickled df with all features computed.  Do final cleaning,
    then pass cleaned df to model steps
    '''
    df = pd.read_pickle('df_1to7499_features.pkl')

    # Keep only rows with no Median_Value NaNs, neighborhood_label == '', NaNs; 
    # street feature NaNs
    df = df[np.isfinite(df['Median_Value'])]
    df = df[df['neighborhood_label'] != '']
    df = df[np.isfinite(df['neighborhood_label'])]
    df = df[np.isfinite(df['SND_FEACOD'])]

    # Remove rows where DURATION_td rounded to zero.
    df = df[df.DURATION_td != 0.000]

    # Conditionally label NaN street features 'no street features'
    if flag:
        df.SND_FEACOD = df.SND_FEACOD.fillna('NO SND_FEACOD')
        df.ST_CODE = df.ST_CODE.fillna('NO ST_CODE')
        df.SEGMENT_TY = df.SEGMENT_TY.fillna('NO SEGMENT_TY')
        df.DIVIDED_CO = df.DIVIDED_CO.fillna('NO DIVIDED_CO')
        df.VEHICLE_US = df.VEHICLE_US.fillna('NO VEHICLE_US')

    # Create another feature, number of potholes initiated on that day
    # ***Later, move this to a function in create_features.py***
    df_number_potholes = pd.DataFrame(df.groupby('INITDT_dt')['OBJECTID'].\
        count()).reset_index()
    df_number_potholes.rename(columns={'OBJECTID': 'Number_potholes'},\
        inplace=True)
    df = pd.merge(df, df_number_potholes, how='left', on='INITDT_dt')

    # Keep only the columns for modeling
    df = df.ix[:, ['neighborhood_label','INIT_Quarter','INIT_month','days_end_FY',\
        'Median_Value','Queene_Anne_dist','Woodland_Park_dist','Space_Needle_dist',\
        'Seattle_dist','latitude','longitude','INITDT_dt','FLDENDDT_dt','DURATION',\
        'DURATION_td','Margin_of_Error','Convention_Center_dist','Pike_Place_dist',\
        'SND_FEACOD','ST_CODE','SEGMENT_TY','DIVIDED_CO','VEHICLE_US']]

    if df.isnull().values.any():
        print 'You still have NaNs'
        return df

    df.to_pickle('df_1to7499_alldata.pkl')

    df = pd.concat([df.ix[:, ['Queene_Anne_dist','Woodland_Park_dist','DURATION_td',\
        'Space_Needle_dist','Convention_Center_dist','Pike_Place_dist',\
        'Seattle_dist','latitude','longitude','Median_Value','Margin_of_Error']],\
        df.neighborhood_label.astype('category'),df.SND_FEACOD.astype('category'),\
        df.INIT_Quarter.astype('category'),df.ST_CODE.astype('category'),\
        df.SEGMENT_TY.astype('category'),\
        df.DIVIDED_CO.astype('category')], axis=1)

    return df

def define_target_vars(df):
    '''
    INPUT: df
    OUTPUT: df
    Define different target variables based on pothole repair time
    '''
    df['b_long_repair'] = df.DURATION_td > 3
    df['b_long_repair'] = df['b_long_repair'].apply(lambda x: 1 if x == True else 0) 
    
    df['b_DURATION_td_95'] = df.DURATION_td < df.DURATION_td.quantile(.95)
    df['b_DURATION_td_IQuart'] = (df.DURATION_td < df.DURATION_td.quantile(.75))\
        & (df.DURATION_td > df.DURATION_td.quantile(.25))

    return df

def lr_model(df):
    '''
    INPUT: None
    OUTPUT: None
    Build a linear regression model
    '''
    # y = df.pop('DURATION_td')
    # X = df
    pass

def rf_model(df):
    '''
    INPUT: None
    OUTPUT: None
    Build a random forest model
    '''
    pass
    
if __name__ == '__main__':
    df = clean_prep_before_model()
    df.info()
    # rf_model(df)

    