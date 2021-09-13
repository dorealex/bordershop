import mongo_queries
import json
import pandas as pd

df = pd.read_csv('legacy_map.csv')

db, collections = mongo_queries.mongo_setup()
mydict = df.to_dict(orient='records')
leg_map = db['leg_map']

leg_map.insert_many(mydict)

