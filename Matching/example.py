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

df_acm_links = pd.read_csv('../ACM/new_link.csv', index_col=0)
df_acm_nodes = pd.read_csv('../ACM/new_node.csv', index_col=0)
df_acm_author = pd.read_csv('../ACM/new_author.csv', index_col=0)
df_acm_paper = pd.read_csv('../ACM/new_paper.csv', index_col=0)
df_acm_paper = df_acm_paper.set_index('ner_id')
df_acm_author = df_acm_author.set_index('ner_id')
base_acm_url = 'https://dl.acm.org'

df_ieee_links = pd.read_csv('../IEEE/new_link.csv', index_col=0)
df_ieee_nodes = pd.read_csv('../IEEE/new_node.csv', index_col=0)
df_ieee_author = pd.read_csv('../IEEE/new_author.csv', index_col=0)
df_ieee_paper = pd.read_csv('../IEEE/new_paper.csv', index_col=0)
df_ieee_paper = df_ieee_paper.set_index('ner_id')
df_ieee_author = df_ieee_author.set_index('ner_id')
base_ieee_url = 'https://ieeexplore.ieee.org'

df_ner = pd.DataFrame(columns=['id', 'type', 'name', 'link', 'count'])
df_links = pd.DataFrame(columns=['from', 'to', 'count'])
df_author = pd.DataFrame(columns=['ner_id', 'link', 'name', 'orcid', 'email', 'affiliation']) 
df_paper = pd.DataFrame(columns=['ner_id', 'link', 'title', 'doi'])

def prepareDocument(base_url, document):
	document['title'] = document['title'].strip()
	if document['link'].find('http') == -1:
		document['link'] = base_url + document['link']
	if document['doi'].find('http') != -1:
		document['doi'] = document['doi'].split('https://doi.org/')[1]
	return document

def prepareAuthor(base_url, author):
	author['name'] = ' '.join(re.sub(r"[^a-zA-Z0-9\.]", " ", author['name']).split())
	if author['link'].find('http') == -1:
		author['link'] = base_url + author['link']
	if 'email' in author and isinstance(author['email'], str):
		author['email'] = author['email'].split(':')[1] if len(author['email'].split(':')) > 1 else author['email']
	if isinstance(author['affiliation'], str):
		results = []
		for affiliation in author['affiliation'].split('; '):
			results.append(geocoder.geocode(affiliation)[0]['formatted'] if geocoder.geocode(affiliation) else affiliation)
		author['affiliation'] = ';'.join(results)
		print(author['affiliation'])
	if 'orcid' in author:
		author['orcid'] = author['orcid'] if isinstance(author['orcid'], str) else ''
	if 'email' in author:
		author['email'] = author['email'] if isinstance(author['email'], str) else ''
	if 'affiliation' in author:
		author['affiliation'] = author['affiliation'] if isinstance(author['affiliation'], str) else ''
	return author

def insertACM(): 
	global current_id, df_ner, df_paper, df_author , df_links
	for index, link in df_acm_links.iterrows():
		df_links = df_links._append({'from': int(link['from']) + current_id + 1, 'to': int(link['to']) + current_id + 1, 'count': int(link['count'])}, ignore_index = True)
		# print('\n=====', int(link['from']) + current_id + 1, int(link['to']) + current_id + 1)

	for index,node in df_acm_nodes.iterrows():
		if node["type"] == 1:
			try:
				current_id += 1
				document = df_acm_paper.loc[node["id"]].copy()
				document_after = prepareDocument(base_acm_url, document)
				print('\n======document=======\n', document_after)
				df_ner = df_ner._append({'id': current_id, 'name': document_after['title'], 'type': 1, 'link': document_after['link'], 'count': int(node['count'])}, ignore_index=True)
				df_paper = df_paper._append({'ner_id': current_id, 'link': document_after['link'], 'title': document_after['title'], 'doi': document_after['doi']}, ignore_index=True)
			except KeyError:
		  		print('\n=====error======\n', node['name'], ' not claim yet!')
		  		df_links = df_links.loc[~((df_links['from'] == node["id"]) | (df_links['to'] == node["id"]))]

		if node["type"] == 2:
			try:
				current_id += 1
				author = df_acm_author.loc[node['id']].copy()
				author_after = prepareAuthor(base_acm_url, author)
				print('\n======author=======\n', author_after)
				df_ner = df_ner._append({'id': current_id, 'name': author_after['name'], 'type': 2, 'link': author_after['link'], 'count': int(node['count'])}, ignore_index=True)
				df_author = df_author._append({'ner_id': current_id, 'link': author_after['link'], 'name': author_after['name'], 'affiliation': author_after['affiliation'],'email': author_after['email'], 'orcid': author_after['orcid']}, ignore_index=True)
			except KeyError:
				print('\n=====error======\n', node['name'], ' not claim yet!')
				df_links = df_links.loc[~((df_links['from'] == node["id"]) | (df_links['to'] == node["id"]))]
				# break;

def insertIEEE(): 
	global current_id, df_ner, df_paper, df_author , df_links
	for index, link in df_ieee_links.iterrows():
		df_links = df_links._append({'from': int(link['from']) + current_id, 'to': int(link['to']) + current_id, 'count': int(link['count'])}, ignore_index = True)
		print('\n=====', int(link['from']) + current_id + 1, int(link['to']) + current_id + 1)

	for index,node in df_ieee_nodes.iterrows():
		if node["type"] == 1:
			try:
				current_id += 1
				document = df_ieee_paper.loc[node["id"]].copy()
				document_after = prepareDocument(base_ieee_url, document)
				print('\n======document=======\n', document_after)
				df_ner = df_ner._append({'id': current_id, 'name': document_after['title'], 'type': 1, 'link': document_after['link'], 'count': int(node['count'])}, ignore_index=True)
				df_paper = df_paper._append({'ner_id': current_id, 'link': document_after['link'], 'title': document_after['title'], 'doi': document_after['doi']}, ignore_index=True)
			except KeyError:
		  		print('\n=====error======\n', node['name'], ' not claim yet!')
		  		df_links = df_links.loc[~((df_links['from'] == node["id"]) | (df_links['to'] == node["id"]))]
		if node["type"] == 2:
			try:
				current_id += 1
				author = df_ieee_author.loc[node['id']].copy()
				author_after = prepareAuthor(base_ieee_url, author)
				print('\n======author=======\n', author_after)
				df_ner = df_ner._append({'id': current_id, 'name': author_after['name'], 'type': 2, 'link': author_after['link'], 'count': int(node['count'])}, ignore_index=True)
				df_author = df_author._append({'ner_id': current_id, 'link': author_after['link'], 'name': author_after['name'], 'affiliation': author_after['affiliation'],'email': author_after['email'], 'orcid': author_after['orcid']}, ignore_index=True)
			except KeyError:
				print('\n=====error======\n', node['name'], ' not claim yet!')
				df_links = df_links.loc[~((df_links['from'] == node["id"]) | (df_links['to'] == node["id"]))]
				# break;

current_id = 0
insertACM()
insertIEEE()

df_ner.to_csv('new_node_test.csv', index=True)
df_links.to_csv('new_link_test.csv', index=True)
df_paper.to_csv('new_paper_test.csv', index=True)
df_author.to_csv('new_author_test.csv', index=True)

print(df_ner)
print(df_links)
print(df_author)
print(df_paper)

# name_matcher = NameMatcher()
# score = name_matcher.match_names('Mark D. Plumbley', 'M. Plumbley')
# print(score) 

