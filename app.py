import streamlit as st
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import pydeck as pdk

from datetime import datetime as dt
from matplotlib import pyplot as plt

import pytz

st.title("Border Wait Times Visualisation")
def wait_seconds(row):
    return max([0,row['traffic']-row['baseline']])

def wait_factor(row):
    base = row['baseline']
    traffic  =row['traffic']

    delta = traffic - base
    delta = max([0,delta])
    if delta <=0:
        return "None"
    elif delta < 60:
        return "Less than 1 minute"
    else:
        return str(round(delta/60))+" minutes"

def make_coords(row):
    lat = row['lat']
    lon = row['lon']
    return [lon,lat]

def return_colour(row):
    delay = row['delay']
    if 0<= delay < (3*60):
        return [0,255,000]
    elif (3*60)<=delay < (5*60):
        return [252, 186, 3]
    elif (5*60) <= delay:
        return [255,0,0]

def format_time(row):
    return str(row['time']).replace("_",":")
    

def utc_time(row):
    utc=pytz.timezone('UTC')
    date_time=row['datetime']
    return dt.astimezone(date_time,utc)
def get_delay(row):
    return max(0,row['traffic']-row['baseline'])


def local_time(row):
    sel = pytz.timezone(row['timeZoneId'])
    return dt.astimezone(row['UTC'],sel)
log_file = 'log.csv'
tz_data = pd.read_csv("tz_data.csv")






df = pd.read_csv('baseline.csv')
df[['lat','lon']] = df['dest'].str.split(',',expand=True)
df['lat'].astype(float)
df['lon'].astype(float)
#df['wait times'] = df.apply(wait_factor,axis=1)
#df['wait(s)'] = df.apply(wait_seconds, axis=1)
cols=['id', 'name', 'province','baseline']
display = df[cols]

log = pd.read_csv('log.csv')


log['datetime'] = log['date']+" "+log['time']
log['datetime'] = pd.to_datetime(log['datetime'], format='%d-%b-%Y %H_%M_%S')
log['delay'] = log.apply(wait_seconds,axis=1)
log['wait_times'] = log.apply(wait_factor,axis=1)
cols=['datetime', 'id', 'name', 'delay','wait_times']

sorted = log[cols].sort_values('datetime')
result = sorted.drop_duplicates('id', keep='last')


df.set_index('id')
result.set_index('id')
final = pd.merge(df, result)


final['lat'] = final['lat'].astype(float)
final['lon'] = final['lon'].astype(float)
final['coordinates'] = final.apply(make_coords, axis=1)
final['color'] = final.apply(return_colour,axis=1)
midpoint = (np.average(final['lat']), np.average(final['lon']))

#st.write(midpoint)



#st.map(final)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=final,
    pickable=True,
    opacity=0.8,
    stroked=True,
    filled=True,
    
    radius_min_pixels=10,
    radius_max_pixels=100,
    line_width_min_pixels=1,
    get_position='coordinates',
    get_radius='delay',
    get_weight='delay',
    get_fill_color='color',
    get_line_color=[0, 0, 0],
)

view_state = pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=3, bearing=0, pitch=0)

r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{id} {name}\nDelay: {wait_times}"})
st.pydeck_chart(r)
display_cols=['name','province','wait_times','datetime','delay' ]
final = final.sort_values("delay", ascending=False)
final = final[display_cols]
final

log2 = pd.read_csv(log_file)
log2['time']=log2.apply(format_time, axis=1)
log2['datetime'] = pd.to_datetime(log2['date'] + ' ' + log2['time'])
if "utc_time" not in log2.columns:
    log2['UTC'] = log2.apply(utc_time,axis=1)
log2 = log2.merge(tz_data[['id','timeZoneId']], on='id')
log2['local time'] = log2.apply(local_time,axis=1)
log2['delay'] = log2.apply(get_delay,axis=1)
cols = ['id','name', 'local time', 'delay']
log2 = log2[cols]
st.write("### Specific Crossing Info")
choice = st.selectbox("Choose Crossing", log2['name'].sort_values().unique())
filtered = log2[log2['name']== choice]
filtered[['local time', 'delay']]