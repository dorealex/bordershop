import os
import json
import pymongo
import pandas as pd

df = pd.read_csv("C:\Users\Owner\OneDrive\13-work\CBSA\BorderShop\bordershop\crossings.csv")

print(df.to_dict())