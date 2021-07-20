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


log = pd.read_csv(log_file)
log['time']=log.apply(format_time, axis=1)
log['datetime'] = pd.to_datetime(log['date'] + ' ' + log['time'])
if "utc_time" not in log.columns:
    log['UTC'] = log.apply(utc_time,axis=1)
log = log.merge(tz_data[['id','timeZoneId']], on='id')
log['local time'] = log.apply(local_time,axis=1)
log['delay'] = log.apply(get_delay,axis=1)
cols = ['id','name', 'local time', 'delay']
log = log[cols]

log.dtypes
st.write(log.columns)
choice = st.selectbox("Choose Crossing", log['name'].sort_values().unique())
filtered = log[log['name']== choice]
filtered
fig, ax = plt.subplots()
fig = ax.hist(filtered['delay'],bins=24)
