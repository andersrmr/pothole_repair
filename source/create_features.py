import pandas as pd
import numpy as np
import fiona
from shapely.geometry import shape, Polygon, MultiPolygon, Point, MultiPoint

def get_neighborhoods(df):
    '''
    INPUT: df
    OUTPUT: df
    Pass in the cleaned data as a dataframe and add a new column
    containing the neighborhood the pothole belongs to
    '''
    # Read in shapefile
    shapefilename = '../sandbox/data/Neighborhoods'
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

    # Keep the potholes, indices that fall within the neighborhoods
    city_holes_inds = []
    city_holes = []
    for hole in xrange(len(potholes_tup)):
        for hood in xrange(len(neighborhoods_tup)):
            if neighborhoods_tup[hood][0].contains(potholes_tup[hole][0]):
                city_holes.append(potholes_tup[hole][0])
                city_holes_inds.append(potholes_tup[hole][1])

    #Extract the neighborhood index associated with each pothole
    neighborhood_label = []
    for hole in xrange(len(city_holes)):
        for hood in xrange(len(neighborhoods_tup)):
            if neighborhoods_tup[hood][0].contains(city_holes[hole]):
                neighborhood_label.append(neighborhoods_tup[hood][1])
    
    # Add labels to dataframe
    df['neighborhood_label'] = pd.Series(neighborhood_label,\
        index = city_holes_inds)

    return df

if __name__ == '__main__':
	df = pd.read_pickle('../sandbox/df_first757_cleaned.pkl')
	df = get_neighborhoods(df)
	print df.head()

