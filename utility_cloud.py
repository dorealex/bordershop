from datetime import datetime as dt
import pandas as pd

def get_local(row):
    utc = row['utc']
    tz = row['timezone']
    #df['timestamp'].dt.tz_localize('utc').dt.tz_convert('US/Central')
    return utc.tz_localize('utc').tz_convert(tz)

def return_color(row):
    delay = row['wait']
    if 0<= delay < (3*60):
        return [0,255,000]
    elif (3*60)<=delay < (5*60):
        return [252, 186, 3]
    elif (5*60) <= delay:
        return [255,0,0]

def make_coords(row):
    
    lat = row['lat']
    lon = row['long']
    if type(lat) == str:
        lat = float(lat)
    if type(lon) == str:
        lon = float(lon)
    return (lon,lat)