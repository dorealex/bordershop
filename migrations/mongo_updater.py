import os
from os.path import isfile, join
import pymongo
import datetime
import pandas as pd
from config import cluster_uri
import certifi
import sys

def get_columns(args):
    return [str(x) for x in args if str(x)[-3:] != "csv" and str(x)[-2:] != "py"]


if __name__ =='__main__':
    ### PyMongo Set up
    ca = certifi.where()
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)
    db = cluster['bordercross']
    col= db['baseline']

    ### Load File
    dir_path = os.path.dirname(os.path.realpath(__file__))
    args = sys.argv

    #print(dir_path)
    #print(str(args[1:]))

    onlyfiles = [f for f in os.listdir(dir_path) if isfile(f)]
    #print(onlyfiles)
    file_sel = "crossings.csv"
    for x in args[1:]:
        if str(x)[-3:] == 'csv':
            file_sel= str(x)
    #print(file_sel)

    if file_sel in onlyfiles:
        #file in the directory
        print("File found", file_sel)
        cols = get_columns(args)

        df = pd.read_csv(file_sel)
        if len(cols) >=1:
            df = df[cols+['id']] if id not in cols else df[cols]
        else:
            print("No columns specified, here's the df")
            print(df)
            sys.exit
        print(df)
        for x in range(len(df)):
            cross_id = int(df['id'].iloc[x])
            for y in df.columns:
                value = df[y].iloc[x]
                print("Updating:", cross_id,y, value)
                col.find_one_and_update(filter={'id':cross_id}, update={'$set':{y:value}})

    else:
        #file not in, quitting
        print("file not found")
        sys.exit
