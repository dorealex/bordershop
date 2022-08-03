# Contents of ~/my_app/pages/page_2.py
import streamlit as st
import pytz
import datetime as dt
import tools.mongo_queries as mongo_queries
from tools.utility_cloud import formatWait, get_local_one



st.markdown("# Traveller Use Case")
st.sidebar.markdown("# Traveller Use Case")

def writeRoute(route):
    name = route['crossing name']   #1
    prov = route['province']            #2
    utc_arriv = route['est. arrival at border (utc)']
    wait = route['est. wait at border (s)'] #3
    routeName = route['route name'] #4
    timezone = route['timezone']    #5
    local_arrive = get_local_one(utc_arriv, timezone)
    cols = st.columns(5)
    st.write('-----')
    cols[0].write('**Route**')
    cols[0].write(routeName)
    cols[1].write('**Crossing Name**')
    cols[1].write(name)
    cols[2].write('**Province**')
    cols[2].write(prov)
    cols[3].write('**Est. Border Arrival Time (Local Time)**')
    cols[3].write(local_arrive)
    cols[4].write('**Est. Wait**')
    cols[4].write(formatWait(wait))


st.write('#### Note, each run of this is an API call to Google.')
gmaps = mongo_queries.gmaps
col = mongo_queries.col
with st.form(key='travel'):
    
    
    start = st.text_input('Start location','Philadelphia, PA')
    use = st.checkbox('Use my current location  *only works outside Canada*')
    stop = st.text_input('Destination in Canada','Peterborough, ON')
    tcol = st.columns(2)
    when = tcol[0].date_input('When are you leaving?',dt.datetime.now())
    time = tcol[1].time_input('Time?', dt.datetime.now())
    submit = st.form_submit_button('Estimate')
dtime = dt.datetime.combine(when,time)
gc = gmaps.geocode(stop)
for x in gc[0]['address_components']:
    if 'country' in x['types']:
        ctry = x['short_name']
        if ctry == 'CA':
            stop_ok = True
        else:
            stop_ok = False
if submit:
    if use:
        pos = gmaps.geolocate()['location']        
        #pos = {'lat': 48.512680, 'lng': -111.871895} # 48.512680, -111.871895
        gc = gmaps.reverse_geocode(pos)
    else:
        #loc = gmaps.geocode(start)[0]['geometry']['location']
        gc = gmaps.geocode(start)
    for x in gc[0]['address_components']:
        if 'country' in x['types']:
            ctry = x['short_name']
    if ctry == 'US' and stop_ok:    
        loc = gc[0]['geometry']['location']
        #loc = gmaps.geocode(start)[0]['geometry']['location']
    
        dep_tz = gmaps.timezone(loc)['timeZoneId']        
        dtime = dtime.astimezone(pytz.timezone(dep_tz))        
        st.components.v1.iframe(mongo_queries.mapmaker(start = loc, dest =stop,key=mongo_queries.api_key),height=400)
        routeinfo = mongo_queries.get_trip_wait(loc,stop,dtime)
        #routeinfo = test_dict
        #df = pd.DataFrame(routeinfo)
        
        for r in routeinfo:        
            writeRoute(r)
