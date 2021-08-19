# Requires the PyMongo package.
# https://api.mongodb.com/python/current

###Gets the latest results, joins the specific data: coordinates, province, etc.
from numpy import dtype
from datetime import datetime as dt, time
from datetime import timedelta

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

def get_local_tz(filter):
    if type(filter) == str:
        return merge_running_timezones+[{'$match':{'name':filter}}]
    
    elif type(filter) == int:
        return merge_running_timezones+[{'$match':{'id':id}}]
    


if __name__ == '__main__':
    #print(get_local_tz("Douglas"))
    print(dt.utcnow().date()-timedelta(days=7))
    