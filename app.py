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
#st.set_page_config(layout="wide")



    
    




def get_local_mongo(row):
    return mongo_queries.get_local_tz(row['crossing_id'])


db, collections = mongo_queries.mongo_setup()


filter = {}
#DOuglas 840
#Lacolle 351
#Remove Landsdowne 456
#Remove Windsor 452
sites = [427,440,602,351,453,840]
#filter.update({'crossing_id':{'$in':[427,440,602,452,453,456]}})

region_sel = st.sidebar.selectbox('Region',['All']+mongo_queries.get_regions())
district_sel = st.sidebar.selectbox('District',['All']+mongo_queries.get_district(region_sel))
port_sel = st.sidebar.selectbox('Border Crossing',['All']+mongo_queries.get_ports(region_sel,district_sel))
st.sidebar.markdown("""---""")
zoom=2
if region_sel !='All':
    filter.update({'region':region_sel})
    zoom=5
if district_sel !='All':
    filter.update({'district':district_sel})
    zoom=8
if port_sel !='All':
    filter.update({'name':port_sel})
    zoom=10



metric = st.sidebar.selectbox("Metric", ['Average','Maximum','Median'], index=0, key=None, help=None, on_change=None, args=None, kwargs=None)
timeframe = st.sidebar.selectbox("Timeframe", ['1 week','All Time','1 day', '1 month', '1 quarter', '1 year' ])

day_filter = mongo_queries.update_filter_timeframe(filter,timeframe)




def clicked():
    st.title("Border Wait Times")    
    day_filter2 = day_filter
    day_filter2.update({'crossing_id':{'$in':sites}})    
    df2 = pd.DataFrame(mongo_queries.new_vis_data(day_filter2))   
    df2['local_time'] = df2.apply(get_local,axis=1)    
    day_filter.update({'_id':{'$in':sites}})
    day_filter.pop('crossing_id', None)
    mini = pd.DataFrame(mongo_queries.map_df(day_filter))
    mini['local_time'] = mini.apply(get_local,axis=1)
    mini['color'] = mini.apply(return_color,axis=1)
    mini['lat'] = mini.lat.astype(str).astype(float)
    mini['long'] = mini.long.astype(str).astype(float)
    mini['coordinates'] = mini.apply(make_coords, axis=1)
    midpoint = (np.average(mini['lat']), np.average(mini['long']))
    cols=['name', 'wait', 'local_time']
    mini[cols].sort_values('local_time',ascending=False,inplace=True)
    #df2[cols]
    st.write("### Current wait times")
    mini[cols]
    layer = pdk.Layer(
        "ScatterplotLayer",
        mini,
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
    view_state = pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=zoom, bearing=0, pitch=0)
    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}\nDelay: {wait} seconds"})
    mini
    st.write("### Map")
    st.pydeck_chart(r)
    alt_color = {'Maximum':'max(wait):Q', 'Average':'average(wait):Q','Median':'median(wait):Q'}
    #df2 = run.aggregate() #agg func, filter on name, then find the TZ use this {'name':{'$in':mongo_queries.get_ports(region_sel,district_sel)}}
    #df2['local']
    #st.write(subset)
    df2
    histo = alt.Chart(df2).mark_bar().encode(
        alt.X('wait:Q', bin=True),
        #y='count()',
        y=alt.Y('count():Q',stack=None),
     
    )
    scatter = alt.Chart(df2).mark_rect().encode(
        alt.Y('hours(local_time):O', title='hour of day',),
        alt.X('day(local_time):O', title='Weekday'),        
        color=alt_color[metric]
    )
    st.write("### Schedule view")
    st.altair_chart(scatter, use_container_width=True)

    #df3 = pd.DataFrame(mongo_queries.new_vis_data(day_filter))
    #df3['local_time'] = df3.apply(get_local,axis=1)
    #df3
    st.write("### "+timeframe+' trend')
    one_day = alt.Chart(df2).mark_bar().encode(
        x='local_time:T',
        y=alt_color[metric]
    )
    st.altair_chart(one_day, use_container_width=True)
    st.write("### Distribution of wait times")
    st.altair_chart(histo, use_container_width=True)
    ################################################
    project = {
        'crossing_id':1,
        'utc':1,
        'wait':1,
        'name':1,
        'timezone':1,
        'type':1,
        'district':1,
        'region':1
    }
    day_filter.pop('_id')
    day_filter.update({'crossing_id':{'$in':sites}})
    legacy_data = db['legacy_mapped'].find(day_filter,projection=project)
    new_data = db['run_merge_vs'].find(day_filter,projection=project)
    test_df  =pd.DataFrame(legacy_data)
    other_df = pd.DataFrame(new_data)
    result = pd.concat([test_df,other_df])
    result['local_time'] = result.apply(get_local,axis=1)
    result
    versus = alt.Chart(result).mark_line(point=True).encode(
        alt.X('local_time:T'),
        alt.Y('wait:Q'),
        color='type',
        shape='name'
    )
    st.write("### Comparison to legacy system")
    st.altair_chart(versus, use_container_width=True)
btn = st.sidebar.button('Update',on_click=clicked)






################################################
############################################################################
#metdadata section
############################################################################
###TO DO 
#Collection info
#daily data info


with st.beta_expander("Metadata"):
    st.write("""
        How many calls to the API this month:
    """)
    st.write(str(mongo_queries.queries_this_month())+" of 15500")
    daily = pd.DataFrame(mongo_queries.totals_by_day())
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
