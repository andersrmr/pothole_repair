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
    df = df[df['WO_STATUS'] == 'COMPLETED']

    # Keep only dates where end later than beginning
    df = df[df['INITDT_dt'] < df['FLDENDDT_dt']]

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
    # df = df.loc[1499:1999,:]
    # df = df.loc[1999:2499,:]
    # df = df.loc[2499:2999,:]
    # df = df.loc[2999:3499,:]
    # df = df.loc[3499:3999,:]
    # df = df.loc[3999:4499,:]
    # df = df.loc[4499:4999,:]
    # df = df.loc[4999:5499,:]
    # df = df.loc[5499:5999,:]
    # df = df.loc[5999:6499,:]
    # df = df.loc[6499:6999,:]
    df = df.loc[6999:7499,:]

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
    # df.to_pickle('df_999to1499_cleaned.pkl')
    # df.to_pickle('df_1999to2499_cleaned.pkl')
    # df.to_pickle('df_2499to2999_cleaned.pkl')
    # df.to_pickle('df_2999to3499_cleaned.pkl')
    # df.to_pickle('df_3499to3999_cleaned.pkl')
    # df.to_pickle('df_3999to4499_cleaned.pkl')
    # df.to_pickle('df_4499to4999_cleaned.pkl')
    # df.to_pickle('df_4999to5499_cleaned.pkl')
    # df.to_pickle('df_5499to5999_cleaned.pkl')
    # df.to_pickle('df_5999to6499_cleaned.pkl')
    # df.to_pickle('df_6499to6999_cleaned.pkl')
    df.to_pickle('df_6999to7499_cleaned.pkl')
    return df

def _append_geocoded_dfs(df1, df2):
    '''
    INPUT: df, df
    OUTPUT: df
    Append df2 to df1.  First ck if last row df1 = first row of df2.  If so,
    remove first row of df2 before appending.
    '''
    if df1.tail(1).index == df2.head(1).index:
        df2 = df2.drop(df2.head(1).index, 0)
        return df1.append(df2)
    return df1.append(df2)

def clean_geocoded():
    '''
    Remove rows with poorly performing geocoding
    '''
    df = pd.read_pickle('df_1to6999_cleaned.pkl')

    df = df[df['address'] != 'Seattle, WA, USA']
    df.to_pickle('df_1to6999_geo_cleaned.pkl')

if __name__ == '__main__':
    # df = pd.read_pickle('../sandbox/df_first757_cleaned.pkl')
    # df = get_neighborhoods(df)
    # df = get_census_economic_vals(df)
    # df = create_distances(df)
    # df = clean_data()
    # df = do_geocoding()
    # df2 = pd.read_pickle('df_1to6499_cleaned.pkl')
    # df3 = pd.read_pickle('df_6499to6999_cleaned.pkl')
    # df = _append_geocoded_dfs(df2, df3)
    # df.to_pickle('df_1to6999_cleaned.pkl')
    # print df2.tail(2)
    # print df3.head(2)
    # print df.loc[1495:1505,:]
    # print df
    # df.info()
    clean_geocoded()