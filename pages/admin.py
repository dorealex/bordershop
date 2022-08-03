import streamlit as st
import tools.mongo_queries as mongo_queries
import pymongo
import os
import datetime as dt
import pandas as pd


st.markdown("# Admin")
st.sidebar.markdown("# Admin")

on_heroku=False
if 'on_heroku' in os.environ:

    on_heroku = True
    cleared = False
    cluster_uri = os.environ['cluster_uri']
    cluster = pymongo.MongoClient(cluster_uri)
    api_key = os.environ['gmaps']
else:
    cleared = True
    import certifi
    import tools.utility_func
    from config import cluster_uri, api_key
    ca = certifi.where()
    cluster = pymongo.MongoClient(cluster_uri,tlsCAFile=ca)
def numcalls(rate,date_until):
    rate=rate.lower()
    if rate == 'daily': return 1
    if rate == 'weekly': return 7
    if rate == 'monthly': return 30
    if rate == 'yearly': return 365
    if rate == 'target end': 
        days_left = dt.datetime(date_until.year,date_until.month,date_until.day) - dt.datetime.utcnow()
        return days_left.total_seconds()/3600/24
def make_segments(time1,time2,lowrate,highrate):
    #create segment dict with the 2 times
    tformat = "%H:%M:%S"
    
    time1 = dt.time.strftime(time1,tformat)
    time2 = dt.time.strftime(time2,tformat)
    first = {'start':'00:00:00','end':time1,'rate':lowrate}
    mid = {'start':time1,'end':time2,'rate':highrate}
    last = {'start':time2,'end':'23:59:00','rate':lowrate}
    return [first,mid,last]

def calculate_cost(sites):
    cost_per = 0.02
    cost_unit = "USD"
    total_calls = 0
    for site in sites:
        segments = site['segments']
        for seg in segments:
            start = seg['start']
            end = seg['end']
            rate = seg['rate'] #delay in number of minutes
            t1 = start
            t2 = end
            form = '%H:%M:%S'
            
            dt1 = dt.datetime.strptime(t1,form)
            dt2 = dt.datetime.strptime(t2,form)
            delta = dt2-dt1
            calls =  delta / dt.timedelta(minutes=rate)
            total_calls = calls + total_calls
    
    return total_calls * cost_per, cost_unit, total_calls, cost_per

def costing_table(doc):
    
    sites=doc['sites']
    date_until = doc['until_date']
    cols = ['Time', 'Calls', 'Total Estimate']
    times = ['Daily', 'Weekly', 'Monthly', 'Yearly','Target End']
    est, unit, calls, cost_per = calculate_cost(sites)
    rows=[]
    for t in times:
        row=[]
        row.append(t)
        num_calls = numcalls(t,date_until)
        row.append(round(numcalls(t,date_until)* calls))
        row.append(str(round(row[1] * cost_per,2)) +" "+ unit)
        rows.append(row)
    df = pd.DataFrame(data=rows, columns=cols)
    return df

sites = mongo_queries.get_current_updaters(full=False)
names = mongo_queries.ids_to_names(sites)
names = [i['name'] for i in names]
items = []
for n in names:
    items.append(" - "+n)
st.markdown(f"{len(items)} ports being polled by the API:\n"+"\n".join(items))
### todo indicate if past the time

st.write("Estimate of current rate")
# target end date
current = mongo_queries.get_current_updaters(full=True)
st.dataframe(costing_table(current))
st.write(f'Target end date (UTC): {current["until_date"]}')
if 'doc' not in st.session_state:
    st.session_state['doc'] = {}
if 'sites' not in st.session_state:
    st.session_state['sites'] = []

if 'on_heroku' in os.environ:
    admin_code = st.sidebar.text_input("Code")
    submit_adm = st.sidebar.button("Submit")
    if submit_adm:
        if os.environ['admin_pass'] == admin_code: cleared = True

if cleared:

    st.session_state.doc['utc'] = dt.datetime.utcnow()

    id_input = st.number_input('Crossing ID',1,1000,427,1)
    #todo error catching
    #todo bulk entries
    peak_rate = st.number_input('Peak rate (minutes between updates)',1,60,10,1)
    offpeak_rate = st.number_input('Off Peak rate (minutes between updates)',1,60,20,1)
    slider_range = st.slider("Peak Time (local time)",dt.time(0,0),dt.time(23,59),value=[dt.time(7,0),dt.time(19,0)])
    segments = make_segments(slider_range[0],slider_range[1],offpeak_rate,peak_rate)
    add = st.button('Add crossing to updating list', key=None, help=None, on_click=None, args=None, kwargs=None, disabled=False)
    date_until = st.date_input("Run script until",dt.datetime.utcnow() + dt.timedelta(days=7))
    cols = ['Time', 'Calls', 'Total Estimate']
    times = ['Daily', 'Weekly', 'Monthly', 'Yearly','Target End']

    if add:
        site = {'id':id_input,'segments':segments}
        st.session_state.sites = st.session_state.sites + [site]
        st.dataframe(costing_table({'until_date':date_until,'sites':st.session_state.sites}))

    st.session_state.doc['sites']= st.session_state.sites

    st.session_state.doc['until_date']= dt.datetime(date_until.year,date_until.month,date_until.day)
    with st.expander("Doc contructed:"):

        st.session_state.doc

    write = st.button("Write to DB")
    if write:
        mongo_queries.write_config(st.session_state.doc)
        st.session_state.doc = {}