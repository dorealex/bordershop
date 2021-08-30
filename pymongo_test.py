from mongo_updater import get_columns
import os
from os.path import isfile, join
import pymongo
import datetime
import pandas as pd
from config import cluster_uri
import certifi
import sys
import numpy as np
ca = certifi.where()

on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
else:
    from config import cluster_uri
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)

db = cluster['bordercross']
col= db['baseline']
