import requests
from bs4 import BeautifulSoup
import pandas as pd

URL = "https://www.cbsa-asfc.gc.ca/bwt-taf/menu-eng.html"
page = requests.get(URL)

soup = BeautifulSoup(page.text, "html.parser")

html_table = soup.find(id='bwttaf')

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

print(df)