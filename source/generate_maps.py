import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
import fiona
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
from pysal.esda.mapclassify import Natural_Breaks

def custom_colorbar(cmap, ncolors, labels, **kwargs):    
    '''Create a custom, discretized colorbar with correctly formatted/aligned labels.
    
    cmap: the matplotlib colormap object you plan on using for your graph
    ncolors: (int) the number of discrete colors available
    labels: the list of labels for the colorbar. Should be the same length as ncolors.
    '''
    from matplotlib.colors import BoundaryNorm
    from matplotlib.cm import ScalarMappable
        
    norm = BoundaryNorm(range(0, ncolors), cmap.N)
    mappable = ScalarMappable(cmap=cmap, norm=norm)
    mappable.set_array([])
    mappable.set_clim(-0.5, ncolors+0.5)
    colorbar = plt.colorbar(mappable, **kwargs)
    colorbar.set_ticks(np.linspace(0, ncolors, ncolors+1)+0.5)
    colorbar.set_ticklabels(range(0, ncolors))
    colorbar.set_ticklabels(labels)
    return colorbar

def map_seattle():
    '''
    INPUT: None
    OUTPUT: None
    Generate maps for Seattle.
    '''
    df = pd.read_pickle('df_1to6999_geo_cleaned.pkl')

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

    # apply our custom color values onto the patch collection
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

	# ncolors+1 because we're using a "zero-th" color
	cbar = custom_colorbar(cmap, ncolors=len(jenks_labels)+1, labels=jenks_labels,\
	    shrink=0.5)
	cbar.ax.tick_params(labelsize=16)

# fig.suptitle("Time Spent in Seattle Neighborhoods", fontdict={'size':24, 'fontweight':'bold'}, y=0.92)
# ax.set_title("Using location data collected from my Android phone via Google Takeout", fontsize=14, y=0.98)
# ax.text(1.35, 0.04, "Collected from 2012-2014 on Android 4.2-4.4\nGeographic data provided by data.seattle.gov", 
#     ha='right', color='#555555', style='italic', transform=ax.transAxes)
# ax.text(1.35, 0.01, "BeneathData.com", color='#555555', fontsize=16, ha='right', transform=ax.transAxes)

plt.savefig('chloropleth.png', dpi=100, frameon=False, bbox_inches='tight',\
    pad_inches=0.5, facecolor='#F2F2F2')
