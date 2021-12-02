import streamlit as st
import datetime as dt


import mongo_queries
import pandas as pd



with st.expander('Traveller'):
    st.write("## Travellers BWT Example")
    st.write('#### Note, each run of this is an API call to Google.')
    gmaps = mongo_queries.gmaps
    col = mongo_queries.col







    




    use = st.checkbox('Use my current location')

    if not use:
        start = st.text_input('Start location','Orlando, FL')


    stop = st.text_input('Destination in Canada','Laval, QC')
    when = st.date_input('When are you leaving?',dt.datetime.now())
    time = st.time_input('At what time?', dt.datetime.now())

    submit = st.button('Estimate')
    dtime = dt.datetime.combine(when,time)

    if submit:
        if use:
            loc = gmaps.geolocate()['location']
        
        else:
            loc = gmaps.geocode(start)[0]['geometry']['location']
        st.components.v1.iframe(mongo_queries.mapmaker(start = loc, dest =stop,key=mongo_queries.api_key),height=400)

        df = pd.DataFrame(mongo_queries.get_trip_wait(loc,stop,dtime))
        cols = ['route name', 'crossing name']
        df
        st.write('''
        #### TO-DO
        - Convert to local time
        - Fix table height
        - Fix number formatting
        - Fix column ordering
        ''')
