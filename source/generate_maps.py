import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
import fiona
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch

def map_seattle():
    '''
    INPUT: None
    OUTPUT: None
    Generate maps for Seattle.
    '''
    df = pd.read_pickle('df_neighborhoods.pkl')

    shapefilename = 'data/Neighborhoods'
    shp = fiona.open(shapefilename+'.shp')
    coords = shp.bounds
    shp.close()

    w, h = coords[2] - coords[0], coords[3] - coords[1]
    extra = 0.01

    # Set up basemap as backdrop for neighborhoods
    m = Basemap(
        projection='tmerc', ellps='WGS84',\
        lon_0=np.mean([coords[0], coords[2]]),\
        lat_0=np.mean([coords[1], coords[3]]),\
        llcrnrlon=coords[0] - extra * w,\
        llcrnrlat=coords[1] - (extra * h),\
        urcrnrlon=coords[2] + extra * w,\
        urcrnrlat=coords[3] + (extra * h),\
        resolution='i',  suppress_ticks=True)

    _out = m.readshapefile(shapefilename, name='seattle',\
        drawbounds=False, color='none', zorder=2)

    # Set up a map dataframe
    df_map = pd.DataFrame({
        'poly': [Polygon(hood_points) for hood_points in m.seattle],
        'name': [hood['S_HOOD'] for hood in m.seattle_info]
    })

    # Convert our latitude and longitude into Basemap cartesian map coordinates
    mapped_points = [Point(m(mapped_x, mapped_y)) for mapped_x, mapped_y in\
        zip(df['longitude'], df['latitude'])]
    all_points = MultiPoint(mapped_points)

    # Use prep to optimize polygons for faster computation
    hood_polygons = prep(MultiPolygon(list(df_map['poly'].values)))

    # Filter out the points that do not fall within the map we're making
    city_points = filter(hood_polygons.contains, all_points)

