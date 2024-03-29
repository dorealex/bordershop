#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import pandas as pd
import tools.mongo_queries as mongo_queries
import datetime
import schedule
from datetime import timedelta
import time
import sys
import utility_func


def get_seconds_commercial(row):
  cat = 'Commercial Flow'
  text = row[cat]
  seconds=0
  if 'minute' in text:
    if text =='1 minute':
      seconds=60
    else:
      take = len(" minutes")
      seconds = int(text[0:len(text)-take])*60
  return seconds



def get_seconds_travellers(row):
  seconds=0

  cat = 'Travellers Flow'
  text = row[cat]
  if 'minute' in text:
    if text =='1 minute':
      seconds = 60
    else:
      take = len(" minutes")
      seconds = int(text[0:len(text)-take])*60
  return seconds

def canadian_city(row):
  text = row['City']
  text = text.split("/")
  return "".join(text[:-1])

def main():
  URL = "https://www.cbsa-asfc.gc.ca/bwt-taf/menu-eng.html"
  page = requests.get(URL)

  soup = BeautifulSoup(page.text, "html.parser")

  html_table = soup.find(id='bwttaf')
  #df['commercial_seconds'] = df.apply(get_seconds_commercial,axis=1)

  html_header = html_table.select("thead")[0]
  html_body = html_table.select("tbody")[0]
  html_body = str(html_body).replace("</b>","</b></th><th>").replace("<br/>","")
  html_header  =str(html_header).replace("<th>CBSA Office</th>","<th>CBSA Office</th><th>City</th>")
  temp = "<table>"+str(html_header)+html_body+"</table>"
  df = pd.read_html(temp)[0]
  df['travellers_seconds'] = df.apply(get_seconds_commercial,axis=1)
  df['commercial_seconds'] = df.apply(get_seconds_travellers,axis=1)
  df['City'] = df.apply(canadian_city,axis=1)
  crossings = pd.read_csv("crossings.csv")
  name = crossings['name']
  df['timestamp'] = utility_func.round_to_10min(datetime.datetime.utcnow())
  for i in range(len(df)):
    office = df['CBSA Office'].iloc[i]
    id = int(mongo_queries.legacy_name_to_id(office))
    timestamp = df['timestamp'].iloc[i]
    wait = int(df['travellers_seconds'].iloc[i])
    doc = {'timestamp':timestamp,'travellers_seconds':wait}
    #print(id, office, wait)
    
    mongo_queries.col.update_one({"id":id}, {'$push':{'legacy_times':doc}})
  #mongo_queries.legacy_add(df.to_dict('records'))
  #print(df)
  return df
if __name__ == "__main__":
    main()
    schedule.every(30).minutes.until(timedelta(days=5)).do(main)
    while True:
      try:
        schedule.run_pending()
        time.sleep(1)
      except KeyboardInterrupt:
        print("User interrupted script with keyboard")
        sys.exit()
      except Exception as Argument:
        with open("error_log_legacy_scraper.txt","a") as f:
                f.write(str(Argument))
        print("error occured")