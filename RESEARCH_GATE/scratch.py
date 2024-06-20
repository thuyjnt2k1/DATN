from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from parsel import Selector
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import codecs
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations

from webdriver_manager.chrome import ChromeDriverManager

playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False)
browser2 = playwright.chromium.launch(headless=False)
browser3 = playwright.chromium.launch(headless=False)

nodeType = {
  "paper": 1,
  "author": 2,
  "source ": 3
}
id = 0
df_ner = pd.DataFrame(columns=['id', 'type', 'name', 'link', 'count'] )
df_links = pd.DataFrame(columns=['from', 'to', 'count'])
df_queue = pd.DataFrame(columns=['id', 'type', 'link']) #Để lưu trữ link tạm thời
df_author = pd.DataFrame(columns=['ner_id', 'link', 'name', 'orcid']) 
df_paper = pd.DataFrame(columns=['ner_id', 'link', 'title', 'doi'])
base_url = 'https://www.researchgate.net/'
df_error = pd.DataFrame(columns=['id', 'url'])
content_types = ['Article', 'Research', 'Chapter', 'Conference Paper']
file = open("log.txt", "w", encoding="utf-8")
context1 = None
context2 = None
context3 = None

def insert_author_node(paper, node_ids):
	global id, df_queue, df_ner, df_links, context2
	if context2:
			context2.close()
	context2 = browser2.new_context()
	page2 = context2.new_page()
	title_container = paper.find('div', class_='nova-legacy-v-publication-item__title').find('a')
	paper_link = title_container.get("href")
	print(paper_link)
	page2.goto(f"{base_url}{paper_link}", timeout=80000)
	has_show_more = page2.query_selector_all('.js-show-more-authors')
	if(has_show_more):
		page2.click('.js-show-more-authors')
		page2.wait_for_timeout(2000)
	soup = BeautifulSoup(page2.content(),'lxml')
	authors = soup.find_all('div', class_='nova-legacy-v-person-list-item__title')
	for author in authors:
		author_container = author.find('a')
		if(author_container):
			author_link = author_container.get("href")
			author_name = author_container.text
			if(author_link.startswith('scientific-contributions')):
				continue
			if author_link in df_ner['link'].values:
				df_ner.loc[df_ner['link'] == author_link, 'count'] += 1
				file.write(f"\nauthor {author_name} existed")
				print(f"\nauthor {author_name} existed")
				node_ids.append(df_ner.loc[df_ner['link'] == author_link]['id'].values[0])
			else:
				id = id + 1
				node_ids.append(id)
				df_ner = df_ner._append({'id': id, 'name': author_name,'type': 2, 'link': author_link, 'count': 1},  ignore_index=True)
				file.write(f"\ninsert author {author_name}")
				print(f"\ninsert author {author_name}")
				df_queue = df_queue._append({'id': id, 'type': 2, 'link': author_link}, ignore_index=True)
				scratch_author_data(id, author_link)
	return df_ner, node_ids

def scratch_author_data(ner_id, url):
	global df_author,df_error, context3
	if context3:
		context3.close()
	context3 = browser.new_context()
	page3 = context3.new_page()
	file.write(f"\nstart scratching {url}")
	print(f"\nstart scratching {url}")
	try:
		print(base_url+url)
		page3.goto(base_url+url, timeout=80000)
		author_soup = BeautifulSoup(page3.content(),'lxml')
		author_profile = author_soup.find("div", class_="profile-header-details-wrapper")
		author_name = author_profile.find("h1").find(class_='nova-legacy-o-pack__item').text
		affiliation = []
		if author_profile.find('a', class_='gtm-institution-item'):
			afitext = author_profile.find('a', class_='gtm-institution-item').find('span').text
			print(f"====={afitext}===")
			affiliation.insert(0, afitext)
		if author_soup.find('div', class_="js-target-affiliations-list"):
			for item in author_soup.find('div', class_="js-target-affiliations-list").find_all('div', class_='gtm-institution-item'):
				metadata = ''
				if len(item.find_all('li', class_='nova-legacy-v-entity-item__meta-data-item')) > 1:
					metadata = ' ' + item.find_all('li', class_='nova-legacy-v-entity-item__meta-data-item')[1].find('span').text.strip() 
				else:
					if(item.find('ul', class_='nova-legacy-v-entity-item__meta-data')):
						metadata = item.find('li', class_='nova-legacy-v-entity-item__meta-data-item').text
				affiliation.insert(0, item.find('div', class_='nova-legacy-v-entity-item__title').find('b').text + metadata)
		author_affiliation = '; '.join(affiliation)
		df_author = df_author._append({'ner_id': ner_id, 'link': url, 'name': author_name, 'affiliation': author_affiliation}, ignore_index=True)
		file.write(f"{ner_id}, {url}, {author_name}, {author_affiliation}")
		print(f"{ner_id},\n {url}, \n {author_name}, \n {author_affiliation}")
		file.write(f"\nsuccess scratching {url}")
	except Exception as e:
	    # Error handling and logging
			file.write(f"\nAn error occurred: {str(e)}")
			print(f"An error occurred: {str(e)}")
			df_error = df_error._append({id: ner_id, "url": url}, ignore_index=True)

def insert_paper_node(paper, node_ids, doi):
	global id, df_queue, df_ner, df_links, df_paper
	title_container = paper.find('div', class_='nova-legacy-v-publication-item__title').find('a')
	paper_link = title_container.get("href")
	paper_name = title_container.text
	li_elements = paper.find_all('li', class_='nova-legacy-v-publication-item__meta-data-item')
	if paper_link in df_ner['link'].values:
		df_ner.loc[df_ner['link'] == paper_link, 'count'] += 1
		file.write(f"\npaper {paper_name} existed")
		print(f"\npaper {paper_name} existed")
		node_ids.append(df_ner.loc[df_ner['link'] == paper_link]['id'].values[0])
	else:
		id = id + 1
		node_ids.append(id)
		df_ner = df_ner._append({'id': id, 'name': paper_name,'type': 1, 'link': paper_link, 'count': 1}, ignore_index=True)
		file.write(f"\ninsert paper {paper_name}")
		print(f"\ninsert paper {paper_name}")
		df_queue = df_queue._append({'id': id, 'type': 1, 'link': paper_link}, ignore_index=True)
		df_paper = df_paper._append({'ner_id':id, 'link': paper_link, 'title': paper_name, 'doi': doi}, ignore_index=True)
	return df_ner, node_ids

def insert_link(node_ids):
	global df_links
	combs = list(combinations(node_ids, 2))
	for comb in combs:
		    author_from, author_to = comb
		    if ((df_links['from'] == author_from) & (df_links['to'] == author_to)).any():
		        df_links.loc[(df_links['from'] == author_from) & (df_links['to'] == author_to), 'count'] += 1
		    else:
		        df_links = df_links._append({'from': author_from, 'to': author_to, 'count': 1}, ignore_index=True)
	return df_links

def scratch_list_data(url):
	global id, df_queue, df_ner, df_links, df_error, context1, context2
	file.write(f"\n\nstart scratching {url}")
	print(f"\nstart scratching {url}")
	page = 1
	has_next_page = False
	retry = 1
	entry_time = 5
	while True:
		if context1:
			context1.close()
		print(1)
		context1 = browser.new_context()
		print(2)
		page1 = context1.new_page()

		current_url = url + f"&page={page}"
		file.write(f"\n\nStart scratching page {current_url}")
		print(f"\nStart scratching page {current_url}")
		try:
			page1.goto(current_url, timeout=80000)
			soup = BeautifulSoup(page1.content(),'lxml')
			matches = soup.find_all("div", class_="nova-legacy-v-publication-item")
			for match in matches:
				node_ids = []
				#get paper
				type = match.find("span", class_="nova-legacy-v-publication-item__badge").text
				if type is None or type not in content_types:
					continue;

				li_elements = match.find_all('li', class_='nova-legacy-v-publication-item__meta-data-item')
				doi = False
				for li in li_elements:
					if li.span and li.span.text.startswith('DOI: '):
						doi = li.span.text.split(':')[1]
						break	
				if(not doi):
					print('\nNot have doi')
					continue

				df_ner, node_ids = insert_paper_node(match, node_ids, doi)
				df_ner, node_ids = insert_author_node(match, node_ids)
				df_links = insert_link(node_ids)
			if(page == 100):
				retry = 5
			else:
				page += 1
			# has_next_page = False
		except Exception as e:
		    # Error handling and logging
				file.write(f"\nAn error occurred: {str(e)}")
				print(f"An error occurred: {str(e)}")
				has_next_page = False
				retry += 1
				df_error = df_error._append({'id': page, "url": url}, ignore_index=True)
		finally:
			df_ner.to_csv('new_node.csv', index=True)
			df_links.to_csv('new_link.csv', index=True)
			df_queue.to_csv('new_queue.csv', index=True)
			df_paper.to_csv('new_paper.csv', index=True)
			df_author.to_csv('new_author.csv', index=True)
			df_error.to_csv('error.csv', index=True)
			if(retry > 3):
				break;

# with sync_playwright() as p:
# 	browser = p.chromium.launch(headless=False)
# 	browser2 = p.chromium.launch(headless=False)
	# page.goto(f"https://www.researchgate.net/search/publication?q=Big%2BData&page=2", timeout=50000)

	# search_query = ['haha']
search_query_string = 'q=Big%2BData'
base_url = 'https://www.researchgate.net/'
base_filter_url = "https://www.researchgate.net/search/publication?"
current_url = base_filter_url + search_query_string

try:
	scratch_list_data(current_url)
	# scratch_author_data(1, 'profile/Ayorinde-Oduroye-2')
except KeyboardInterrupt:
	file.write('Stop from terminal')
finally:
	file.write(df_ner.to_string())
	file.write(df_links.to_string())
	# file.write(matches.to_string)
	# file.write(df_queue.to_string)
	file.write(df_paper.to_string())
	file.write(df_author.to_string())
	file.write(df_error.to_string())

	df_ner.to_csv('new_node.csv', index=True)
	df_links.to_csv('new_link.csv', index=True)
	df_queue.to_csv('new_queue.csv', index=True)
	df_paper.to_csv('new_paper.csv', index=True)
	df_author.to_csv('new_author.csv', index=True)
	df_error.to_csv('error.csv', index=True)
	browser.close()
	browser2.close()
	file.close()

