import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
import fiona
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
from matplotlib.colors import BoundaryNorm
from matplotlib.cm import ScalarMappable
from pysal.esda.mapclassify import Natural_Breaks

def custom_colorbar(cmap, ncolors, labels, **kwargs):    
    '''Create a custom, discretized colorbar with correctly formatted/aligned labels.
    
    cmap: the matplotlib colormap object you plan on using for your graph
    ncolors: (int) the number of discrete colors available
    labels: the list of labels for the colorbar. Should be the same length as ncolors.
    '''
    norm = BoundaryNorm(range(0, ncolors), cmap.N)
    mappable = ScalarMappable(cmap=cmap, norm=norm)
    mappable.set_array([])
    mappable.set_clim(-0.5, ncolors+0.5)
    colorbar = plt.colorbar(mappable, **kwargs)
    colorbar.set_ticks(np.linspace(0, ncolors, ncolors+1)+0.5)
    colorbar.set_ticklabels(range(0, ncolors))
    colorbar.set_ticklabels(labels)
    return colorbar

def prep_seattle_neighborhoods(df):
    '''
    INPUT: None
    OUTPUT: df, df, Basemap object, float, float, list, list
    Generate neighborhood basemap and city potholes for Seattle.
    '''
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

     # Convert latitude and longitude, into Basemap cartesian map coordinates
    mapped_points = [Point(m(mapped_x, mapped_y)) for mapped_x, mapped_y in\
        zip(df['longitude'], df['latitude'])]
    all_points = MultiPoint(mapped_points)

    # Use prep to optimize polygons for faster computation
    hood_polygons = prep(MultiPolygon(list(df_map['poly'].values)))

    # Filter out the points that do not fall within the map we're making
    city_points = filter(hood_polygons.contains, all_points)

    return df_map, m, h, w, coords, city_points

def chlor_map(df, df_map, m, h, w, coords, city_points):
    '''
    INPUT: df, df, Basemap object, float, float, list
    OUTPUT: None
    Generate chloropleth map
    '''
    # Chloropleth: No. of potholes in a neighborhood
    def num_of_contained_points(apolygon, city_points):
        return int(len(filter(prep(apolygon).contains, city_points)))

    df_map['hood_count'] = df_map['poly'].apply(num_of_contained_points,\
        args=(city_points,))

    # Use Natural_Breaks to calculate the breaks:
    breaks = Natural_Breaks(df_map[df_map['hood_count'] > 0].hood_count,\
        initial=300, k=3)
    df_map['jenks_bins'] = -1 #default value if no data exists for this bin
    df_map['jenks_bins'][df_map.hood_count > 0] = breaks.yb

    jenks_labels = ['No potholes here', "> 0 potholes"]\
        +["> %d potholes"%(perc) for perc in breaks.bins[:-1]]

    figwidth = 14
    fig = plt.figure(figsize=(figwidth, figwidth*h/w))
    ax = fig.add_subplot(111, axisbg='w', frame_on=False)

    cmap = plt.get_cmap('Blues')

    # draw neighborhoods with grey outlines
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(x, ec='#111111',\
        lw=.8, alpha=1., zorder=4))
    pc = PatchCollection(df_map['patches'], match_original=True)

    # apply custom color values onto the patch collection
    cmap_list = [cmap(val) for val in (df_map.jenks_bins.values \
        - df_map.jenks_bins.values.min())/(df_map.jenks_bins.values.max() \
        -float(df_map.jenks_bins.values.min()))]
    pc.set_facecolor(cmap_list)
    ax.add_collection(pc)

    #Draw a map scale
    m.drawmapscale(coords[0] + 0.08, coords[1] + -0.01,
        coords[0], coords[1], 10.,
        fontsize=16, barstyle='fancy', labelstyle='simple',
        fillcolor1='w', fillcolor2='#555555', fontcolor='#555555',
        zorder=5, ax=ax,)

    # ncolors+1 because I'm using a "zero-th" color
    cbar = custom_colorbar(cmap, ncolors=len(jenks_labels)+1, labels=jenks_labels,\
        shrink=0.5)
    cbar.ax.tick_params(labelsize=16)

    plt.show()

def hexbin_map(df, df_map, m, h, w, coords, city_points):
    '''
    PLOT A HEXBIN MAP OF LOCATION
    '''
    figwidth = 14
    fig = plt.figure(figsize=(figwidth, figwidth*h/w))
    ax = fig.add_subplot(111, axisbg='w', frame_on=False)

    # draw neighborhood patches from polygons
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='#555555', ec='#555555', lw=1, alpha=1, zorder=0))

    # plot neighborhoods by adding the PatchCollection to the axes instance
    ax.add_collection(PatchCollection(df_map['patches'].values, match_original=True))

    # The number of hexbins in the x-direction
    numhexbins = 50
    hx = m.hexbin(
    np.array([geom.x for geom in city_points]),
    np.array([geom.y for geom in city_points]),
    gridsize=(numhexbins, int(numhexbins*h/w)), #critical to get regular hexagon, must stretch to map dimensions
    bins='log', mincnt=1, edgecolor='none', alpha=1.,
    cmap=plt.get_cmap('Blues'))

    # Draw the patches again, but this time just their borders (to achieve borders over the hexbins)
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='none', ec='#FFFF99', lw=1, alpha=1, zorder=1))
    ax.add_collection(PatchCollection(df_map['patches'].values, match_original=True))

    # Draw a map scale
    m.drawmapscale(coords[0] + 0.05, coords[1] - 0.01,
        coords[0], coords[1], 4.,
        units='mi', barstyle='fancy', labelstyle='simple',
        fillcolor1='w', fillcolor2='#555555', fontcolor='#555555',
        zorder=5)

    plt.show()

def bubble_map(df, df_map, m, h, w):
    '''
    PLOT A BUBBLE PLOT of pothole repair times
    '''
    figwidth = 14
    fig = plt.figure(figsize=(figwidth, figwidth*h/w))
    ax = fig.add_subplot(111, axisbg='w', frame_on=False)

    # draw neighborhood patches from polygons
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='#555555', ec='#555555', lw=1, alpha=1, zorder=0))

    # plot neighborhoods by adding the PatchCollection to the axes instance
    ax.add_collection(PatchCollection(df_map['patches'].values, match_original=True))

    # sizes = [x*10 for x in df_95['DURATION_td'].tolist()]
    sizes = 200
    color = [x*5 for x in df['DURATION_td'].tolist()]

    # Convert our latitude and longitude into Basemap cartesian map coordinates
    xcart, ycart = m(df['longitude'].tolist(), df['latitude'].tolist())

    # m.scatter(xcart, ycart, s=sizes, marker='o',color='lime', alpha=0.5)
    m.scatter(xcart, ycart, s=sizes, marker='o',c=color, alpha=0.5)

    # Draw the patches again, but this time just their borders
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='none', ec='#FFFF99', lw=1, alpha=1, zorder=1))
    ax.add_collection(PatchCollection(df_map['patches'].values, match_original=True))

    plt.show()

def map_econ_value(df, df_map, m, h, w):
    '''
    Plot econ values
    '''
    figwidth = 14
    fig = plt.figure(figsize=(figwidth, figwidth*h/w))
    ax = fig.add_subplot(111, axisbg='w', frame_on=False)

    # draw neighborhood patches from polygons
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='#555555', ec='#555555', lw=1, alpha=1, zorder=0))

    # plot neighborhoods by adding the PatchCollection to the axes instance
    ax.add_collection(PatchCollection(df_map['patches'].values, match_original=True))

    # sizes = [x*.001 for x in df_95['Median_Home_Value'].tolist()]
    sizes = 100
    color = [x*5 for x in df['Median_Home_Value'].tolist()]

    # Convert our latitude and longitude into Basemap cartesian map coordinates
    xcart, ycart = m(df['longitude'].tolist(), df['latitude'].tolist()) 

    # m.scatter(xcart, ycart, s=sizes, marker='o',color='darkred', alpha=0.5)
    m.scatter(xcart, ycart, s=sizes, marker='o',c=color, alpha=0.5)

    # Draw the patches again, but this time just their borders (to achieve borders over the hexbins)
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='none', ec='#FFFF99', lw=1, alpha=1, zorder=1))
    ax.add_collection(PatchCollection(df_map['patches'].values, match_original=True))

    plt.show()

def main():
    df = pd.read_pickle('df_95_features.pkl')
    df_map, m, h, w, coords, city_points = prep_seattle_neighborhoods(df)
    chlor_map(df, df_map, m, h, w, coords, city_points)
    hexbin_map(df, df_map, m, h, w, coords, city_points)
    bubble_map(df, df_map, m, h, w)
    map_econ_value(df, df_map, m, h, w)

if __name__ == '__main__':
    main()
    

