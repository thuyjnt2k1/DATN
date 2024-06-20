import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import re
from namematcher import NameMatcher
from opencage.geocoder import OpenCageGeocode
import math
import copy

api_key = "68020a7f39dd42fd9dc58971638403e6"
geocoder = OpenCageGeocode(api_key)

df_affiliation = pd.DataFrame(columns=['affiliation', 'result'])
df_affiliation.set_index('affiliation')
df_acm_author = pd.read_csv('../IEEE/new_author.csv', index_col=0)
df_affiliation = pd.read_csv('affiliation.csv', index_col='affiliation')

def getAffiliation(affiliation):
	global df_affiliation
	result = ''
	formatted_affiliation = affiliation.strip()
	formatted_affiliation = ' '.join(formatted_affiliation.strip().split())
	try:
		result = df_affiliation.loc[formatted_affiliation,'result']
		print('\nda co')
	except KeyError:
		print('\nchua co')
		getGeocode = geocoder.geocode(formatted_affiliation)
		if(len(getGeocode) == 0):
			result = formatted_affiliation
		else:
			result = getGeocode[0]['formatted']
		df_affiliation.loc[formatted_affiliation] = result
	return result

try: 
	for index, author in df_acm_author.iterrows():
		print(author)
		if isinstance(author['affiliation'], str):
			results = []
			for affiliation in author['affiliation'].split('; '):
				results.append(getAffiliation(affiliation))
			print(results)
			author['affiliation'] = ';'.join(results)
			print(author['affiliation'])
except Exception as e:
	print(str(e))
finally:
	df_affiliation.to_csv('affiliation.csv')
	print(df_affiliation)

df_affiliation.to_csv('affiliation.csv')
print(df_affiliation)