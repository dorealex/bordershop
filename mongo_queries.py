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
#merge = db['running_merge']
merge = db['running_merge2'] #for smaller queries
lm = db['latest_merged']
current = db['current_updaters']
profs = db['profiles']
leg_map = db['leg_map']


def prepare_legacy_compare(f):
    #get regular wait times
    print(f)
    timeframe = f.pop('utc') if 'utc' in f else False
    first = {'$match':f}
    q1 = [first]
    q2 = [first]
    q1.append({'$unwind':{'path':'$legacy_times'}})
    q2.append({'$unwind':{'path':'$wait_times'}})
    if timeframe:
        q1.append({'$match': {'legacy_times.timestamp':timeframe}})
        q2.append({'$match': {'wait_times.utc':timeframe}})
    q1.append({'$project':{
        'name': 1,
        'timezone': '$timeZone',
        'utc': '$legacy_times.timestamp',
        'wait': '$legacy_times.travellers_seconds',
        'type': 'legacy'}})
    q2.append({'$project':{
        'name':1,
        'timezone':'$timeZone',
        'utc':'$wait_times.utc',
        'wait':'$wait_times.wait',
        'type':'api'
    }})
    print(q1,"\n-----")
    res1 = list(col.aggregate(q1))
    print(len(res1),"\n-----")
    print(q2,"\n-----")
    res2 = list(col.aggregate(q2))
    print(len(res2),"\n-----")
    
    
    
    
    return res1+res2


def legacy_name_to_id(name):
    #given a name, as per the legacy times website, provide an ID as per the mapping
    res = leg_map.find_one({'CBSA_Office':name})
    return res['crossing_id']
def id_to_legacy_name(id):
    #given an id, as per the legacy times website, provide a name
    res = leg_map.find_one({'crossing_id':id})
    if res:
        return res['CBSA_Office']
    else:
        return

def convert_to_local(ut,tz):
    #given a utc and a timezone, convert UTC into local time at that time zone and return it
    if ut.tzinfo != pytz.UTC:
        ut = pytz.utc.localize(ut) # convert to aware
    if type(tz)==str:
        tz = pytz.timezone(tz) #in case the input is just string
    res = ut.astimezone(tz)
    #print(ut,">>>",res) #debug
    return res


def get_poll_rate(profile, local_time):
    #returns the poll rate in number of minutes for the profile given local time
    #based on latest info from database
    #local_time has to be a datetime
    hour = local_time.hour
    #minu = local_time.minute #not needed?
    if type(profile) == int: #mongodb keys are strings
        profile  =str(profile)

    default = 60 # in case we can't find the rate
    latest = list(profs.aggregate([
        {'$sort':{'utc':-1}},
        {'$limit':1}
    ]))[0] #finds the latest set of profile rates
    try:
        sub_d = latest['profiles'][profile]
        for seg in sub_d:
            if hour in range(seg['segment_start'],seg['segment_end']):
                return seg['poll_rate']
        return default #if for whatever reason there was no time match
    except KeyError:
        return default
def get_hist_data(f):
    #print(f)
    timeframe = f.pop('utc') if 'utc' in f else False 
    q = [
    {
        '$match': f
    }, {
        '$unwind': {
            'path': '$wait_times', 
            'preserveNullAndEmptyArrays': False
        }
    }, {
        '$project': {
            'timezone': '$timeZone', 
            'utc': '$wait_times.utc', 
            'wait': '$wait_times.wait',
            '_id':0,
        }
    }
    ]
    
    if timeframe:
            q.append({'$match': {'utc':timeframe}})
    res = col.aggregate(q,allowDiskUse=True)
    #print(q)
    
    return list(res)

def get_last_run_by_filter(f,req = None):
    timeframe = f.pop('utc') if 'utc' in f else False
    q=[
        {
            '$match': f
        }, {
            '$unwind': {
                'path': '$wait_times', 
                'preserveNullAndEmptyArrays': False
            }
        }, {
            '$group': {
                '_id': '$id', 
                'utc': {
                    '$last': '$wait_times.utc'
                }, 
                'wait': {
                    '$last': '$wait_times.wait'
                }
            }
        }]
    if timeframe:
        q.append({'$match': {'utc':timeframe}})

    tail = [{
            '$lookup': {
                'from': 'baseline', 
                'localField': '_id', 
                'foreignField': 'id', 
                'as': 'string'
            }
        }, {
            '$project': {
                '_id': {
                    '$arrayElemAt': [
                        '$string.id', 0
                    ]
                }, 
                'name': {
                    '$arrayElemAt': [
                        '$string.name', 0
                    ]
                }, 
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
                'origin': {
                    '$arrayElemAt': [
                        '$string.origin', 0
                    ]
                }, 
                'timezone': {
                    '$arrayElemAt': [
                        '$string.timeZone', 0
                    ]
                }, 
                'region': {
                    '$arrayElemAt': [
                        '$string.region', 0
                    ]
                }, 
                'district': {
                    '$arrayElemAt': [
                        '$string.region', 0
                    ]
                }, 
                'profile': {
                    '$arrayElemAt': [
                        '$string.profile', 0
                    ]
                }, 
                'utc': 1, 
                'wait': 1
            }
        }
    ]

    q.extend(tail)
    #print(q)
    res = col.aggregate(q,allowDiskUse=True)
    return list(res)
def get_last_run_base(id, req = None):
    ###Given an id, return the last reading
    ###Part of DB reset, times are now sub doc arrays on the baseline collection
    res = col.aggregate([
    {
        '$match': {
            'id': id
        }
    }, {
        '$unwind': {
            'path': '$wait_times', 
            'preserveNullAndEmptyArrays': False
        }
    }, {
        '$project': {
            '_id': 0, 
            'id': 1, 
            'name': 1, 
            'province': 1, 
            'dest': 1, 
            'timeZone': 1, 
            'region': 1, 
            'district': 1,
            'origin':1,
            'profile':1, 
            'utc': '$wait_times.utc', 
            'wait': '$wait_times.wait'
        }
    }, {
        '$sort': {
            'utc': -1
        }
    }, {
        '$limit': 1
    }
])
    res = list(res)[0]
    if req == 'wait':
        return res['wait']
    elif req =='utc':
        return res['utc'].astimezone(pytz.utc)
    elif req =='local':
        utc = res['utc']
        local_tz = res['timeZone']
        
        return utc.astimezone(pytz.timezone(local_tz))
    else:
        return res
def ids_to_names(ids):
    if type(ids) != list:
        ids = [ids]
    return list(col.find({'id':{'$in':ids}},projection={'name':1, '_id':0}))
def get_updating_list():
    ###Part of db reset, collection gets the latest array and queries those only.
    return list(current.find({}).sort('datetime',-1).limit(1))[0]['sites']

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

def add_one_base(r,id):
    ###DB RESET FRIENDLY
    #r is the request
    #id is the crossing id as an integer, from the baseline collection, ex 817 -> Abbotsford
    traffic = utility_func.get_traffic_time(r.json())
    baseline = utility_func.get_baseline_time(r.json())
    wait = max(0,traffic-baseline)
    utc_time = utility_func.round_to_10min(dt.now(tz=timezone.utc))
    doc = {'utc':utc_time,'wait':wait}
    col.update_one({'id':id},{'$push':{'wait_times':doc}})

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

def queries_this_month_base(curr=None):
    #how many queries were sent to google this month, if a date is supplied it will use that calendar month. If not, it will use today (UTC)
    if not curr:
        curr = dt.utcnow()
    y = curr.year
    m = curr.month

    start = dt(y,m,1)
    if m==12:
        end = dt(y+1,1,1) - timedelta(days=1) #if its in December, then you go to the day before Jan 1st.
    else:
        end = dt(y,m+1,1) - timedelta(days=1) #otherwise go to the next month, and go back 1 day. This handles the months of varying length

    res = col.aggregate([
        {
            '$unwind': {
                'path': '$wait_times', 
                'includeArrayIndex': 'string', 
                'preserveNullAndEmptyArrays': False
            }
        }, {
            '$project': {
                'utc': '$wait_times.utc'
            }
        }, {
            '$match': {
                'utc': {
                    '$gte': start, 
                    '$lt': end
                }
            }
        }, {
            '$count': 'utc'
        }
    ])
    return list(res)[0]['utc']

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
def timeframe(selection):
    #given a selection, return the filter text to generate the appropriate query
    day = dt.utcnow()    

    if selection == '1 day':
        delta_d=1
    elif selection == '1 week':
        delta_d = 7
    elif selection == '1 month':
        delta_d = 30
    elif selection == '1 quarter':
        delta_d = 90
    elif selection == '1 year':
        delta_d = 365
    else:
        return ""
    newdate = day - timedelta(days=delta_d)
    
    return {'utc':{'$gte':newdate}}

def update_filter_timeframe(filter, selection):
    
    day = dt.utcnow()
    

    if selection == '1 day':
        delta_d=1
    elif selection == '1 week':
        delta_d = 7
    elif selection == '1 month':
        delta_d = 30
    elif selection == '1 quarter':
        delta_d = 90
    elif selection == '1 year':
        delta_d = 365
    else:
        return filter
    
    newdate = day - timedelta(days=delta_d)
    
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