import pandas as pd
import numpy as np
import cPickle as pickle
from geopy.geocoders import GoogleV3

# google API server key
KEY_FILEPATH = 'C:\Users\\andersrmr\.ssh\\richard_google_developer_key'

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

    df.to_pickle('df_all_cleaned.pkl')

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
    Read in pickled, clean data, geocode the pothole locations.

    ***WARNING***

    RUNNING THIS CODE IGNORES THE QUERY LIMITS THAT EXIST ON THE GOOGLEMAPS API.
    TO AVOID BEING CUT OFF, RUN IN SMALLER CHUNKS OF, SAY, 500, EVERY FEW MINUTES,
    UP TO YOUR DAILY LIMIT OF 2,500.  USE THE ADDITIONAL FUNCTIONS BELOW, e.g., 
    _append_geocoded_dfs to put the geocoded dataframes together.

    ***WARNING***

    '''
    df = pd.read_pickle('df_all_cleaned.pkl')
    
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

def clean_geocoded(df):
    '''
    INPUT: df
    OUTPUT: None
    Remove rows with poorly performing geocoding
    '''
    df = df[df['address'] != 'Seattle, WA, USA']
    df.to_pickle('df_geo_cleaned.pkl')

def main():
    with open(KEY_FILEPATH) as p:
       KEY=p.read().strip('\n')

    geolocator = GoogleV3(KEY)

    df = clean_data()
    df = do_geocoding()
    clean_geocoded(df)

if __name__ == '__main__':
    main()