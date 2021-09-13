# Requires the PyMongo package.
# https://api.mongodb.com/python/current

###Gets the latest results, joins the specific data: coordinates, province, etc.
import datetime
from altair.vegalite.v4.schema.core import Projection
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
merge = db['running_merge']
lm = db['latest_merged']

def map_pipeline():
    pipeline = [{
        '$group': {
            '_id': '$crossing_id', 
            'name': {'$last': '$name'}, 
            'utc': {'$last': '$utc'}, 
            'district': {'$last': '$district'}, 
            'region': {'$last': '$region'}, 
            'lat': {'$last': '$lat'}, 
            'long': {'$last': '$long'}, 
            'wait': {'$last': '$wait'}
        }
    }]
    return merge.aggregate(pipeline)


def get_all_run_with_tz_latest():
    query = [
        {
            '$sort': {
                'utc': -1
            }
        }, {
            '$lookup': {
                'from': 'baseline', 
                'localField': 'crossing_id', 
                'foreignField': 'id', 
                'as': 'string'
            }
        }, {
            '$project': {
                '_id': 1, 
                'crossing_id': 1, 
                'name': 1, 
                'wait': 1, 
                'utc': 1, 
                'province': {
                    '$arrayElemAt': [
                        '$string.province', 0
                    ]
                }, 
                'dest': {
                    '$arrayElemAt': [
                        '$string.dest', 0
                    ]
                }, 
                'timezone': {
                    '$arrayElemAt': [
                        '$string.timeZone', 0
                    ]
                }
            }
        }, {
            '$addFields': {
                'coords': {
                    '$split': [
                        '$dest', ','
                    ]
                }
            }
        }, {
            '$addFields': {
                'lat': {
                    '$arrayElemAt': [
                        '$coords', 0
                    ]
                }, 
                'long': {
                    '$arrayElemAt': [
                        '$coords', 1
                    ]
                }
            }
        }, {
            '$project': {
                '_id': 1, 
                'crossing_id': 1, 
                'name': 1, 
                'wait': 1, 
                'province': 1, 
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
                '_id': 1, 
                'crossing_id': 1, 
                'name': 1, 
                'wait': 1, 
                'utc': 1, 
                'province': 1, 
                'timezone': 1, 
                'lat': {
                    '$toDecimal': '$lat'
                }, 
                'long': {
                    '$toDecimal': '$long'
                }
            }
        }, {
            '$group': {
                '_id': '$crossing_id', 
                'name': {
                    '$first': '$name'
                }, 
                'wait': {
                    '$first': '$wait'
                }, 
                'province': {
                    '$first': '$province'
                }, 
                'timezone': {
                    '$first': '$timezone'
                }, 
                'lat': {
                    '$first': '$lat'
                }, 
                'long': {
                    '$first': '$long'
                }, 
                'utc': {
                    '$first': '$utc'
                }
            }
        }, {
            '$sort': {
                'name': 1
            }
        }
    ]
    return run.aggregate(query)
def baseline_info(query={},req={}):
    return col.find(query,projection=req)

def get_run_with_query(query={}):
    return run.find(query)

def get_all_run_with_tz():
    query = [
        {
            '$lookup': {
                'from': 'baseline', 
                'localField': 'crossing_id', 
                'foreignField': 'id', 
                'as': 'string'
            }
        }, {
            '$project': {
                '_id': 1, 
                'utc': 1, 
                'crossing_id': 1, 
                'name': 1, 
                'wait': 1, 
                'timezone': {
                    '$arrayElemAt': [
                        '$string.timeZone', 0
                    ]
                },
                'profile': {
                    '$arrayElemAt': [
                        '$string.profile', 0
                    ]
                },
                'district': {
                    '$arrayElemAt': [
                        '$string.district', 0
                    ]
                },
                'region': {
                    '$arrayElemAt': [
                        '$string.region', 0
                    ]
                },                                  
            }
        }
    ]
    return run.aggregate(query)

def get_regions():
    return list(col.distinct('region'))
def get_district(region):
    if region =='All':
        return list(col.distinct('district'))
    return list(col.distinct('district',filter={'region':region}))
def map_df(filter):
    return lm.find(filter)
def new_vis_data(filter):
    return merge.find(filter)
def get_ports(region,district):
  filter = {'profile':1} #DEBUG ONLY FOR NOW BECAUSE WE ONLY GET DATA FOR 26 SITES
  if region != 'All':
      filter.update({'region':region})
  if district != 'All':
      filter.update({'district':district})

  return list(col.distinct('name',filter))
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
            'wait': 1, 

            'timezone': {
                '$arrayElemAt': [
                    '$timezone.timeZone', 0
                ]
            }
        }
    }
]
def mongo_setup():
    return db, db.list_collections()
def add_one_log(r,id):
    traffic = utility_func.get_traffic_time(r.json())
    baseline = utility_func.get_baseline_time(r.json())
    wait = max(0,traffic-baseline)
    utc_time = utility_func.round_to_10min(dt.now(tz=timezone.utc))
    name = id['name']
    local_tz = pytz.timezone(id['timeZone'])
    day_strf = '%d-%b-%Y'
    time_strf = '%H_%M_%S'
    local_dt = utility_func.round_to_10min(datetime.datetime.now(local_tz))
    day_val = local_dt.strftime(day_strf)
    time_val = local_dt.strftime(time_strf)

    mydict = {"utc":utc_time, "crossing_id": id['id'], "name":name,"wait":wait}
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
def queries_this_month():
    m = dt.utcnow().month
    y = dt.utcnow().year


    start_date = dt(y,m,1)
    if m > 11:
        m = 1
        y = y+1
    else:
        m = m+1
    end_date = dt(y,m,1)

    filter = {'utc':{'$gte':start_date,'$lt':end_date}}
    
    return run.count_documents(filter)
def mongo_setup():
    return db, db.list_collections()

def legacy_add(l):
    leg.insert_many(l)
def records_by_day():
    pipeline = [
        {
            '$addFields': {
                'Date': {
                    '$dateToString': {
                        'format': '%Y-%m-%d', 
                        'date': '$utc'
                    }
                }
            }
        }, {
            '$group': {
                '_id': '$Date', 
                'count': {
                    '$sum': 1
                }
            }
        }
    ]
    return run.aggregate(pipeline)
def update_filter_timeframe(filter, selection):
    month = dt.utcnow().month
    day = dt.utcnow().day
    year = dt.utcnow().year
    delta_d=0
    delta_m = 0
    delta_y = 0
    if selection == '1 day':
        delta_d = 1
    elif selection == ' 1 week':
        delta_d = 7
    elif selection == '1 month':
        delta_m = 1
    elif selection == '1 quarter':
        delta_m = 3
    elif selection == '1 year':
        delta_y = 1
    else:
        return filter
    newday = day - delta_d
    newmonth = month - delta_m
    newyear = year - delta_y
    if newday < 1:
        newmonth = newmonth - 1
    if newmonth < 1:
        newmonth = newmonth + 12
        newyear = newyear - 1
    newdate = dt(newyear,newmonth,day)
    filter.update({'utc':{'$gte':newdate}})
    return filter

def totals_by_day():
    pipeline = [
        {
            '$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d', 
                        'date': '$utc'
                    }
                }, 
                'count': {
                    '$sum': 1
                }
            }
        }, {
            '$sort': {
                '_id': 1
            }
        }
    ]
    return run.aggregate(pipeline)

if __name__ == '__main__':
    # print(get_all_ids())
    # print(len(get_all_ids()))
    #print(get_all_ids())
    #pass
    print(queries_this_month())