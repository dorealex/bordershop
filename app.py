from altair.vegalite.v4.schema.channels import Tooltip
import streamlit as st
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import pydeck as pdk
import os
from datetime import datetime as dt
from matplotlib import pyplot as plt
import pymongo
import pytz
import csv
import certifi
from datetime import datetime as dt
import mongo_queries
import altair as alt



on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
else:
    from config import cluster_uri
    ca = certifi.where()
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)

def get_local(row):
    utc = row['utc']
    tz = row['timezone']
    #df['timestamp'].dt.tz_localize('utc').dt.tz_convert('US/Central')
    return utc.tz_localize('utc').tz_convert(tz)
def make_coords(row):
    lat = row['lat']
    lon = row['long']
    return [lon,lat]

def get_wait(row):
    traf = row['traffic']
    base = row['baseline']
    delta = traf - base
    if delta <0:
        return 0
    else:
        return delta

def return_colour(row):
    delay = row['wait']
    if 0<= delay < (3*60):
        return [0,255,000]
    elif (3*60)<=delay < (5*60):
        return [252, 186, 3]
    elif (5*60) <= delay:
        return [255,0,0]


db = cluster['bordercross']
col= db['baseline']
run = db['running']
late = db['latest times']

st.title("Border Wait Times")
df = pd.DataFrame(late.aggregate(mongo_queries.latest_result))
df.sort_values(by="wait",ascending=False)
df['local time'] = df.apply(get_local,axis=1)
display_cols = ['name', 'province', 'wait', 'local time','utc']

df[display_cols]

df['color'] = df.apply(return_colour,axis=1)

df['lat'] = df.lat.astype(str).astype(float)

df['long'] = df.long.astype(str).astype(float)
df['coordinates'] = df.apply(make_coords, axis=1)
midpoint = (np.average(df['lat']), np.average(df['long']))

layer = pdk.Layer(
    "ScatterplotLayer",
    df,
    pickable=True,
    opacity=0.8,
    stroked=True,
    filled=True,
    radius_scale=6,
    radius_min_pixels=10,
    radius_max_pixels=100,
    line_width_min_pixels=1,
    get_position="coordinates",
    get_radius=15,
    get_fill_color='color',
    get_line_color=[0, 0, 0],
)
view_state = pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=3, bearing=0, pitch=0)

r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}\nDelay: {wait} seconds"})
st.pydeck_chart(r)

st.write("### Specific Crossing Info")
choice = st.selectbox("Choose Crossing", df['name'].sort_values().unique())

df2 = pd.DataFrame(list(run.aggregate(mongo_queries.get_local_tz(choice))))
df2['local_time'] = df2.apply(get_local,axis=1)
cols=['local_time', 'wait']
hist = df2[cols].sort_values(by='local_time', ascending=False)
st.write('#### Historical log')
day_filter = st.slider("Days to filter", min_value=0, max_value=None, value=7, step=1, format=None, key=None, help=None, on_change=None, args=None, kwargs=None)
hist= df2[df2.utc.dt.date>=dt.utcnow().date()-timedelta(days=day_filter)]

chart1 = alt.Chart(hist).mark_line().encode(
    x='local_time',
    y='wait',
    tooltip=['local_time', 'wait']
)

st.altair_chart(chart1+chart1.mark_point(size=50, opacity=0,tooltip=alt.TooltipContent("data")),use_container_width=True)
grp = df2.groupby(df2.local_time.dt.hour).wait.agg([('Average','mean'),('Max','max')])
hist = hist[['local_time','wait']].sort_values("local_time",ascending=False)
st.write("#### Summary Statistics for crossing during selected timeframe")
st.write(hist.describe())
#hist
st.write('#### Wait Time by Time of Day (local time)')
grp=grp.reset_index()
#st.line_chart(grp,use_container_width=True)

df2['frac'] = round((df2.local_time.dt.hour + df2.local_time.dt.minute/60)*6)/6

grp2 = df2.groupby(df2.frac).wait.agg([('Average','mean'),('Max','max')])

st.line_chart(grp2,use_container_width=True)