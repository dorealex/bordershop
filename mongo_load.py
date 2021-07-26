import os
import json
import pandas as pd
import pymongo
import datetime
import pytz

# df = pd.read_csv("crossings.csv")

# print(df.head(2).to_dict('records'))


cluster = pymongo.MongoClient("mongodb+srv://dorea:philo@tyche.tndz8.mongodb.net/test?retryWrites=true&w=majority")
db = cluster['bordercross']
col = db['log']
# doc = df.to_dict('records')
# col.insert_many(doc)


from os import listdir
from os.path import isfile, join
onlyfiles = [f for f in listdir("data") if isfile(join("data", f))]
load_list=[]
for x in onlyfiles:
    fname = x[:-5]
    ext = x.split(".")[-1]
    if ext == 'json':
        items = fname.split("-")
        print("Items is this long", len(items), items)
        border_id = int(items[0])
        crossing_name = "-".join(items[1:-2]).replace("_"," ")
        crossing_name = " ".join(crossing_name.split())
        EDT_date = datetime.datetime.strptime(items[-2],"%m_%d_%y" )
        EDT_time = datetime.datetime.strptime(items[-1],"%H_%M_%S")
        EDT_datetime = datetime.datetime.combine(EDT_date,EDT_time.time())
        tz = pytz.timezone("Canada/Eastern")
        local_time = tz.localize(EDT_datetime)
        
        epoch = local_time.timestamp()
        with open(join("data",x)) as json_file:
            my_dict = json.load(json_file)
        my_dict['border_id'] = border_id
        my_dict['crossing_name'] = crossing_name
        my_dict['timestamp'] = epoch
        my_dict['utc_time'] = local_time.astimezone(pytz.UTC)
        load_list.append(my_dict)
        #col.insert(my_dict)
col.insert_many(load_list)
