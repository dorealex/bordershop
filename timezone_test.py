import datetime
import pytz

tzs = ['America/New_York', 'America/Winnipeg','America/Edmonton']

for x in tzs:
    print(datetime.datetime.now(pytz.timezone(x)))