from altair.vegalite.v4.schema.channels import Tooltip
from altair.vegalite.v4.schema.core import Projection
import streamlit as st
import pandas as pd
import numpy as np
from streamlit import util
import mongo_queries
from utility_cloud import get_local, return_color, make_coords, get_local_one
import altair as alt
import datetime as dt
from datetime import timedelta
from pandas.api.types import CategoricalDtype
import pydeck as pdk
from pathlib import Path

import pytz

def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

test_dict = [
  {
    "crossing name": "St-Bernard-de-Lacolle: Highway 15",
    "province": "QC",
    "id": 351,
    "timezone": "America/New_York",
    "est. arrival at border (utc)": dt.datetime(2021, 12, 4, 6, 36, 52),
    "est. wait at border (s)": 49.75,
    "total driving time": 647.4163888888888,
    "total driving distance": 2330.699,
    "route name": "I-95 N"
  },
  {
    "crossing name": "Landsdowne (Thousand Islands Bridge)",
    "province": "ON",
    "id": 456,
    "timezone": "America/New_York",
    "est. arrival at border (utc)": dt.datetime(2021, 12, 4, 5, 32, 47),
    "est. wait at border (s)": 10,
    "total driving time": 656.4591666666666,
    "total driving distance": 2363.253,
    "route name": "I-95 N and I-81 N"
  },
  {
    "crossing name": "Landsdowne (Thousand Islands Bridge)",
    "province": "ON",
    "id": 456,
    "timezone": "America/New_York",
    "est. arrival at border (utc)": dt.datetime(2021, 12, 4, 7, 18, 18),
    "est. wait at border (s)": 1.8125,
    "total driving time": 703.195,
    "total driving distance": 2531.502,
    "route name": "I-95 N and I-77 N"
  }
]


sites = mongo_queries.get_updating_list()
names = mongo_queries.ids_to_names(sites)
names = [i['name'] for i in names]
items = []
def formatWait(wait):
    wait = int(wait)
    hours = 0
    minutes = 0 
    if wait > 60:
        minutes = wait // 60
        wait = wait - (minutes * 60)
    if minutes > 60:
        hours = minutes // 60
        minutes = minutes - (hours * 60)
    result = ""
    if hours > 0:
        result = str(hours)+"h "
    if minutes > 0:
        result = result + str(minutes)+"m "
    if wait > 0:
        result = result + str(wait)+"s "
    return result
def writeRoute(route):
    name = route['crossing name']   #1
    prov = route['province']            #2
    utc_arriv = route['est. arrival at border (utc)']
    wait = route['est. wait at border (s)'] #3
    routeName = route['route name'] #4
    timezone = route['timezone']    #5
    local_arrive = get_local_one(utc_arriv, timezone)
    cols = st.columns(5)
    cols[0].write('**Route**')
    cols[0].write(routeName)
    cols[1].write('**Crossing Name**')
    cols[1].write(name)
    cols[2].write('**Province**')
    cols[2].write(prov)
    cols[3].write('**Est. Arrival Time (Local Time)**')
    cols[3].write(local_arrive)
    cols[4].write('**Est. Wait**')
    cols[4].write(formatWait(wait))
    st.write('-----')

for n in names:
    items.append(" - "+n)





st.title("Border Wait Times")
st.markdown("The current ports being polled by the API:\n"+"\n".join(items))
with st.expander('User: Management'):
    region_sel = st.selectbox('Region',['All']+mongo_queries.get_regions())
    district_sel = st.selectbox('District',['All']+mongo_queries.get_district(region_sel))
    port_choices = ['All']
    if region_sel =='All' and district_sel == 'All':
        port_choices =['Currently being updated','All']
    port_sel = st.selectbox('Border Crossing',port_choices+mongo_queries.get_ports(region_sel,district_sel))


    metric = st.selectbox("Metric", ['Average','Maximum','Median'], index=0, key=None, help=None, on_change=None, args=None, kwargs=None)
    timeframe = st.selectbox("Timeframe", ['1 week','All Time','1 day', '1 month', '1 quarter', '1 year' ])
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

        df = pd.DataFrame(data)
        
        
        df['local_time'] = df.apply(get_local,axis=1)
        df['color'] = df.apply(return_color,axis=1)
        df[['lat','long']] = df['dest'].str.split(', ',expand=True)
        pd.to_numeric(df['lat'],errors='coerce')
        pd.to_numeric(df['long'],errors='coerce')
        df.lat.astype(str).astype(float)
        df.long.astype(str).astype(float)
        df['coordinates'] = df.apply(make_coords,axis=1)
        mid_lat = (np.max(df['lat'].astype(float)) + np.min(df['lat'].astype(float)))/2
        mid_long = (np.max(df['long'].astype(float)) + np.min(df['long'].astype(float)))/2

        midpoint = (mid_lat,mid_long)
        #midpoint = (np.average(df['lat'].astype(float)), np.average(df['long'].astype(float)))

        cols=['name', 'wait', 'local_time']
        df[cols]
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
            get_position='coordinates',
            get_radius=15,
            get_fill_color='color',
            get_line_color=[0, 0, 0],
        )
        view_state = pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=zoom, bearing=0, pitch=0)
        r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}\nDelay: {wait} seconds"})
        st.write("### Map")
        st.pydeck_chart(r)

        ####
        
        f.update(mongo_queries.timeframe(timeframe))
        
        hist = pd.DataFrame(mongo_queries.get_hist_data(f)) # get the data
        hist['utc'] = hist['utc'].dt.tz_localize('UTC')
        hist['local_time'] = hist.apply(get_local,axis=1) # convert UTC to local time
        
        alt_color = {'Maximum':'max(wait):Q', 'Average':'average(wait):Q','Median':'median(wait):Q'}
        
        st.write('### Schedule View')
        scatter = alt.Chart(hist).mark_rect().encode(
            alt.Y('hours(local_time):O', title='hour of day',),
            alt.X('day(local_time):O', title='Weekday'),        
            alt.Tooltip(['hours(local_time):O','day(local_time):O',alt_color[metric]]),
            color=alt_color[metric],
            
        ).interactive()
        st.altair_chart(scatter, use_container_width=True)
        ####
        st.write('### Trend ('+timeframe+')')
        one_day = alt.Chart(hist).mark_bar().encode(
            x='local_time:T',
            y=alt_color[metric]
        )
        st.altair_chart(one_day, use_container_width=True)

        ####
        st.write('### Distribution')
        histo = alt.Chart(hist).mark_bar().encode(
            alt.X('wait:Q', bin=True),
            #y='count()',
            y=alt.Y('count():Q',stack=None),
        
        )
        st.altair_chart(histo, use_container_width=True)
        ####
        # f.update(mongo_queries.timeframe(timeframe))
        # st.write("### Comparison to legacy system")
        # ####
        # versus = pd.DataFrame(mongo_queries.prepare_legacy_compare(f))
        # #versus['local_time'] = versus.apply(get_local,axis=1),
        # versusChart = alt.Chart(versus).mark_line(point=True).encode(
        #     #alt.X('local_time:T'),
        #     alt.X('utc:T'),
        #     alt.Y('wait:Q'),
        #     color='type',
        #     shape='name'
        # )
        
        # st.altair_chart(versusChart, use_container_width=True)

with st.expander('User: Traveller'):
    st.write("## Travellers BWT Example")
    st.write('#### Note, each run of this is an API call to Google.')
    gmaps = mongo_queries.gmaps
    col = mongo_queries.col
    use = st.checkbox('Use my current location')
    if not use:
        start = st.text_input('Start location','Orlando, FL')
    stop = st.text_input('Destination in Canada','Laval, QC')
    tcol = st.columns(2)
    when = tcol[0].date_input('When are you leaving?',dt.datetime.now())
    time = tcol[1].time_input('Time?', dt.datetime.now())
    submit = st.button('Estimate')
    dtime = dt.datetime.combine(when,time)
    if submit:
        if use:
            loc = gmaps.geolocate()['location']        
        else:
            loc = gmaps.geocode(start)[0]['geometry']['location']
        dep_tz = gmaps.timezone(loc)['timeZoneId']        
        dtime = dtime.astimezone(pytz.timezone(dep_tz))        
        st.components.v1.iframe(mongo_queries.mapmaker(start = loc, dest =stop,key=mongo_queries.api_key),height=400)
        routeinfo = mongo_queries.get_trip_wait(loc,stop,dtime)
        #routeinfo = test_dict
        #df = pd.DataFrame(routeinfo)
        
        for r in routeinfo:        
            writeRoute(r)
with st.expander('Details'):
    md = read_markdown_file("info.md")
    st.markdown(md)
with st.expander("Metadata"):
    st.write("""
        How many calls to the API this month:
    """)
    st.write(str(mongo_queries.queries_this_month())+" of 15500")
    daily = pd.DataFrame(mongo_queries.totals_by_day())###TODO this will need to change
    daily.rename(columns={"_id":"day", "count":"count"}, inplace=True)
    
    daily['day'] = pd.to_datetime(daily['day'])
    
    
    daily = daily.groupby('day')['count'].sum()
    daily = daily.groupby(daily.index.month).cumsum().reset_index()
    daily['month'] = daily['day'].dt.month
    daily['day'] = daily['day'].dt.date
    #daily
    chart2 = alt.Chart(daily).mark_bar().encode(
        alt.X('day:O', title='Day (UTC)'),   
        y='count',
        color=alt.Color('month', legend=None)
    )
    #st.write(daily.dtypes)
    st.altair_chart(chart2, use_container_width=True)
