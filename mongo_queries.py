# Requires the PyMongo package.
# https://api.mongodb.com/python/current

###Gets the latest results, joins the specific data: coordinates, province, etc.
import datetime
from numpy import dtype
from datetime import datetime as dt, time
from datetime import timedelta
import os
import pymongo
import certifi

from datetime import timezone
import pytz

on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
else:
    import utility_func
    from config import cluster_uri
    ca = certifi.where()
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)

db = cluster['bordercross']
col= db['baseline']
run = db['running']
leg = db['legacy']
late = db['latest times']




latest_result = [
    {
        '$lookup': {
            'from': 'baseline', 
            'localField': '_id', 
            'foreignField': 'id', 
            'as': 'coords'
        }
    }, {
        '$project': {
            'id': 1, 
            'name': 1, 
            'wait': 1, 
            'utc': 1, 
            'coordinates': {
                '$arrayElemAt': [
                    '$coords.dest', 0
                ]
            }, 
            'province': {
                '$arrayElemAt': [
                    '$coords.province', 0
                ]
            }, 
            'timezone': {
                '$arrayElemAt': [
                    '$coords.timeZone', 0
                ]
            }
        }
    }, {
        '$addFields': {
            'coordinates': {
                '$split': [
                    '$coordinates', ','
                ]
            }
        }
    }, {
        '$addFields': {
            'lat': {
                '$arrayElemAt': [
                    '$coordinates', 0
                ]
            }, 
            'long': {
                '$arrayElemAt': [
                    '$coordinates', 1
                ]
            }
        }
    }, {
        '$project': {
            'id': 1, 
            'name': 1, 
            'province': 1, 
            'wait': 1, 
            'utc': 1, 
            'lat': {
                '$trim': {
                    'input': '$lat'
                }
            }, 
            'long': {
                '$trim': {
                    'input': '$long'
                }
            }, 
            'timezone': 1
        }
    }, {
        '$project': {
            'id': 1, 
            'name': 1, 
            'province': 1, 
            'wait': 1, 
            'utc': 1, 
            'lat': {
                '$toDecimal': '$lat'
            }, 
            'long': {
                '$toDecimal': '$long'
            }, 
            'timezone': 1
        }
    }
]

merge_running_timezones = [
    {
        '$lookup': {
            'from': 'baseline', 
            'localField': 'crossing_id', 
            'foreignField': 'id', 
            'as': 'timezone'
        }
    }, {
        '$project': {
            'id': '$crossing_id', 
            'name': 1, 
            'utc': 1, 
            'traffic': 1, 
            'baseline': 1, 
            'timezone': {
                '$arrayElemAt': [
                    '$timezone.timeZone', 0
                ]
            }
        }
    }
]

def add_one_log(r,id):
    traffic = utility_func.get_traffic_time(r.json())
    baseline = utility_func.get_baseline_time(r.json())
    wait = max(0,traffic-baseline)
    utc_time = dt.now(tz=timezone.utc)
    name = id['name']
    local_tz = pytz.timezone(id['timeZone'])
    day_strf = '%d-%b-%Y'
    time_strf = '%H_%M_%S'
    local_dt = datetime.datetime.now(local_tz)
    day_val = local_dt.strftime(day_strf)
    time_val = local_dt.strftime(time_strf)

    mydict = {"day":day_val, "time":time_val, "utc":utc_time, "crossing_id": id['id'], "name":name,"traffic":traffic,"baseline":baseline, "wait":wait,"local_tz":str(local_tz)}
    run.insert_one(mydict)
    #print(mydict)

def get_all_ids(poc = False):
    return list(col.find({'profile':1})) if poc else list(col.find({}))

def get_local_tz(filter):
    if type(filter) == str:
        return merge_running_timezones+[{'$match':{'name':filter}}]
    
    elif type(filter) == int:
        return merge_running_timezones+[{'$match':{'id':filter}}]

def get_last_run(crossing_id):
    #print(crossing_id)
    result = list(run.find({"crossing_id":crossing_id}).sort([("utc",-1)]).limit(1))
    if not result:
        return datetime.datetime(1,1,1,tzinfo=pytz.utc)
    else:
        return result[0]['utc'].replace(tzinfo=pytz.UTC)

def legacy_add(l):
    leg.insert_many(l)

if __name__ == '__main__':
    # print(get_all_ids())
    # print(len(get_all_ids()))
    #print(get_all_ids())
    pass