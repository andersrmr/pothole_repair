import pandas as pd
import numpy as np
import cPickle as pickle
from geopy.geocoders import GoogleV3

# google API server key
file_path = 'C:\Users\\andersrmr\.ssh\\richard_google_developer_key'
with open(file_path) as p:
    KEY=p.read().strip('\n')

geolocator = GoogleV3(KEY)
# geolocator = GoogleV3()

def clean_data():
    '''
    INPUT: None
    OUTPUT: None
    Read in raw pothole data from disk, do some cleaning then pickle
    the cleaned dataframe.
    '''
    df = pd.read_csv('data/Pothole_Repairs_Seattle.csv')

    # Convert to datetime columns
    df['FLDSTARTDT_dt'] = pd.to_datetime(df['FLDSTARTDT'])
    df['INITDT_dt'] = pd.to_datetime(df['INITDT'])
    df['FLDENDDT_dt'] = pd.to_datetime(df['FLDENDDT'])

    # Keep completed repairs
    df['IS_COMPLETED'] = df['WO_STATUS'] == 'COMPLETED'
    df = df[df['IS_COMPLETED'] == True]
    df.drop('IS_COMPLETED', axis=1, inplace=True)

    # Keep only dates where end later than beginning
    df['DATE_REVERSE'] = df['INITDT_dt'] > df['FLDENDDT_dt']
    df = df[df['DATE_REVERSE'] == False]
    df.drop('DATE_REVERSE', axis=1, inplace=True)

    # Create repair time column and discard 0 repair times
    df['DURATION'] = df['FLDENDDT_dt'] - df['INITDT_dt']
    df['DURATION_td'] = df['DURATION'].astype('timedelta64[D]')
    df = df[df['DURATION'] != '0 days']

    # Keep only the columns I need
    df = df[['OBJECTID','WOKEY','LOCATION','ADDRDESC','INITDT_dt',\
        'FLDSTARTDT_dt','FLDENDDT_dt','DURATION','DURATION_td']]

    # df.to_pickle('df_all_cleaned.pkl')
    return df

def _forward_geocode(df):
    new_locs = []
    for row in df.index.tolist():
        loc = df.ix[row,'ADDRDESC'] + ' Seattle'
        loc = geolocator.geocode(loc, timeout=10)
        new_locs.append((row, loc))
    return new_locs

def _reverse_geocode(df):
    rev_locs = []
    for row in df.index.tolist():
        rev_loc = df.ix[row,'latitude'], df.ix[row,'longitude']
        addr = geolocator.reverse(rev_loc, exactly_one=True, timeout=10).address
        rev_locs.append((row, addr))
    return rev_locs

def do_geocoding():
    '''
    INPUT: None
    OUTPUT: None
    Read in pickled, clean data, geocode the pothole locations, then 
    reverse geocode them to get closest addresses to each pothole.
    Pickle result.
    '''
    df = pd.read_pickle('df_all_cleaned.pkl')
    # df = df.loc[0:999,:]
    # df = df.loc[999:1499,:]
    df = df.loc[1499:1999,:]

    # Forward geocoding
    geocodes = _forward_geocode(df)

    # Create an index
    inds = []
    for elem in geocodes:
        inds.append(elem[0])

    # Create Series of lats, longs, general addresses; add to df
    lats, longs, addrs = [], [], []
    for elem in geocodes:
        lats.append(elem[1].latitude)
        longs.append(elem[1].longitude)
        addrs.append(elem[1].address)
    
    lats = pd.Series(lats, index=inds, name='lats')
    longs = pd.Series(longs, index=inds, name='longs')
    addrs = pd.Series(addrs, index=inds, name='addrs')

    df['latitude'] = lats 
    df['longitude'] = longs
    df['address'] = addrs

    # Reverse geocoding
    # rev_geocodes = _reverse_geocode(df)

    # Create Series of specific addresses from reverse geocoding; add to df
    # addrs_dets = []
    # for elem in rev_geocodes:
    #     addrs_dets.append(elem[1])
    # addrs_dets = pd.Series(addrs_dets, index=inds, name='addrs_det')

    # df['address_detail'] = addrs_dets

    # df.to_pickle('df_first1000_cleaned.pkl')
    df.to_pickle('df_1499to1999_cleaned.pkl')
    return df

def clean_geocoded():
    '''
    Remove rows with poorly performing geocoding
    '''
    pass

if __name__ == '__main__':
    # df = pd.read_pickle('../sandbox/df_first757_cleaned.pkl')
    # df = get_neighborhoods(df)
    # df = get_census_economic_vals(df)
    # df = create_distances(df)
    # df = clean_data()
    df = do_geocoding()
    print df.head(25)
    # print df
    print df.info()
