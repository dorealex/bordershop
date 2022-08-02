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
import googlemaps
from datetime import timezone
import pytz

on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
    api_key = os.environ['gmaps']
else:
    import tools.utility_func as utility_func
    from config import cluster_uri, api_key
    ca = certifi.where()
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)
gmaps = googlemaps.Client(key=api_key)
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
controller = db['controller'] # This is the collection of documents that dictates which sites are updated and when
hist = db['hist']

def mapmaker(start,dest,key,crossing=None, day=None,time=None):
    #######################################
    # used in the traveller page          #
    #######################################

    base = 'https://www.google.com/maps/embed/v1/directions'
    key = '?key='+key
    origin = '&origin='+str(start['lat'])+","+str(start['lng'])
    dest = '&destination='+dest
    src = base+key+origin+dest
    html_str = '<iframe width="450" height="250" frameborder="0" style="border:0" src='+src+'</iframe>'
    #print(src)
    #return html_str
    return src



def find_latest_from_ID(x,write=True):
    #goes in the hist collection, finds the latest wait and writes that to the collection (baseline)

    #######################################
    # used to update the hist coll        #
    # July 2022, keep for new version     #
    #######################################

    filter={'id': x}
    project = {'utc':1,'id':1,'wait':1,'_id':0}
    sort=list({'utc': -1}.items())
    limit=1
    latest = list(hist.find(filter=filter, projection=project,sort=sort, limit=limit))[0]
    
    wait = latest['wait']
    utc = latest['utc']
    update = {'latest_times':{
        'utc':utc,
        'wait':wait
    }}
    if write:
        col.find_one_and_update({'id':x},{'$set':update})
    else:
        return latest




def get_trips(start_location,end_location,utc_start_time=None):
  #maps out a trip using google maps api
  #finds when the user is crossing into Canada, returns that GPS coordinate, and when

    #######################################
    # used in the traveller page          #
    #######################################

  gmaps = googlemaps.Client(key=api_key)
  trips = []
  directions = gmaps.directions(origin=start_location, destination=end_location,alternatives=True,departure_time=utc_start_time,)
  if not utc_start_time:
    utc_start_time= dt.utcnow()
  for r in range(len(directions)):
    route = directions[r]
    val = 0
    duration = 0
    dist = 0
    summary = route['summary'] 
    for l in range(len(route['legs'])):
      leg = route['legs'][l]
      dist = dist + leg['distance']['value']/1000 #km
      duration = duration + leg['distance']['value']/3600 #hours
      for s in range(len(leg['steps'])):
        
        step = leg['steps'][s]
        val = val + step['duration']['value']
        #print(r,l,s)
        instructions = step['html_instructions']
        if "Entering Canada" in instructions:
          end_loc = step['end_location']
          #print(step.keys())
          lat = end_loc['lat']
          lng = end_loc['lng']
          cross_time = utc_start_time + datetime.timedelta(seconds=val)
          #print(r,l,s,instructions, (lng,lat), cross_time)
          trips.append({'lat': lat, 'long':lng, 'time_utc':cross_time, 'duration':duration, 'distance':dist, 'summary':summary})
  if len(trips) == 0:
    return "Could not find crossing"
  else:
    return trips

def lookup_geo(lat,lng):

    #########################################
    # input: latitude, longitude            #
    # output: nearest crossing (within 15km)#
    #########################################
    q = [{'$geoNear':
        {'near': {'type': 'Point', 
            'coordinates': [
                lng, lat
                ]
            }, 
            'distanceField': 'distanceCalc', 
            'maxDistance': 15000, 
            'query': {}, 
            'spherical': True
        }
    }, {
        '$sort': {
            'distanceCalc': 1
        }
    }, {
        '$limit': 1
    }, {
        '$project': {
            'name': 1, 
            'province': 1, 
            'location': 1,
            'id':1,
            'timezone':'$timeZone',
            '_id':0
        }
    }]
    res = list(col.aggregate(q))[0]
    #print(res)
    return res

def get_avg_wait(id,utc):


    #################################################
    # input: crossing ID, crossing datetime         #
    # output: provides estimated wait time          #
    # todo: replace with better estimation model    #
    #################################################


    hour = utc.hour
    dayofweek = utc.date().isoweekday()
    
    q = [
    {
        '$match': {
            'id': id
        }
    }, {
        '$project': {
            'id': 1, 
            'wait_times': 1
        }
    }, {
        '$unwind': {
            'path': '$wait_times'
        }
    }, {
        '$project': {
            'id': 1, 
            'utc': '$wait_times.utc', 
            'wait': '$wait_times.wait', 
            'dayofweek': {
                '$isoDayOfWeek': '$wait_times.utc'
            }, 
            'hour': {
                '$hour': '$wait_times.utc'
            }
        }
    }, {
        '$group': {
            '_id': {
                'dayofweek': '$dayofweek', 
                'hour': '$hour'
            }, 
            'avg_wait': {
                '$avg': '$wait'
            }
        }
    }, {
        '$match': {
            '_id.dayofweek': dayofweek, 
            '_id.hour': hour
        }
    }
]
    
    res = list(col.aggregate(q))
    if len(res)>0:
        
        return res[0]['avg_wait']
    else:
        return 0

def get_trip_wait(start_loc,end_loc, start_time=None):
    #################################################################
    # used in the traveller page                                    #
    # input: start location (USA) end location (Canada), start time #
    # output: trips, crossings and estimated wait at crossing       #
    #################################################################
  results= []
  trips = get_trips(start_location=start_loc, end_location=end_loc,utc_start_time = start_time)
  for t in trips:
    
    crossing = lookup_geo(t['lat'],t['long'])
    duration = t['duration'],
    distance = t['distance'],
    summary = t['summary'],
    driving_time = duration[0]
    #driving_time = driving_time - datetime.timedelta(microseconds = driving_time.microseconds)

    time = t['time_utc']
    id = crossing['id']
    wait = get_avg_wait(id,time)
    #wait = datetime.timedelta(seconds=get_avg_wait(id,time))
    #print(wait)
    d = {'crossing name':crossing['name'],
         'province':crossing['province'],
         'id':id,
         'timezone':crossing['timezone'],
         'est. arrival at border (utc)':time,
         'est. wait at border (s)':wait,
         'total driving time':driving_time,
         'total driving distance':distance[0],
         'route name':summary[0]}
    results.append(d)
  return results

def prepare_legacy_compare(f):
    #############################################################################
    #input: a dict which is used to filter the database of legacy wait times    #
    #output: the legacy wait times                                              #
    #TODO: update to reflect new structure of db and how times are stored       #
    #############################################################################
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
        'type': 'legacy',
        '_id':0}})
    q2.append({'$project':{
        'name':1,
        'timezone':'$timeZone',
        'utc':'$wait_times.utc',
        'wait':'$wait_times.wait',
        'type':'api',
        '_id':0
    }})
    #print(q1,"\n-----")
    res1 = list(col.aggregate(q1))
   # print(len(res1),"\n-----")
   # print(q2,"\n-----")
    res2 = list(col.aggregate(q2))
   # print(len(res2),"\n-----")
    
    
    
    
    return res1+res2

def crossing_is_due(id):
    #########################################################
    # input: crossing id                                    #
    # lookup in db to find when it was last updated
    # !!! Pre supposes site is already on the list          #
    # find out how often it needs to be updated             #
    # output: whether or not site is due for an update      #
    #########################################################
    
    projection={'_id':0,"wait_times":0,"legacy_times":0} # get rid of all the unnecessary info
    doc = col.find_one({'id':id},projection)    #find the baseline doc 
    tz = pytz.timezone(doc['timeZone'])     # timezone of crossing
    utcmoment_naive = dt.utcnow() #now
    utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc) #to tz
    local_dt = utcmoment.astimezone(tz) #convert current UTC time to local time
    local_time = local_dt.time() # get rid of the date portion
    time_format = "%H:%M:%S" #time is stored in this format in the db
    last_time = doc['latest_times']['utc'] # last time this crossing was updated
    last_time = last_time.replace(tzinfo=pytz.utc)
    time_since = utcmoment - last_time

    sites = get_current_updaters()['sites'] # go through the control collection to see which sites are being updated and how often
    due=False # do not update by default
    for s in sites:
        
        if s['id'] == id: #once we find the site we are looking for
            
            segments = s['segments'] 
            for e in segments: # loop through all the segments
                start = dt.strptime(e['start'],time_format).time() #figure out if we are in this segment
                end = dt.strptime(e['end'],time_format).time()
                if start <= local_time <= end:
                    rate = e['rate'] # get the rate in minutes
                    if time_since>=timedelta(seconds=rate*60): # convert to seconds
                        due=True
            
    return due

def get_current_updaters(full=True):
    #####################################################################################
    #input: whether you want the full segment details of the sites being updated or not #
    #output: the data regarding which sites are being updated                           #
    #####################################################################################

    ### part of July 2022 update, multipage setup
    ### this will be used
    #get a list of dict of the currently updating sites
    #format
    # {'utc': datetime,
    #   'sites': [
    #       {'id': int,
    #       'segments':[
    #           {'start':strftime,'end':strftime, 'rate':int} ### rate in number of minutes
    #           ]
    #       }
    #   ]
    # }



    filter={}
    sort=list({
        'utc': -1
    }.items())
    limit=1
    project={'_id':0}
    result = controller.find(
    filter=filter,
    sort=sort,
    limit=limit,
    projection=project
    )
    result = list(result)[0]
    if full:
        return result
    else:
        return [s['id'] for s in result['sites']]




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