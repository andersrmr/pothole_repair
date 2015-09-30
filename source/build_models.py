import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.cross_validation import KFold
from sklearn.cross_validation import train_test_split
from sklearn.cross_validation import cross_val_score
import cPickle as pickle
import sklearn.metrics as skm
from sklearn.metrics import confusion_matrix
import sys
from sklearn.ensemble import RandomForestClassifier

def clean_prep_before_model():
    '''
    INPUT: None
    OUTPUT: df
    Read in pickled df with all features computed.  Do final cleaning,
    then pass cleaned df to model steps
    '''
    df = pd.read_pickle('df_1to10999_features.pkl')

    # Keep only rows with no Median_Value NaNs, neighborhood_label == '', NaNs; 
    # street feature NaNs
    df = df[np.isfinite(df['Median_Home_Value'])]
    df = df[df['neighborhood_label'] != '']
    df = df[np.isfinite(df['SND_FEACOD'])]

    # Remove rows where DURATION_td rounded to zero.
    df = df[df.DURATION_td != 0.000]

    # Label NaN street features 'no street features'
    df.SND_FEACOD = df.SND_FEACOD.fillna('NO SND_FEACOD')
    df.ST_CODE = df.ST_CODE.fillna('NO ST_CODE')
    df.SEGMENT_TY = df.SEGMENT_TY.fillna('NO SEGMENT_TY')
    df.DIVIDED_CO = df.DIVIDED_CO.fillna('NO DIVIDED_CO')
    df.VEHICLE_US = df.VEHICLE_US.fillna('NO VEHICLE_US')

    if df.isnull().values.any():
        print 'You still have NaNs'
        return df

    # Conditionally add no. of potholes feature from pickled file
    if 'cumul_potholes' not in df:
        df['INITDT_date_only'] = df['INITDT_dt'].apply( lambda x: x.date())
        df['INITDT_date_only'] = pd.to_datetime(df.INITDT_date_only)

        df_number_potholes = pd.read_pickle('df_number_potholes.pkl')
        df = df.reset_index()
        df = pd.merge(df, df_number_potholes, how='left', on='INITDT_date_only')
        df = df.set_index('index')

    # Conditionally compute and add Temp feature
    if 'Temp' not in df:
        df = create_features.get_temp(df)

    # Conditionally compute and add min_dist feature
    if 'min_dist' not in df:
        df['min_dist'] = df[['Seattle_dist','Space_Needle_dist','Pike_Place_dist',\
            'Convention_Center_dist','Woodland_Park_dist']].min(axis=1)

    # Conditionally rename days_end_FY feature:
    if 'days_end_FY' in df:
        df.rename(columns={'days_end_FY': 'months_end_FY'}, inplace=True)

    # Get rid of unneeded columns
    df.drop(['OBJECTID','WOKEY','LOCATION','ADDRDESC','address',\
        'Seattle_dist','Space_Needle_dist','Pike_Place_dist',\
        'Convention_Center_dist','Woodland_Park_dist','Queene_Anne_dist',\
        'GEOID','GEO.id_x','GEO.id_y','GEO.display-label_y',\
        'GEO.display-label_x',], axis=1, inplace=True)

    df.neighborhood_label = df.neighborhood_label.astype('category')
    df.SND_FEACOD = df.SND_FEACOD.astype('category')
    df.ST_CODE = df.ST_CODE.astype('category')
    df.SEGMENT_TY = df.SEGMENT_TY.astype('category')
    df.DIVIDED_CO = df.DIVIDED_CO.astype('category')
    df.VEHICLE_US = df.VEHICLE_US.astype('category')

    return df

def define_target_vars(df):
    '''
    INPUT: df
    OUTPUT: df
    Define different target variables based on pothole repair time
    '''
    df['b_long_repair'] = df.DURATION_td > 3
    df['long_repair'] = df['b_long_repair'].apply(lambda x: 1 if x == True else 0) 
    
    df['b_DURATION_td_95'] = df.DURATION_td < df.DURATION_td.quantile(.95)
    df['b_DURATION_td_IQuart'] = (df.DURATION_td < df.DURATION_td.quantile(.75))\
        & (df.DURATION_td > df.DURATION_td.quantile(.25))

    # Focus modeling on repair durations less than the 95th percentile
    df = df[df['b_DURATION_td_95']]
    df.to_pickle('df_95_features.pkl')

    return df

def select_predictors(df, dummies=False, choose_dummies=True):
    '''
    INPUT: df
    OUTPUT: df
    Select and return predictor variables
    '''
    X = ['cumul_potholes','Median_Home_Value','Temp','min_dist']

    # Conditionally compute categorical dummy variables
    if dummies:
        df_dum_neighborhood_label = pd.get_dummies(df.neighborhood_label)
        df_dum_SND_FEACOD = pd.get_dummies(df.SND_FEACOD)
        df_dum_ST_CODE = pd.get_dummies(df.ST_CODE)
        df_dum_SEGMENT_TY = pd.get_dummies(df.SEGMENT_TY)
        df_dum_DIVIDED_CO = pd.get_dummies(df.DIVIDED_CO)
        df_dum_VEHICLE_US = pd.get_dummies(df.VEHICLE_US)

        df_dummies = pd.concat([df_dum_SND_FEACOD, df_dum_ST_CODE, df_dum_SEGMENT_TY,\
            df_dum_DIVIDED_CO, df_dum_VEHICLE_US, df_dum_neighborhood_label], axis=1)

        if choose_dummies:
            X = pd.concat([df.ix[:, X], df_dum_neighborhood_label], axis=1)
        else:
            X = pd.concat([df.ix[:, X], df_dummies], axis=1)
    
    return df[X]

def logit_model(df, X):
    '''
    INPUT: None
    OUTPUT: None
    Build a logistic regression model
    '''
    y = df['long_repair']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=67)

    lr = LogisticRegression(class_weight='auto')
    lr.fit(X_train, y_train)

    print 
    print 'Logistic Regression'
    print '-------------------'
    print
    print 'Predictors: ', X.columns.tolist()
    print
    print 'Accuracy: ', lr.score(X_test,y_test)
    print 'AUC: ', skm.roc_auc_score(y_test, lr.predict(X_test))
    print 
    print confusion_matrix(y_test, lr.predict(X_test))

def rf_model(df, X):
    '''
    INPUT: None
    OUTPUT: None
    Build a random forest model
    '''
    y = df['long_repair']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=67)
    rfc = RandomForestClassifier(n_estimators=500, n_jobs=-1) 
    rfc.fit(X_train, y_train)

    print
    print 'Random Forest Classifier'
    print '------------------------'
    print 
    print 'Predictors: ', X.columns.tolist()
    print
    print 'Accuracy: ', rfc.score(X_test,y_test)
    print 'AUC: ', skm.roc_auc_score(y_test, rfc.predict(X_test))
    print 
    print confusion_matrix(y_test, rfc.predict(X_test))

def main():
    df = clean_prep_before_model()
    df.info()
    df = define_target_vars(df)
    X = select_predictors(df, dummies=False, choose_dummies=True)
    logit_model(df, X)
    rf_model(df, X)
    
if __name__ == '__main__':
    sys.path.insert(0, '../source')
    import create_features
    main()
    
    