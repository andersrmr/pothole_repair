import pandas as pd
import numpy as np
import fiona
from shapely.geometry import shape, Polygon, MultiPolygon, Point, MultiPoint
import cPickle as pickle
from geopy.distance import vincenty

# Lat-lons for key Seattle locations
SEATTLE_LOC = (47.6062095, -122.3320708)
SPACE_NEEDLE_LOC = (47.6205063, -122.3492774)
PIKE_PLACE_LOC = (47.60972, -122.342193)
CONVENTION_CENTER_LOC = (47.611389, -122.33168)
WOODLAND_PARK_ZOO_LOC = (47.6685394, -122.3536447)
QUEENE_ANNE_LOC = (47.63747,-122.3578884)

def _get_distance(df, origin):
    '''
    INPUT: df, tuple
    OUTPUT: pandas Series
    Input dataframe has lat-lon coords for each row/pothole.
    Returns Series containing distance from origin to each pothole.
    '''
    dists = []
    for row in df.index.tolist():
        point = df.ix[row,'latitude'], df.ix[row, 'longitude']
        dist = vincenty(origin, point)
        dists.append(dist.miles)
    dists = pd.Series(dists, index=df.index)
    return dists

def create_distances(df):
    '''
    INPUT: df
    OUTPUT: df
    Pass in cleaned data as dataframe and add columns containing
    distances to key landmarks in Seattle
    1. City center
    2. Space Needle
    3. Convention center
    4. Center of Queene Anne neighborhood
    5. Pike Place
    6. Woodland_Park_zoo_loc
    '''
    df['Seattle_dist'] = _get_distance(df, SEATTLE_LOC)
    df['Space_Needle_dist'] = _get_distance(df, SPACE_NEEDLE_LOC)  
    df['Pike_Place_dist'] = _get_distance(df, PIKE_PLACE_LOC) 
    df['Convention_Center_dist'] = _get_distance(df, CONVENTION_CENTER_LOC) 
    df['Woodland_Park_dist'] = _get_distance(df, WOODLAND_PARK_ZOO_LOC) 
    df['Queene_Anne_dist'] = _get_distance(df, QUEENE_ANNE_LOC) 

    return df

def create_seasonality(df):
    '''
    INPUT: df
    OUTPUT: df
    Pass in cleaned data as dataframe and add columns representing
    seasonality trends
    '''
    quarters = [df.ix[row, 'INITDT_dt'].quarter for row in df.index.tolist()]
    df['INIT_Quarter'] = pd.Series(quarters, index = df.index)

    days = [6 - df.ix[row, 'INITDT_dt'].month for row in df.index.tolist()]
    df['days_end_FY'] = pd.Series(days, index = df.index)

    months = [df.ix[row, 'INITDT_dt'].month for row in df.index.tolist()]
    df['INIT_month'] = pd.Series(months, index = df.index)

    return df

def get_neighborhoods(df):
    '''
    INPUT: df
    OUTPUT: df
    Pass in the cleaned data as a dataframe and add a new column
    containing the neighborhood the pothole belongs to
    '''
    # Read in shapefile of Seattle neighborhoods
    shapefilename = 'data/Neighborhoods'
    shp = fiona.open(shapefilename+'.shp')
    
    # Get neighborhood polys and their indices
    polys = [shape(pol['geometry']) for pol in shp]
    shp.close()
    neighborhood_index = [i+1 for i in range(len(polys))]

    # Associate each neighborhood polygon with its index
    neighborhoods_tup = []
    for hood in xrange(len(polys)):
        neighborhoods_tup.append((MultiPolygon(polys)[hood],\
        neighborhood_index[hood]))

    # Get potholes
    all_potholes = MultiPoint([Point(x, y) for x, y in zip(df['longitude'],\
        df['latitude'])])

    # Associate each pothole with its df index
    potholes_tup = []
    for hole in xrange(df.shape[0]):
        potholes_tup.append((all_potholes[hole], df.index.tolist()[hole]))

    # Keep the potholes, indices that fall within the neighborhoods.
    # Pickle them for later usage.
    city_holes_inds = []
    city_holes = []
    for hole in xrange(len(potholes_tup)):
        for hood in xrange(len(neighborhoods_tup)):
            if neighborhoods_tup[hood][0].contains(potholes_tup[hole][0]):
                city_holes.append(potholes_tup[hole][0])
                city_holes_inds.append(potholes_tup[hole][1])
    
    city_potholes = (city_holes, city_holes_inds)
    with open('city_potholes.pkl', 'w') as f:
        pickle.dump(city_potholes, f)

    # Extract the neighborhood index associated with each pothole
    neighborhood_label = []
    for hole in xrange(len(city_holes)):
        for hood in xrange(len(neighborhoods_tup)):
            if neighborhoods_tup[hood][0].contains(city_holes[hole]):
                neighborhood_label.append(neighborhoods_tup[hood][1])

    # Add labels to dataframe
    df['neighborhood_label'] = pd.Series(neighborhood_label,\
        index = city_holes_inds)

    return df

def get_census_economic_vals(df):
    '''
    INPUT: df
    OUTPUT: df
    Pass in the cleaned data as a dataframe and add a new column
    containing economic values based on census data.
    '''
    # Read in shapefile of Seattle block groups
    shapefilename = 'data/tl_2013_53_bg_Seattle'
    shp = fiona.open(shapefilename+'.shp')

    # Get block group polys and their indices
    polys = [shape(pol['geometry']) for pol in shp]

    # Associate each block group polygon with its GEOID
    block_group_tup = []
    idx = 0
    for feature in shp:
        block_group_tup.append((MultiPolygon(polys)[idx],\
        feature['properties']['GEOID']))
        idx += 1
    shp.close()

    with open('city_potholes.pkl') as f:
        city_potholes = pickle.load(f)

    # Extract the block group GEOID associated with each pothole
    block_group_label = []
    for hole in xrange(len(city_potholes[0])):
        found = False
        for group in xrange(len(block_group_tup)):
            if block_group_tup[group][0].contains(city_potholes[0][hole]):
                block_group_label.append(block_group_tup[group][1])
                found = True
        if not found:
            block_group_label.append('')

    # Add block group to dataframe
    df['GEOID'] = pd.Series(block_group_label,\
        index = city_potholes[1])
 
    # Read in, prep, join economic data
    df_econ = pd.read_csv('data/ACS_13_5YR_B25077_with_ann.csv',\
        skiprows=range(1,2))
    df_econ.rename(columns={'GEO.id2':'GEOID'}, inplace=True)
    df_econ['GEOID'] = df_econ['GEOID'].astype('unicode')
    df = pd.merge(df, df_econ, how='left', on='GEOID')

    # Convert economic values to floats, NaNs if not possible
    df['HD01_VD01'] = df['HD01_VD01'].\
        convert_objects(convert_numeric=True)
    df['HD02_VD01'] = df['HD02_VD01'].\
        convert_objects(convert_numeric=True)

    # Rename economic values
    df.rename(columns={'HD01_VD01': 'Median_Value',\
                       'HD02_VD01': 'Margin_of_Error'}, inplace=True)

    return df

def do_nlp_on_location(df):
	''''
    Do nlp on LOCATION field and add new column to df
	'''
	pass

if __name__ == '__main__':
    df = pd.read_pickle('df_1to1999_geo_cleaned.pkl')
    df = create_distances(df)
    df = create_seasonality(df)
    df = get_neighborhoods(df)
    df = get_census_economic_vals(df)
    df.to_pickle('df_1to1999_features.pkl')
    print df.head(25)
    print df.tail(25)

