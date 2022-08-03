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
