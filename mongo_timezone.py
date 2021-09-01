import pymongo
import certifi
import pandas as pd
import json
import os
import pprint

ca = certifi.where()

on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
else:
    from config import cluster_uri
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)

df = pd.read_csv("tz_data.csv")
db = cluster['bordercross']
col= db['baseline']

#records = json.loads(df.to_json(orient='records'))
#col.insert_many(records)

print(col.find({"id":817})[0])

for x in range(len(df)):
    id = int(df['id'].iloc[x])
    tz = df['timeZoneId'].iloc[x]
    query = {"id":id}
    update_val = {"$set":{"timeZone":tz}}
    col.find_one_and_update(query,update_val)
