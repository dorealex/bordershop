import requests
import json
from datetime import datetime as dt
import time

#####
#important, create file called config.py, in it declare a variable api_key with your google maps api key
from config import api_key
#####


def get_timezone_data(id,name,point):
  #ask google for the timezone data, store in file
  ts=str(time.time())
  base_url = 'https://maps.googleapis.com/maps/api/timezone/json?location='+point+'&timestamp='+ts+'&key='+api_key
  r = requests.get(base_url)
  if r.status_code == 200:
    response = r.json()
    print("response is of type",type(response))
    fname = "-".join([str(id),name,"TimeZone",str(dt.today().strftime("%d_%m_%Y"))])+".json"
    fname = fname.replace("/","_")
    fname = fname.replace(":","_")

    with open('timezone/'+fname,'w') as outfile:
      json.dump(response, outfile, indent=4)
  else:
    print("Error on the api", r.status_code)
    print(base_url)
  

def url_creator(origin, destination):
  #prepares http request url string
  base = "https://maps.googleapis.com/maps/api/directions/json?"
  return base + "&departure_time=now&mode=driving&origin=side_of_road:"+origin+"&destination=side_of_road:"+destination+"&key="+api_key

def get_baseline_time(response):
  #returns the regular time (without traffic)
  #iterate through the gmaps output and sum up the time values, in case it is more complex
  total= 0
  
  if 'routes' in response.keys():
    for x in response['routes']:
      for y in x['legs']:
        z = y['duration']['value']
        total=total+z
  return total


def get_data(url_req):
  #returns the request
  return requests.get(url_req)

def save_request(id,name,r):
  #saves the json
  fname = "-".join([str(id),name,dt.now().strftime("%x-%X")])
  fname = fname.replace("/","_")
  fname = fname.replace(":","_")
  fname = fname+".json"
  with open('data/'+fname, 'w') as outfile:
    json.dump(r.json(), outfile,indent=4)


def get_traffic_time(response):
  #returns the time with the traffic
  #iterate through the gmaps output and sum up the time values, in case it is more complex
  total = 0

  if 'routes' in response.keys():
    for x in response['routes']:
      for y in x['legs']:
        z = y['duration_in_traffic']['value']
        total=total+z
  return total

def get_distance(response):
  #returns the time with the traffic
  #iterate through the gmaps output and sum up the time values, in case it is more complex
  total = 0

  if 'routes' in response.keys():
    for x in response['routes']:
      for y in x['legs']:
        z = y['distance']['value']
        total=total+z
  return total


def passthrough(origin, destination, type):
  #old function, does it all, but uses 1 api call each time.
    url_req = url_creator(origin, destination)
    r = requests.get(url_req)
    response = r.json()
    if type =='baseline':
        return get_baseline_time(response)
    elif type =='traffic':
        return get_traffic_time(response)
    elif type =='distance':
        return get_distance(response)
