from altair.vegalite.v4.schema.channels import Tooltip
from altair.vegalite.v4.schema.core import Projection
import streamlit as st
import pandas as pd
import numpy as np
from streamlit import util
import mongo_queries
from utility_cloud import get_local, return_color, make_coords, get_local_one
import altair as alt
import datetime as dt
from datetime import timedelta
from pandas.api.types import CategoricalDtype
import pydeck as pdk
from pathlib import Path
from PIL import Image
import pytz

def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

test_dict = [
  {
    "crossing name": "St-Bernard-de-Lacolle: Highway 15",
    "province": "QC",
    "id": 351,
    "timezone": "America/New_York",
    "est. arrival at border (utc)": dt.datetime(2021, 12, 4, 6, 36, 52),
    "est. wait at border (s)": 49.75,
    "total driving time": 647.4163888888888,
    "total driving distance": 2330.699,
    "route name": "I-95 N"
  },
  {
    "crossing name": "Landsdowne (Thousand Islands Bridge)",
    "province": "ON",
    "id": 456,
    "timezone": "America/New_York",
    "est. arrival at border (utc)": dt.datetime(2021, 12, 4, 5, 32, 47),
    "est. wait at border (s)": 10,
    "total driving time": 656.4591666666666,
    "total driving distance": 2363.253,
    "route name": "I-95 N and I-81 N"
  },
  {
    "crossing name": "Landsdowne (Thousand Islands Bridge)",
    "province": "ON",
    "id": 456,
    "timezone": "America/New_York",
    "est. arrival at border (utc)": dt.datetime(2021, 12, 4, 7, 18, 18),
    "est. wait at border (s)": 1.8125,
    "total driving time": 703.195,
    "total driving distance": 2531.502,
    "route name": "I-95 N and I-77 N"
  }
]




sites = mongo_queries.get_updating_list()
names = mongo_queries.ids_to_names(sites)
names = [i['name'] for i in names]
items = []
def formatWait(wait):
    wait = int(wait)
    hours = 0
    minutes = 0
    if wait > 60:
        minutes = wait // 60
        wait -= minutes * 60
    if minutes > 60:
        hours = minutes // 60
        minutes -= hours * 60
    result = f'{hours}h ' if hours > 0 else ""
    if minutes > 0:
        result = result + str(minutes)+"m "
    if wait > 0:
        result = result + str(wait)+"s "
    return result
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
    

for n in names:
    items.append(" - "+n)





st.title("Border Wait Times")

st.markdown("The current ports being polled by the API:\n"+"\n".join(items))
with st.expander('How this works'):
    ''' 
     ## Components
     This an experimentation into an automated way to measure wait times at the Canada-USA border. Various functions are being developped in a modular fashion.
     ## Methodology
     The proposed methodology for this experiment is to use the Google Maps API to estimate the wait times.

     This is achieved by requesting directions from the Google Maps API service for a trip that starts approximately 1km from the border, on the USA side, with the destination being the CBSA port of entry.

     The response provided includes both a "time in traffic" and "time without traffic", for our purposes, the difference between these two is assumed to be the wait time.
    '''
    image = Image.open('pics/trip.png')

    st.image(image, caption='Example trip for Ambassador Bridge')
    
    '''
      
     #### Pros:
    - Automated, CBSA staff do not need to provide any input
    - Google Maps is an industry leader and has a lot of data
    - This methodology is repeatable anywhere, supports splitting commercial and travellers if they are further apart
    - No hardware is required
    - The granularity of the polling rate can be modified
    #### Cons:
    - Each request costs money, ~ $0.002 USD per request.
    - Accuracy has not been confirmed
    - If there were a traffic jam to exceed the POE's trip length (~1km, depending on the nearest intersection), the actual wait time will not be estimated properly.
    ## Script
    - A very light script runs every minute.
    - Each minute, it looks up which sites are to be updated.
    - For each site identified, it looks up which "profile" it belongs to
        - A profile determines how often a location is polled for wait times
        - These profiles can be defined by hour, for example:
            - From 12:00 AM to 7:00 AM, poll at a reduced rate
            - From 7:00 AM to 7:00 PM, poll often
            - From 7:00 PM to 12:00 AM, poll at a reduced rate
        - More complex profiles (based on weekdays, month for example) are possible but not currently implemented.
    - If this location is due to be polled based on the profile, the request is sent to Google to estimate the wait times.
    - The result is stored in a database (currently: MongoDB Cloud Atlas DB, free-tier)


    ## API
    The database of stored wait times is accessible via an API service.  The service could be consumed interally, or opened up to other GC orgs, or even the public. The API service is essentially the backbone, providing the data for the various visualizations, apps, and dashboards.
    ## Display
    This app, hosted on Heroku (free-tier) is a simple Python Application using Streamlit as a front-end.
    ### User: Management
    This section is a WIP app developped with Management in mind. It allows the user to select single locations, or groups based on district and/or regions.

    The user can select the metric they want to display: the average wait time, the maximum wait time, the median wait time.

    Furthermore, the user can select a timeframe showing the most recent data for the day, week, month, quarter, year or all of the data. The data collection started in late summer 2021.



    1. Wait times table
    This is a simple table showing the latest data available for each site selected.

    2. Map
    This visualiation shows the status of selected locations on a map. The color of the dot represents the wait times.

    3. Schedule view
    This allows the user to see the "hotspots" in terms of wait times based on the day of the week, and the hour. As such, management can take some resource allocation decisions

    4. Trend
    This allows the user to see the evolution of the wait times at the location selected, for the timeframe selected

    5. Distribution
    This is a histogram that shows the distribution of the wait times.

    6. Legacy wait times comparison
    This 2 line graph directly comparing the data we're collecting with what the current wait times are, according to the current CBSA Border Wait times website (https://www.cbsa-asfc.gc.ca/bwt-taf/menu-eng.html).

    




    ### User: Traveller
    This section was developped with Travellers in mind. The goal is to provide the user with an estimate of how long they will have to wait at the border.

    The user provides where they are (in the USA), where they are going (in Canada) as well as their departure time. Optionnaly, the user can select a checkbox and have their departure location automatically determined. 

    - Once entered, more calls are made to Google Maps API to obtain the current timezone. 
    - Another request is sent to Google to provide directions
        - The response may also include a few alternative routes
        - The response is displayed on an interactive map 
    - Within those directions, the location and time of border crossing is identified
        - A query is sent to the database to match the border crossing to the route
    - For now, a simple estimate of the wait duration at that time is provided using the historical average wait at that location, for that border crossing, hour and day of the week.
        - In the future, an AI/machine learning model may be employed to provide even more accurate forecasts. It could take more factors into consideration:
            - FX Rate
            - Special events (concerts, sports, etc.)
            - Seasonal trends (Thanksgiving, Holidays, etc.)
    - A table displays the information provided
    - Perhaps this could be integrated into existing apps. Once the user obtains this information, they could begin entering ArriveCan data, etc.

    
    '''

### Removed Apr 7th for demo, added text in section above to include picture
# with st.expander('Details'):
#     md = read_markdown_file("info.md")
#     st.markdown(md)

with st.expander('User: Management'):
    with st.form(key='manager'):

        region_sel = st.selectbox('Region',['All']+mongo_queries.get_regions())
        district_sel = st.selectbox('District',['All']+mongo_queries.get_district(region_sel))
        port_choices = ['All']
        if region_sel =='All' and district_sel == 'All':
            port_choices =['Currently being updated','All']
        port_sel = st.selectbox('Border Crossing',port_choices+mongo_queries.get_ports(region_sel,district_sel))


        metric = st.selectbox("Metric", ['Average','Maximum','Median'], index=0, key=None, help=None, on_change=None, args=None, kwargs=None)
        timeframe = st.selectbox("Timeframe", ['All Time','1 week','1 day', '1 month', '1 quarter', '1 year' ])
        refresh = st.form_submit_button('Get Data')
    if refresh:
        f={}
        zoom=2
        if region_sel !='All':
            zoom=5
            f.update({'region':region_sel})
        if district_sel !='All':
            zoom=8
            f.update({'district':district_sel})
        if port_sel !='All':
            if port_sel =='Currently being updated':
                f = {'id':{'$in':sites}}
                zoom=3
            else:
                zoom=10
                f.update({'name':port_sel})
        f.update(mongo_queries.timeframe(timeframe))


        data = mongo_queries.get_last_run_by_filter(f)
        #catch empty data
        if not data:
            st.write('No data available')
        else:

            df = pd.DataFrame(data)
            
            
            df['local_time'] = df.apply(get_local,axis=1)
            df['color'] = df.apply(return_color,axis=1)
            df[['lat','long']] = df['dest'].str.split(', ',expand=True)
            pd.to_numeric(df['lat'],errors='coerce')
            pd.to_numeric(df['long'],errors='coerce')
            df.lat.astype(str).astype(float)
            df.long.astype(str).astype(float)
            df['coordinates'] = df.apply(make_coords,axis=1)
            mid_lat = (np.max(df['lat'].astype(float)) + np.min(df['lat'].astype(float)))/2
            mid_long = (np.max(df['long'].astype(float)) + np.min(df['long'].astype(float)))/2

            midpoint = (mid_lat,mid_long)
            #midpoint = (np.average(df['lat'].astype(float)), np.average(df['long'].astype(float)))

            cols=['name', 'wait', 'local_time']
            df[cols]
            layer = pdk.Layer(
                "ScatterplotLayer",
                df,
                pickable=True,
                opacity=0.8,
                stroked=True,
                filled=True,
                radius_scale=6,
                radius_min_pixels=10,
                radius_max_pixels=100,
                line_width_min_pixels=1,
                get_position='coordinates',
                get_radius=15,
                get_fill_color='color',
                get_line_color=[0, 0, 0],
            )
            view_state = pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=zoom, bearing=0, pitch=0)
            r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}\nDelay: {wait} seconds"}, map_style = 'road')
            st.write("### Map")
            st.pydeck_chart(r)

            ####
            
            f.update(mongo_queries.timeframe(timeframe))
            
            hist = pd.DataFrame(mongo_queries.get_hist_data(f)) # get the data
            hist['utc'] = hist['utc'].dt.tz_localize('UTC')
            hist['local_time'] = hist.apply(get_local,axis=1) # convert UTC to local time
            
            alt_color = {'Maximum':'max(wait):Q', 'Average':'average(wait):Q','Median':'median(wait):Q'}
            
            st.write('### Schedule View')
            scatter = alt.Chart(hist).mark_rect().encode(
                alt.Y('hours(local_time):O', title='hour of day',),
                alt.X('day(local_time):O', title='Weekday'),        
                alt.Tooltip(['hours(local_time):O','day(local_time):O',alt_color[metric]]),
                color=alt_color[metric],
                
            ).interactive()
            st.altair_chart(scatter, use_container_width=True)
            ####
            st.write('### Trend ('+timeframe+')')
            one_day = alt.Chart(hist).mark_bar().encode(
                x='local_time:T',
                y=alt_color[metric]
            )
            st.altair_chart(one_day, use_container_width=True)

            ####
            st.write('### Distribution')
            histo = alt.Chart(hist).transform_joinaggregate(
            total='count(*)'
            ).transform_calculate(
                pct='1 / datum.total'
            ).mark_bar().encode(
                alt.X('wait:Q', bin=True,title='Wait time (s)'),
                alt.Y('sum(pct):Q', axis=alt.Axis(format='%'), title='Percent of count')
            )

            # histo = alt.Chart(hist).mark_bar().encode(
            #     alt.X('wait:Q', bin=True),
            #     #y='count()',
            #     y=alt.Y('count():Q',stack=None),
            
            # )
            st.altair_chart(histo, use_container_width=True)
            ###
            f.update(mongo_queries.timeframe(timeframe))
            st.write("### Comparison to legacy system")
            f2 = f
            f2['id'] = 705
            pops = ['region', 'district', 'name']
            for p in pops:
                if p in f2.keys():
                    f2.pop(p)

            ####
            versus = pd.DataFrame(mongo_queries.prepare_legacy_compare(f2))
            #versus['local_time'] = versus.apply(get_local,axis=1),
            #f2 
            #versus

            
            
            versusChart = alt.Chart(versus).mark_line(point=True).encode(
                #alt.X('local_time:T'),
                alt.X('utc:T', title='Date'),
                alt.Y('wait:Q'),
                color='type',
                shape='name'
            ).interactive()
            
            st.altair_chart(versusChart, use_container_width=True)

with st.expander('User: Traveller'):
    st.write("## Travellers BWT Example")
    st.write('#### Note, each run of this is an API call to Google.')
    gmaps = mongo_queries.gmaps
    col = mongo_queries.col
    with st.form(key='travel'):
        
        
        start = st.text_input('Start location','Philadelphia, PA')
        use = st.checkbox('Use my current location')
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

with st.expander("Metadata"):
    st.write("""
        How many calls to the API this month:
    """)
    st.write(str(mongo_queries.queries_this_month())+" of 15500")
    daily = pd.DataFrame(mongo_queries.totals_by_day())###TODO this will need to change
    daily.rename(columns={"_id":"day", "count":"count"}, inplace=True)
    
    daily['day'] = pd.to_datetime(daily['day'])
    
    
    daily = daily.groupby('day')['count'].sum()
    daily = daily.groupby(daily.index.month).cumsum().reset_index()
    daily['month'] = daily['day'].dt.month
    daily['day'] = daily['day'].dt.date
    #daily
    chart2 = alt.Chart(daily).mark_bar().encode(
        alt.X('day:O', title='Day (UTC)'),   
        y='count',
        color=alt.Color('month', legend=None)
    )
    #st.write(daily.dtypes)
    st.altair_chart(chart2, use_container_width=True)
