import os
import pymongo
import datetime
import pandas as pd
from config import cluster_uri
import certifi
import sys

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
    print(str(args[1:]))