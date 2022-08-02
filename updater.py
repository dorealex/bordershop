import datetime
import schedule
from datetime import timedelta
import time
import tools.legacy_scraper
import pytz
import tools.utility_func
import tools.mongo_queries as mongo_queries
import sys

def main():
    pass

if __name__ == "__main__":
    count = mongo_queries.queries_this_month_base()
    if count >= 15500: ###TODO remove once debug is over
        print("Free-tier monthly limit reached")
        with open("error_log_updater.txt","a") as fil:
            fil.write(f'{datetime.datetime.now()}: Free-tier monthly limit reached')
        schedule.jobs.clear()
        sys.exit()
    main()
    res = mongo_queries.get_current_updaters()
    numdays = res['days'] if 'days' in res.keys() else 4
    schedule.every(1).minutes.until(timedelta(days=numdays)).do(main)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("User interrupted script with keyboard")
            sys.exit()
        except Exception as Argument:
            with open("error_log_updater.txt","a") as fil:
                fil.write(f'{datetime.datetime.now()}:{str(Argument)}')
            print("error occured")