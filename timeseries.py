import streamlit as st
import pandas as pd
from datetime import datetime as dt
from matplotlib import pyplot as plt
import numpy as np
import pytz

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

log2.dtypes
st.write(log2.columns)
choice = st.selectbox("Choose Crossing", log2['name'].sort_values().unique())
filtered = log2[log2['name']== choice]
filtered

