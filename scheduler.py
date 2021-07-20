import datetime
import schedule
from datetime import timedelta
import time
import update

def job():
    print(datetime.datetime.now())
    print("Updating")
    update.main()
    print(schedule.get_jobs())

    

schedule.every(30).minutes.until(timedelta(hours=24)).do(job)

while True:
    schedule.run_pending()
    time.sleep(1)