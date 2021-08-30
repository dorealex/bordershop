import datetime
import schedule
from datetime import timedelta
import time
import update

def job():
    print(datetime.datetime.now(),"... updating")
    
    update.main()
    print(schedule.get_jobs())

    

schedule.every(30).minutes.until(timedelta(days=1)).do(job)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except:
        print("Error")