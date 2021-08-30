from numpy import isnan
from mongo_updater import get_columns
import os
from os.path import isfile, join
import pymongo
import datetime
import pandas as pd
from config import cluster_uri
import certifi
import sys
from bson.objectid import ObjectId

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
col= db['running']

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

def get_wait(t,b):
    if isnan(t) or isnan(b):
        return 0    
    return max(0,t-b)


# df = pd.DataFrame(col.find())

# for x in range(0,len(df)):
#     unique = str(df['_id'].iloc[x])
#     t = df['traffic'].iloc[x]
#     b = df['baseline'].iloc[x]
#     wait = int(get_wait(t,b))
#     update_val = {"$set":{"wait":wait}}
#     print(unique, wait)
#     col.find_one_and_update({"_id":ObjectId(unique)},update_val,upsert=True)

d = col.delete_many(filter = {"_id": {"$type": "string"}})
print(d.deleted_count)