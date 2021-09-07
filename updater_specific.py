#!/usr/bin/env python3
import datetime
import schedule
from datetime import timedelta
import time
import update
import pytz
import utility_func
import mongo_queries
import sys

def get_next_job(local_time, profile):
    local_time = local_time.time()
    next_time = datetime.timedelta(minutes=30)
    if local_time.hour >=7 and local_time.hour<=18:
        if profile == 1:
            next_time = datetime.timedelta(minutes=10)
        else:
            next_time = datetime.timedelta(minutes=15)
    return next_time

def update_one(id):
    #get data
    #print(id)
    orig = id['origin']
    dest = id['dest']
    url = utility_func.url_creator(orig,dest)
    r = utility_func.get_data(url)
    mongo_queries.add_one_log(r,id) #saves to running log, returns dict of what was added.

def init_run():
    time_strf = '%H:%M:%S'
    print(datetime.datetime.utcnow().strftime(time_strf))
    count=0
    
    #first run, no jobs in queue
    ###actually, run all the time
    ids = mongo_queries.get_all_ids(poc)
    if len(sys.argv)>1 and "force" in sys.argv:
        force=True #debug
        sys.argv.pop()
    else:
        force=False
    
    for x in ids:
        try:
            count += 1
            id = x['id']
            #last run
            last_run = mongo_queries.get_last_run(id) #UTC
            #profile 
            profile = x['profile']
            #current local time
            local_tz = pytz.timezone(x['timeZone'])
            #print(local_tz)
            local_dt = datetime.datetime.now(local_tz)
            #print(local_dt)
            #print(last_run)
            time_since =  datetime.datetime.now(pytz.timezone("UTC"))-last_run
            next_job  = get_next_job(local_dt,profile)
            if time_since >= next_job or force:
                update_one(x)
                print(count,"\tUpdating:\t",x['name'], "Local Time", local_dt.strftime(time_strf), "last_run (UTC)",last_run.strftime(time_strf), "time since:", time_since,"interval:",next_job)
            else:
            #pass
                print(count,"\tNOT Updating:\t",x['name'], "Local Time", local_dt.strftime(time_strf), "last_run",last_run.strftime(time_strf), "time since:", time_since,"interval:",next_job)
        except Exception as inst:
            print("Error\t",type(inst),inst.args,inst)
    print("===========")
    force=False
### Change this manually after first run.
poc=True


if __name__ == "__main__":
    init_run()
    schedule.every(1).minutes.until(timedelta(days=5)).do(init_run)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("User interrupted script with keyboard")
            sys.exit()
        except Exception as Argument:
            with open("error_log_updater.txt","a") as f:
                f.write(str(Argument,datetime.datetime.now()))
            print("error occured")
        