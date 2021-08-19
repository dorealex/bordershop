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

on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
else:
    from config import cluster_uri

cluster = pymongo.MongoClient(cluster_uri)
db = cluster['bordercross']
col= db['running']

print(db.list_collection_names())