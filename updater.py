import datetime as dt
import schedule
from datetime import timedelta,timezone
import time
#import tools.legacy_scraper

import tools.utility_func as utility_func
import tools.mongo_queries as mongo_queries
import sys

def main():
    print(dt.datetime.utcnow())
    
    sites = mongo_queries.get_current_updaters(False) #get IDS that we need to poll
    until_date = mongo_queries.get_current_deadline() # check if teh date
    
    for s in sites :
        due, time_since, rate = mongo_queries.crossing_is_due(s,True)
        if due and dt.datetime.utcnow() <= until_date:
            
            print(f"{s} is due, getting data. Time since: {time_since}. Current poll rate: {rate}")
            x = mongo_queries.col.find_one({'id':s})
            url = utility_func.url_creator(x['origin'],x['dest'])               #create the url
            r = utility_func.get_data(url)
            mongo_queries.add_one_base(r,x)
        else:
            print(f"{s} is not due, skipping. Time since: {time_since}. Current poll rate: {rate}")
    # try:
    #     #legacy_scraper.main()
    # except:
    #     print("Legacy scrape failed")
    print("=================================")

if __name__ == "__main__":
    main()
    res = mongo_queries.get_current_updaters()
    stop_date = res['until_date'] if 'until_date' in res.keys() else dt.utcnow()+timedelta(days=4)
    
    numdays = stop_date - dt.datetime.utcnow()
    print(numdays)
    
    schedule.every(1).minutes.until(timedelta(days=numdays.days)).do(main)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("User interrupted script with keyboard")
            sys.exit()
