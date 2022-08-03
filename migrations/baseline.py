import pandas as pd
from datetime import datetime as dt
import utility_func
import datetime as dt
#df = pd.read_csv("crossings_west.csv")
df = pd.read_csv("crossings.csv")
df['dest'] = df['lat_actual'].astype(str) +", " +df['long_actual'].astype(str)
df['origin'] = df['lat_origin'].astype(str) +", "+ df['long_origin'].astype(str)
baselines=[]
traffics=[]
distances=[]

for x in range(len(df['dest'])):
    #build the URL query
    orig = df['origin'].iloc[x]
    dest = df['dest'].iloc[x]
    #get the response
    r = utility_func.get_data(utility_func.url_creator(orig, dest))
    #save the json
    id = df['id'].iloc[x]
    name = df['name'].iloc[x]
    utility_func.save_request(id,name,r)


    #build the results table
    baseline = utility_func.get_baseline_time(r.json())
    traffic = utility_func.get_traffic_time(r.json())
    distance = utility_func.get_distance(r.json())
    baselines.append(baseline)
    traffics.append(traffic)
    distances.append(distance)



df['baseline'] = baselines
df['traffic'] = traffics
df['distance'] = distances

cols = ['id','name', 'province', 'dest', 'origin', 'baseline','distance', 'traffic']
df[cols].to_csv("baseline.csv", index=False)
