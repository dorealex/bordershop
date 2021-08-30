from mongo_updater import get_columns
import os
from os.path import isfile, join
import pymongo
import datetime
import pandas as pd
from config import cluster_uri
import certifi
import sys
import numpy as np
ca = certifi.where()

on_heroku=False
if 'on_heroku' in os.environ:
    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
else:
    from config import cluster_uri
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)

db = cluster['bordercross']
col= db['baseline']



def get_column(df):
    valid = False
    cols = df.columns
    while valid  == False:
        value = str(input("Column you want to upload to MongoDB collection: "))
        if value in cols and value !="id":
            valid = True
            return value
        elif value == 'exit':
            valid = True
            return False
        else:
            print("Invalid selection, please enter a valid entry or exit")

file_name = str(input)

if __name__ == "__main__":
    file_name = str(input("What is the file name?: "))
    if os.path.exists(file_name) and file_name[-3:] == 'csv':
        print("File exists and is a CSV")
        df = pd.read_csv(file_name)
        print("Sample of the df:")
        print("=================")
        print(df.head())
        column = get_column(df)
        if column != False:
            print("You have selected column: ", column)
            df = df[['id','name', column]]
            print(df)
            if str(input("Is this correct? Y/N ").lower()) == "y":
                print("Uploading field to MongoDB")
                for x in range(0,len(df)):
                    id = int(df['id'].iloc[x])
                    value = df[column].iloc[x]
                    if type(value) == np.int64:
                        value = int(value)
                    query = {"id":id}
                    update_val = {"$set":{column:value}}
                    col.find_one_and_update(query,update_val)
                    print("Updated #",id,": ",value)
            else:
                print("Exiting...")
                sys.exit()

        else:
            print("Exiting")
            sys.exit()
    else:
        print("File invalid")