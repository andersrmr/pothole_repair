import pandas as pd
import numpy as np
import fiona
from shapely.geometry import shape, Polygon, MultiPolygon, Point,\
    MultiLineString, MultiPoint
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

def _get_potholes(df):
    '''
    INPUT: df
    OUTPUT: None
    Create geometries for all potholes, get their indices and pickle as a tuple
    '''
    all_potholes = MultiPoint([Point(x, y) for x, y in zip(df['longitude'],\
        df['latitude'])])
    all_potholes = (all_potholes, df.index.tolist())

    with open('all_potholes.pkl', 'w') as f:
        pickle.dump(all_potholes, f)


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
    mpolys = MultiPolygon(polys)
    for hood in xrange(len(polys)):
        neighborhoods_tup.append((mpolys[hood],\
        neighborhood_index[hood]))

    # Associate each pothole with its df index
    # potholes_tup_list = []
    # for hole in xrange(df.shape[0]):
    #     potholes_tup_list.append((all_potholes[hole], df.index.tolist()[hole]))

    # Keep the potholes, indices that fall within the neighborhoods.
    # Keep the potholes, indices.

    # Pickle them for later usage.
    # city_holes_inds = []
    # city_holes = []
    # for hole in xrange(len(potholes_tup)):
    #     for hood in xrange(len(neighborhoods_tup)):
    #         if neighborhoods_tup[hood][0].contains(potholes_tup[hole][0]):
    #             city_holes.append(potholes_tup[hole][0])
    #             city_holes_inds.append(potholes_tup[hole][1])

    # Get potholes
    with open('all_potholes.pkl') as f:
        all_potholes = pickle.load(f)
    
    # Extract the neighborhood index associated with each pothole
    neighborhood_label = []
    for hole in xrange(df.shape[0]):
        found = False
        for hood in xrange(len(neighborhoods_tup)):
            # if neighborhoods_tup[hood][0].contains(potholes_tup[hole][0]):
            if neighborhoods_tup[hood][0].contains(all_potholes[0][hole]):
                neighborhood_label.append(neighborhoods_tup[hood][1])
                found = True
        if not found:
            neighborhood_label.append('')
    
    # Replace '' with NaNs
    df['neighborhood_label'] = df['neighborhood_label'].\
        convert_objects(convert_numeric=True)

    # Add labels to dataframe
    df['neighborhood_label'] = pd.Series(neighborhood_label,\
        index = all_potholes[1])

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

    # Get block group polys
    polys = [shape(pol['geometry']) for pol in shp]

    # Associate each block group polygon with its GEOID
    block_group_tup = []
    idx = 0
    mpolys = MultiPolygon(polys)
    for feature in shp:
        block_group_tup.append((mpolys[idx],\
        feature['properties']['GEOID']))
        idx += 1
    shp.close()

    # Get potholes
    with open('all_potholes.pkl') as f:
        all_potholes = pickle.load(f)

    # Extract the block group GEOID associated with each pothole
    block_group_label = []
    for hole in xrange(len(all_potholes[0])):
        found = False
        for group in xrange(len(block_group_tup)):
            if block_group_tup[group][0].contains(all_potholes[0][hole]):
                block_group_label.append(block_group_tup[group][1])
                found = True
        if not found:
            block_group_label.append('')

    # Add block group to dataframe
    df['GEOID'] = pd.Series(block_group_label,\
        index = all_potholes[1])
 
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

def get_closest_distance_features(df):
    '''
    INPUT: df
    OUTPUT: df
    Pass in the cleaned data as a dataframe and add a new column
    containing closest distance features based on a Seattle street
    network database.
    '''
    # Read in shapefile
    shapefilename = 'data/WGS84/Street_Network_Database'
    shp = fiona.open(shapefilename+'.shp')

    # Get street segments
    segs = [shape(seg['geometry']) for seg in shp]

    # Associate each feature with a list of the desired features
    street_feature_list = []
    for feature in shp:
        feature_list = [feature['properties']['SND_FEACOD']]
        feature_list.append(feature['properties']['ST_CODE'])
        feature_list.append(feature['properties']['SEGMENT_TY'])
        feature_list.append(feature['properties']['DIVIDED_CO'])
        feature_list.append(feature['properties']['VEHICLE_US'])
        street_feature_list.append(feature_list)
    shp.close()

    # Get potholes
    with open('all_potholes.pkl') as f:
        all_potholes = pickle.load(f)

    # Compute closest distance from pothole to street geom;
    # Associate the street geom features with the closest pothole
    street_features = []
    msegs = MultiLineString(segs)
    for hole in xrange(len(all_potholes[0])):
        found = False
        smallest_dist = 100.
        for street in xrange(len(msegs)):
            dist = all_potholes[0][hole].distance(msegs[street])
            if dist < smallest_dist:
                found = True
                smallest_dist = dist
                smallest_dist_street_feature = street_feature_list[street]
        street_features.append(smallest_dist_street_feature)
        if not found:   
            street_features.append([])

    # Add street geom features to dataframe
    df['SND_FEACOD'] = pd.Series([elem[0] for elem in street_features],\
        index = all_potholes[1])

    df['ST_CODE'] = pd.Series([elem[1] for elem in street_features],\
        index = all_potholes[1])

    df['SEGMENT_TY'] = pd.Series([elem[2] for elem in street_features],\
        index = all_potholes[1])

    df['DIVIDED_CO'] = pd.Series([elem[3] for elem in street_features],\
        index = all_potholes[1])

    df['VEHICLE_US'] = pd.Series([elem[4] for elem in street_features],\
        index = all_potholes[1])

    return df

def do_nlp_on_location(df):
	''''
    Do nlp on LOCATION field and add new column to df
	'''
	pass

if __name__ == '__main__':
    df = pd.read_pickle('df_1to7499_geo_cleaned.pkl')
    _get_potholes(df)
    df = create_distances(df)
    df = create_seasonality(df)
    df = get_neighborhoods(df)
    df = get_census_economic_vals(df)
    df = get_closest_distance_features(df)
    df.to_pickle('df_1to7499_features.pkl')
    print df.head()
    print df.tail(25)
    df.info()
    # print df[pd.isnull(df.neighborhood_label)]
    print df[df.neighborhood_label == ''].shape
    print df[df.GEOID == ''].shape


