from altair.vegalite.v4.schema.channels import Tooltip
from altair.vegalite.v4.schema.core import Projection
import streamlit as st
import pandas as pd
import numpy as np
from streamlit import util
import mongo_queries
from utility_cloud import get_local, return_color, make_coords
import altair as alt
import datetime as dt
from datetime import timedelta
from pandas.api.types import CategoricalDtype
import pydeck as pdk
import pytz

sites = mongo_queries.get_updating_list()
names = mongo_queries.ids_to_names(sites)
names = [i['name'] for i in names]
items = []




for n in names:
    items.append(" - "+n)

region_sel = st.sidebar.selectbox('Region',['All']+mongo_queries.get_regions())
district_sel = st.sidebar.selectbox('District',['All']+mongo_queries.get_district(region_sel))
port_choices = ['All']
if region_sel =='All' and district_sel == 'All':
    port_choices =['Currently being updated','All']
port_sel = st.sidebar.selectbox('Border Crossing',port_choices+mongo_queries.get_ports(region_sel,district_sel))

st.sidebar.markdown("""---""")
metric = st.sidebar.selectbox("Metric", ['Average','Maximum','Median'], index=0, key=None, help=None, on_change=None, args=None, kwargs=None)
timeframe = st.sidebar.selectbox("Timeframe", ['1 week','All Time','1 day', '1 month', '1 quarter', '1 year' ])




f={}
zoom=2
if region_sel !='All':
    zoom=5
    f.update({'region':region_sel})
if district_sel !='All':
    zoom=8
    f.update({'district':district_sel})
if port_sel !='All':
    if port_sel =='Currently being updated':
        f = {'id':{'$in':sites}}
        zoom=3
    else:
        zoom=10
        f.update({'name':port_sel})
f.update(mongo_queries.timeframe(timeframe))


data = mongo_queries.get_last_run_by_filter(f)
#catch empty data
if not data:
    st.write('No data available')
else:



    ####
    
    f.update(mongo_queries.timeframe(timeframe))
    st.write(f)
    hist = pd.DataFrame(mongo_queries.get_hist_data(f)) # get the data
    st.write(hist.dtypes)
    hist['utc'] = hist['utc'].dt.tz_localize('UTC')
    hist
    #hist['utc'] = hist['utc'].dt.to_pydatetime()
    #hist['local_time'] = hist.apply(get_local,axis=1) # convert UTC to local time
    
    alt_color = {'Maximum':'max(wait):Q', 'Average':'average(wait):Q','Median':'median(wait):Q'}
    hist['utc1'] = hist.utc.dt.tz_localize(None)
    hist
    st.write(dt.datetime.utcnow())
    st.write(dt.datetime.now())
    h = hist['utc'].iloc[0]
    st.write(hist['utc'].iloc[0],type(h))