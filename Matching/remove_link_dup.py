import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
import pandas as pd
from namematcher import NameMatcher
import time
from collections import defaultdict
from scipy.spatial.distance import pdist
from opencage.geocoder import OpenCageGeocode
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import re
from multiprocessing import Process, Manager
import multiprocessing
from scipy.spatial.distance import cdist
import json
import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

def remove_duplicate_link():
    global df_links
    for i, link in df_links.iterrows():
        if(link['from'] > link['to']):
            from_value = link['from']
            to = link['to']
            print('\n', i,link['from'], link['to'] )
            df_links.loc[i]['from'] = to
            df_links.loc[i]['to'] = from_value
df_links = pd.read_csv('final_link.csv', index_col=0)
remove_duplicate_link()
# df_unique = df_links.groupby(['from', 'to'], as_index=False).sum()
print(df_links)
# df_unique = df_links.drop_duplicates(subset=['from', 'to'])
merged_df = df_links.groupby(['from', 'to']).agg({'count': 'sum'}).reset_index()
print(merged_df)
# removed_rows = df_links[~df_links.set_index(['from', 'to']).index.isin(merged_df.set_index(['from', 'to']).index)]
# print(removed_rows)
duplicated_mask = df_links.duplicated(subset=['from', 'to'], keep=False)
duplicates_over_3 = df_links[duplicated_mask].groupby(['from', 'to']).filter(lambda x: len(x) > 3)
removed_duplicates = df_links[duplicated_mask]
print(duplicates_over_3)
merged_df.to_csv('remove_duplicate_link.csv')