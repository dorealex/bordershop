from numpy.core import numeric
import streamlit as st
import pymongo
import pandas as pd
from config import cluster_uri
import certifi
import numpy
import os
from datetime import datetime as dt
ca = certifi.where()
import numpy as np

on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
else:
    from config import cluster_uri
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)

db = cluster['bordercross']
col= db['running']

df = pd.DataFrame(col.find())
df

# df2 = df.groupby('name').agg(Mean=('wait', 'mean'), Sum=('wait', 'sum'), Max=('wait','max'))
# st.write(df2.columns)
# df3 = df2.sort_values("Max",ascending=False).tail(42)
# df3
# st.write(df3.index.tolist())

# st.write(type(df['crossing_id'].iloc[22])==numpy.int64)

hist_values = np.histogram(df['utc'].dt.hour, bins=24, range=(0,24))[0]
st.bar_chart(hist_values)