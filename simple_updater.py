import datetime
import schedule
from datetime import timedelta
import time
import legacy_scraper
import pytz
import utility_func
import tools.mongo_queries as mongo_queries
import sys



def main():
    time_strf = '%H:%M:%S'
    print(datetime.datetime.utcnow().strftime(time_strf),": starting update check")
    #get the list of sites
    sites = mongo_queries.get_updating_list()
    for s in sites:
            x=mongo_queries.get_last_run_base(s)        
            id = x['id']                                                            #the id of the location
            utc = x['utc']
            utc = pytz.utc.localize(utc)                                            #the utc time it was last run
            tz = x['timeZone']                                                      #the time zone of the location
            ltnow = mongo_queries.convert_to_local(datetime.datetime.utcnow(),tz)   #local time now        
            lt = mongo_queries.convert_to_local(utc,tz)                             #local time at last time it was run
            poll_rate = mongo_queries.get_poll_rate(x['profile'],ltnow)             #how often it should be polled, in minutes
            poll_rate = datetime.timedelta(minutes=poll_rate)                       #convert the number of minutes into minutes (timedelta)
            now = datetime.datetime.utcnow()                                        #current utc time
            now = pytz.utc.localize(now)                                            #converted to aware
            time_since = now - utc                                                  #time since it was last polled
            due = time_since > poll_rate                                            #is it due to be polled
            if due:        
                url = utility_func.url_creator(x['origin'],x['dest'])               #create the url
                r = utility_func.get_data(url)                                      #send the request to google maps API
                mongo_queries.add_one_base(r,x['id'])                               #add it to the database. Note: DB reset --> now adds the data to the baseline collection as a sub array
            x.update({'local_time':lt,'time_since':time_since,'poll_rate':poll_rate,'due':due})  # dict of what we did, not needed other than a df?
            print(now,' - ', x['name'],' \tlast run:', utc,' \ttime since:', time_since,' \tdue:',due)
    print('Scraping legacy')
    legacy_scraper.main()

if __name__ == "__main__":
    count = mongo_queries.queries_this_month_base()
    if count >= 15500: ###TODO remove once debug is over
        print("Free-tier monthly limit reached")
        with open("error_log_updater.txt","a") as f:
                f.write('Free-tier monthly limit reached')
        schedule.jobs.clear()
        sys.exit()
    main()
    schedule.every(1).minutes.until(timedelta(days=4)).do(main)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("User interrupted script with keyboard")
            sys.exit()
        except Exception as Argument:
            with open("error_log_updater.txt","a") as f:
                f.write(str(Argument))
            print("error occured")