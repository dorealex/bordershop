import utility_func
import pandas as pd
import json
from os import listdir
from os.path import isfile, join
import streamlit as st

dir = 'timezone'
onlyfiles = [f for f in listdir(dir) if isfile(join(dir, f))]
crossings = 'crossings.csv'
df = pd.read_csv(crossings)
def run_once():
    for x in range(len(df)):
        id = df['id'].iloc[x]
        name = df['name'].iloc[x]
        loc = str(df['lat_actual'].iloc[x])+','+str(df['long_actual'].iloc[x])
        utility_func.get_timezone_data(id,name,loc)


def get_row(doc):
    with open('timezone/'+doc) as f:
        data = json.load(f)
    data['id'] = doc.split("-")[0]
    data['name'] = doc.split('-')[1]
    return data


if __name__ =='__main__':
    tzs = [get_row(x) for x in onlyfiles if x.split(".")[-1] =='json']
    df = pd.DataFrame(tzs)
    df
    df.to_csv('tz_data.csv',index=False)