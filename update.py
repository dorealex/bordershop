import pandas as pd
import utility_func
from datetime import datetime as dt
from datetime import timezone
import csv

def main():
    df = pd.read_csv("crossings.csv")
    df['dest'] = df['lat_actual'].astype(str) +", " +df['long_actual'].astype(str)
    df['origin'] = df['lat_origin'].astype(str) +", "+ df['long_origin'].astype(str)

    log_file = 'log.csv'
    #headers: date,time,id,name,traffic,baseline
    day_strf = '%d-%b-%Y'
    time_strf = '%H_%M_%S'
    day_val = dt.now().strftime(day_strf)
    time_val = dt.now().strftime(time_strf)
    utc_time = dt.now(tz=timezone.utc)

    #get traffic time
    rows=[]
    for x in range(0, len(df)):
        #row=[]
        id = df['id'].iloc[x]
        name = df['name'].iloc[x]
        orig = df['origin'].iloc[x]
        dest = df['dest'].iloc[x]

        url_req = utility_func.url_creator(orig,dest)
        r = utility_func.get_data(url_req)
        utility_func.save_request(id,name,r)
        traffic = utility_func.get_traffic_time(r.json())
        baseline = utility_func.get_baseline_time(r.json())
        row = [day_val, time_val,utc_time, id, name, traffic, baseline]
        rows.append(row)
    #write to log
    

    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

if __name__ == '__main__':
    main()