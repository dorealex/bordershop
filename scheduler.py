import datetime
import schedule
from datetime import timedelta
import time
import update

def job():
    print(datetime.datetime.now(),"... updating")
    
    update.main()
    print(schedule.get_jobs())

    

schedule.every(10).minutes.until(timedelta(days=2)).do(job)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except:
        print("Error")