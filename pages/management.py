# Contents of ~/my_app/pages/page_2.py
from soupsieve import select
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from altair.vegalite.v4.schema.channels import Tooltip
from altair.vegalite.v4.schema.core import Projection
import altair as alt

import tools.mongo_queries as mongo_queries
from tools.utility_cloud import get_local, return_color, make_coords, get_local_one






########################################
#OLD METHOD
st.markdown("# Management Use Case")
st.sidebar.markdown("# Management Use Case")

sites = mongo_queries.get_current_updaters(False)

names = mongo_queries.ids_to_names(sites)
names = [i['name'] for i in names]
items = []
for n in names:
    items.append(" - "+n)


with st.form(key='manager'):

    region_sel = st.selectbox('Region',['All']+mongo_queries.get_regions())
    district_sel = st.selectbox('District',['All']+mongo_queries.get_district(region_sel))
    port_choices = ['All']
    if region_sel =='All' and district_sel == 'All':
        port_choices =['Currently being updated','All']
    port_sel = st.selectbox('Border Crossing',port_choices+mongo_queries.get_ports(region_sel,district_sel))


    metric = st.selectbox("Metric", ['Average','Maximum','Median'], index=0, key=None, help=None, on_change=None, args=None, kwargs=None)
    timeframe = st.selectbox("Timeframe", ['All Time','1 week','1 day', '1 month', '1 quarter', '1 year' ])
    refresh = st.form_submit_button('Get Data')
if refresh:
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
    
    #data = mongo_queries.get_last_run_by_filter(f) #deprecated
    
    data = mongo_queries.get_latest_times(f)
    
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
        r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}\nDelay: {wait} seconds"}, map_style = 'road')
        st.write("### Map")
        st.pydeck_chart(r)

        ####
        
        f.update(mongo_queries.timeframe(timeframe))
        
        hist = pd.DataFrame(mongo_queries.get_historical_data(f)) # get the data #update this
        
        #hist = pd.DataFrame(mongo_queries.get_hist_data(f)) # get the data #update this
        
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
        histo = alt.Chart(hist).transform_joinaggregate(
        total='count(*)'
        ).transform_calculate(
            pct='1 / datum.total'
        ).mark_bar().encode(
            alt.X('wait:Q', bin=True,title='Wait time (s)'),
            alt.Y('sum(pct):Q', axis=alt.Axis(format='%'), title='Percent of count')
        )

        # histo = alt.Chart(hist).mark_bar().encode(
        #     alt.X('wait:Q', bin=True),
        #     #y='count()',
        #     y=alt.Y('count():Q',stack=None),
        
        # )
        st.altair_chart(histo, use_container_width=True)
        ###
        f.update(mongo_queries.timeframe(timeframe))
        st.write("### Comparison to legacy system")
        f2 = f
        f2['id'] = 705
        pops = ['region', 'district', 'name']
        for p in pops:
            if p in f2.keys():
                f2.pop(p)
        
        ####
        data_comp = mongo_queries.legacy_versus_api(f2)

        
        versus = pd.DataFrame(data_comp)
 
        #versus['local_time'] = versus.apply(get_local,axis=1),
        
        

        
        
        versusChart = alt.Chart(versus).mark_line(point=True).encode(
            #alt.X('local_time:T'),
            alt.X('utc:T', title='Date'),
            alt.Y('wait:Q'),
            color='type',
            shape='name'
        ).interactive()
        
        st.altair_chart(versusChart, use_container_width=True)
