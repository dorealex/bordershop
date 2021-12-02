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


def create_time_box(start,finish,field_name='utc'):
    q = {"wait_times."+field_name:{'$gt':start,'$lte':finish}}
    return {'$match':q}

def main():
    key_date = dt.datetime(2021,11,8)
    kd = st.date_input('Key Date', key_date)
    kd = dt.datetime.combine(kd,dt.datetime.min.time())

    metric = st.selectbox("Metric", ['Average','Maximum','Median'], index=0, key=None, help=None, on_change=None, args=None, kwargs=None)
    plusmin = st.number_input('Plus/Minus (days)',1,365,7,1)
    sites = mongo_queries.get_updating_list()

    kd1 = key_date - timedelta(days=plusmin)
    kd2 = key_date + timedelta(days=plusmin)

    col = mongo_queries.col

    start =[{
            '$match': {
                'id': {
                    '$in': sites
                }
            }
        }, {
            '$project': {
                'wait_times': 1,
                'timezone':'$timeZone'
            }
        }, {
            '$unwind': {
                'path': '$wait_times'
            }
        }]
    tail = {'$project': {
                'utc': '$wait_times.utc',
                'timezone':1, 
                'wait': '$wait_times.wait', 
                '_id': 0
            }}
    q1 = start + [create_time_box(kd1,kd)] + [tail] + [{'$project':{'utc':1,'wait':1,'period':'before','timezone':1}}]


    data1 = list(col.aggregate(q1))
    q2 = start + [create_time_box(kd,kd2)] + [tail] + [{'$project':{'utc':1,'wait':1,'period':'after','timezone':1}}]
    data2 = list(col.aggregate(q2))


    df1 = pd.DataFrame(data1)

    df1['local_time'] = df1.apply(get_local,axis=1)
    alt_color = {'Maximum':'max(wait):Q', 'Average':'average(wait):Q','Median':'median(wait):Q'}

    df2 = pd.DataFrame(data2)

    df2['local_time'] = df2.apply(get_local,axis=1)

    df3 = pd.concat([df1,df2])


    line = alt.Chart(df3).mark_line().encode(
        alt.X('hours(local_time):O', title='Hour'),
        alt.Y('average(wait):Q',title='Wait (s)'),
        alt.Row('day(local_time):O',title='Weekday'),
        color = 'period',
        
        
    )
    st.altair_chart(line,use_container_width=True)

    scatter = alt.Chart(df3).mark_rect().encode(
        alt.Y('hours(local_time):O', title='hour of day',),
        alt.X('day(local_time):O', title='Weekday'),
        alt.Row('period',title='Before/After',sort='descending'),
        alt.Tooltip(alt_color[metric]),        
        color=alt_color[metric],
        
    )
    st.altair_chart(scatter, use_container_width=True)

main()