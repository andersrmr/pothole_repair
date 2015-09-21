import pandas as pd
import numpy as np

def clean_data():
    
    df = pd.read_csv('data/Pothole_Repairs_Seattle.csv')

def do_geocoding():

    pass

if __name__ == '__main__':
    df = pd.read_pickle('../sandbox/df_first757_cleaned.pkl')
    # df = get_neighborhoods(df)
    # df = get_census_economic_vals(df)
    # df = create_distances(df)
    df = create_seasonality(df)
    print df.head(25)
