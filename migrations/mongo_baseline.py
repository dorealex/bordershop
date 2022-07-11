import pymongo
import certifi
import pandas as pd
import json
import os


ca = certifi.where()

on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
else:
    from config import cluster_uri
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)

df = pd.read_csv("baseline.csv")
db = cluster['bordercross']
col= db['baseline']

records = json.loads(df.to_json(orient='records'))
col.insert_many(records)
