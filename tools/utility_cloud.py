from datetime import datetime as dt
from datetime import timezone
from dateutil import tz


import pandas as pd
def get_local_one(utc,tzone):
    #utc = dt(utc)
    print(type(utc))
    print(utc)
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(tzone)
    utc = utc.replace(tzinfo=from_zone)
    
    lt = utc.astimezone(to_zone)
    return str(lt)
def get_local(row):
    
    
    utc = pd.to_datetime(row['utc'])
    tzone = row['timezone']
    # METHOD 1: Hardcode zones:
    from_zone = tz.gettz('UTC')
    
    to_zone = tz.gettz(tzone)
    
    #df['timestamp'].dt.tz_localize('utc').dt.tz_convert('US/Central')
    utc = utc.replace(tzinfo=from_zone)
    
    lt = utc.astimezone(to_zone)
    
    #lt=utc.tz_localize('utc').tz_convert(tz).isoformat()
    

    return str(lt)

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

def formatWait(wait):
    wait = int(wait)
    hours = 0
    minutes = 0
    if wait > 60:
        minutes = wait // 60
        wait -= minutes * 60
    if minutes > 60:
        hours = minutes // 60
        minutes -= hours * 60
    result = f'{hours}h ' if hours > 0 else ""
    if minutes > 0:
        result = result + str(minutes)+"m "
    if wait > 0:
        result = result + str(wait)+"s "
    return result