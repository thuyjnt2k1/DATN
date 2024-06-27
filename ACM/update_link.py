import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import re
from opencage.geocoder import OpenCageGeocode
import math
import copy

df_acm_links = pd.read_csv('after_link3.csv', index_col=0)
df_acm_nodes = pd.read_csv('after_node3.csv', index_col=0)
print(df_acm_links.loc[222])

def get_neighbor(node_id):
	neighbor_nodes = []
	neighbor_rows = df_acm_links[(df_acm_links['from'] == node_id)]
	if(len(neighbor_rows > 0)):
		row = neighbor_rows.index[0]
		count = 0
		while True:
			next_id = int(row) + count
			next_row = df_acm_links.loc[next_id]
			if(next_row['from'] == node_id):
				count += 1
				neighbor_nodes.append(next_row['to'])
			else:
				break
	return neighbor_nodes


for index, node in df_acm_nodes.iterrows():
	id = node['id']
	if node['id'] > 4043:
		break;
	if node['type'] == 2:
		continue
	neighbors = get_neighbor(node['id'])
	print('======================', id, neighbors)
	for neighbor in neighbors:
		if(neighbor < id):
			print('\nupdate', id)
			row = df_acm_links[(df_acm_links['from'] == neighbor) & (df_acm_links['to'] == id) | (df_acm_links['from'] == id) & (df_acm_links['to'] == neighbor)]
			df_acm_links.loc[row.index, 'to'] = int(neighbor - 1)
			df_acm_links.loc[row.index, 'from'] = int(id)
			print('\nupdate', row.index, neighbor -1, id)
			for x in neighbors:
				if(x == neighbor):
					continue
				row = df_acm_links[((df_acm_links['from'] == neighbor) & (df_acm_links['to'] == x)) | ((df_acm_links['from'] == x) & (df_acm_links['to'] == neighbor))]
				df_acm_links.loc[row.index, 'from'] = int(neighbor - 1)
				df_acm_links.loc[row.index, 'to'] = int(x)
				print('\n update', row.index,  neighbor - 1, x)

	# print('\n=====', int(link['from']) + current_id, int(link['to']) + current_id)

print(df_acm_links)
df_acm_links.to_csv('new_link_test.csv', index=True)
