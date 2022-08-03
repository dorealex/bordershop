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