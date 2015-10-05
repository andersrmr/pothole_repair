# pothole_repair
Predicting time to repair Seattle city potholes
=======


####Motivation

Recently, a neighbor expressed to me his opinion that the city government where we live could not be that great since the roads are so bad.  Reflecting on this, I began to wonder if data science could help us understand more about what influences the time required for potholes to be repaired.  This is likely to be of interest to a range of people, from ordinary citizens to cyclists to city leaders to data scientists. See this [link]  (http://www.slideshare.net/RichardAnderson47/predicting-pothole-repair-times-for-the-city-of-seattle) for a  slide deck presenting my results.

Here are the steps I followed in investigating this question:

#####Obtain Data

Data sources included the following:

* [Pothole data] (https://catalog.data.gov/dataset/pothole-repairs-eaf38)

* [Shapefiles of Seattle neighborhoods and street network features] (https://data.seattle.gov/dataset/data-seattle-gov-GIS-shapefile-datasets/f7tb-rnup)

* [U.S. Census data containing information on home values and incomes] (http://factfinder.census.gov/faces/nav/jsf/pages/index.xhtml)

* [Temperature and precipitation information from NOAA] (http://www.noaa.gov/)

After cleaning there were records for approximately 19,000 potholes spanning from 2010 to the download date in August, 2015.

#####Geocode Pothole Locations

Pothole locations were described only in general terms, e.g., lying on a particular street between that street's intersection with two other streets.  This necessitated a geocoding step, which was carried out using a geocoding web service provided via a google API and accessed through the Python module, geopy.

#####Engineering Features

A big part of this project was developing and engineering features I thought likely to explain variation in pothole repair times.  I extracted these features and associated them with the appropriate pothole. The list included the following:

* Colder temperatures could be correlated with more potholes and/or longer repair times.  I mapped to each pothole the average temperature on the pothole initialization date.

* Economic variables could influence variation in repair times.  I mapped median home values and household income aggregated at the census block group level to each pothole based on a 2009-2013 data.

* I used a closest distance calculation to associate to the closest pothole physical descriptions of street features such as segment type (e.g. alley or street), structure (e.g. elevated or below grade), and type of vehicle usage allowed.

* I computed the minimum distance from each pothole to prominent landmarks, e.g., the Convention Center, Pike Place market, and the Space Needle, on the possibility that distance from such location could influence repair time.

* I computed the total number of potholes active (i.e., unrepaired) in the system on any given day and associated it with the day each pothole was initiated.  

* I labelled each pothole with the Seattle neighborhood to which it belongs.

* I associated the number of months until the end of the fiscal year for the day on which each pothole was initiated.  The idea here was that end of fiscal year budgets and schedules could potentially influence repair times.

Several of these features were mapped to facilitate visual interrogation.

![hexbin](images/hexbin.png)
![chloropleth](images/chloropleth.png)

#####Modeling and Conclusions

I alternated exploratory data analysis with building a logistic regression and a random forest classifier.  The target variable was long vs short repair times with a threshhold of 3 days, the goal Seattle DOT has set for having all potholes repaired.  You could think of this as predicting whether or not the City of Seattle would keep its promise to its constituents.

Categorical variables such as labels of neighborhoods and street features alone resulted in an AUC score of only about 55%.  The random forest classifier improved AUC to 65%, with the 5 top important features, "cumulative number of potholes, "Median Home Value", "Temperature", "minimum distance to prominent features", and "months until end of FY".  Surprisingly, adding categorical variables to the random forest provided little further improvement in model performance.  Logistic regression found that temperature was not a statistically significant variable in the model, pointing to some underlying correlation among the features.  

The most interesting result, perhaps, was that median home value was positively correlated with repair times.  This seems unintuitive, raising the question of whether there might be a reporting bias in the dataset, where potholes are reported more frequently in higher income areas.  This would be something to follow up on in future work, along with the more general methodological challenge of figuirng out how to add to the model variables that are both independent and add the most information to the model.      

####Toolkits & Credits
 
* [Google API for Geocoding] (https://developers.google.com/maps/documentation/geocoding/intro)

* [geopy, client for popular geocoding web services] (https://pypi.python.org/pypi/geopy)

* [shapely, for maniulating geometric objects in the Cartesian plane] (https://pypi.python.org/pypi/Shapely)

* [fiona, for reading and writing from shapefiles] (https://github.com/Toblerity/Fiona)

* [Basemap, a matplotlib toolkit for plotting 2D data on maps in python.] (http://matplotlib.org/basemap/api/basemap_api.html)

* [descartes, for using geometric objecdts as matplotlib paths and patches] (https://pypi.python.org/pypi/descartes)

* [scikit-learn, a resource for Python machine learning libraries] (http://scikit-learn.org/stable/)

* Thanks to the team and instructors at Galvanize, as well as my classmates.
