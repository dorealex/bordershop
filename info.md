# Components
This an experimentation into an automated way to measure wait times at the Canada-USA border. Various functions are being developped in a modular fashion.
## Methodology
The proposed methodology for this experiment is to use the Google Maps API to estimate the wait times.

This is achieved by requesting directions from the Google Maps API service for a trip that starts approximately 1km from the border, on the USA side, with the destination being the CBSA port of entry.

The response provided includes both a "time in traffic" and "time without traffic", for our purposes, the differene between these two is assumed to be the wait time.

#### Pros:
- Automated, CBSA staff do not need to provide input, around the clock
- Google Maps is an industry leader and has a lot of data
- This methodology is repeatable anywhere
- No hardware is required
- The granularity of the data can be modified
#### Cons:
- Each request costs money, ~ $0.002 USD per request.
 - Depending on the needed data refresh rate, this could cost CBSA $4,000 USD/month.
- Accuracy has not been confirmed
## Scraper
- A very light script runs every minute.
- Each minute, it looks up which sites are to be updated.
- For each site identified, it looks up which "profile" it belongs to
    - A profile determines how often a location is polled for wait times
    - These profiles can be defined by hour, for example:
        - From 12:00 AM to 7:00 AM, poll at a reduced rate
        - From 7:00 AM to 7:00 PM, poll often
        - From 7:00 PM to 12:00 AM, poll at a reduced rate
    - More complex profiles (based on weekdays, month for example) are possible but not currently implemented.
- If this location is due to be polled based on the profile, the request is sent to google to estimate the wait times.
- The result is stored in a database (currently: MongoDB Cloud Atlas DB, free-tier)


## API
The database of stored wait times is accessible via an API service. Currently, this is hosted on the CBSA AWS environment. The service could be consumed interally by CBSA, or opened up to other GC orgs, or even the public. The API service is essentially the backbone, providing the data for the various visualizations, apps, and dashboards.
## Display
This app, hosted on Heroku (free-tier) is a simple Python Application using Streamlit as a front-end.
### User: Management
This section is a WIP app developped with CBSA management in mind. It allows the user to select single locations, or groups based on district and/or regions.

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

6. Legacy wait times comparison **(currently disabled)**
This 2 line graph directly comparing the data we're collecting with what the current wait times are, according to the current CBSA Border Wait times website (https://www.cbsa-asfc.gc.ca/bwt-taf/menu-eng.html).

This has been disabled for performance reason.




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
- Perhaps this could be integrated into existing CBSA apps. Once the user obtains this information, they could begin entering ArriveCan data, etc.


### Metadata
This is a simply a graph to keep track of how many calls to the Google Maps API service are made per month. Currently, the goal is to stay within the $200 USD free-tier for this service. 

## Future
- Develop AI/ML for predictions.
    - **requires** more data.
- Provide flexible times for Travellers:
    - Current wait is estimated to be X, but if you wait an hour, it might be less, etc.