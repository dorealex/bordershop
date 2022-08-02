# Contents of ~/my_app/pages/page_2.py
import streamlit as st
import tools.mongo_queries as mongo_queries
import pymongo
import os
st.markdown("# Admin")
st.sidebar.markdown("# Admin")

on_heroku=False
if 'on_heroku' in os.environ:

    on_heroku = True
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
    api_key = os.environ['gmaps']
else:
    import certifi
    import tools.utility_func
    from config import cluster_uri, api_key
    ca = certifi.where()
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)