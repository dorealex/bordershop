import datetime
import schedule
from datetime import timedelta
import time
import update


def get_data(id):
    #get data from db
    pass

def get_api_data(id):
    #get data from gmaps
    pass

def process_data(id):
    #save the data to mongodb
    pass
def get_next_job(id,local_time, profile):
    #get the next time this thing should run
    #returns deltatime? or actual datetime to run.... deltatime
    pass

def add_next_job(id,time):
    #adds the job to the queue
    pass

def update_one(id):
    #get data
    #get api data
    #process data, save to db
    #get next run time
    #add run time to schedule
    print("Updated id")
def get_all_ids():
    #get all the ids
    #returns a list of ids from baseline
    pass

def first_run():
    #first run, no jobs in queue
    ids = get_all_ids()
    for x in range(0,len(ids)):
        update_one(x)
    pass

### Change this manually after first run.

if __name__ == "__main__":
    first_run = True
    if first_run:
        first_run()
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            print("Error")