import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import re
from opencage.geocoder import OpenCageGeocode
import math
import copy

df_acm_links = pd.read_csv('new_link.csv', index_col=0)
df_links = pd.DataFrame(columns=['from', 'to', 'count'])
print(df_acm_links)

for index, link in df_acm_links.iterrows():
	df_links = df_links._append({'from': int(link['from']) + 1 , 'to': int(link['to']) + 1 , 'count': int(link['count'])}, ignore_index = True)
	# print('\n=====', int(link['from']) + current_id, int(link['to']) + current_id)
print(df_links)
df_links.to_csv('new_link_test.csv', index=True)
