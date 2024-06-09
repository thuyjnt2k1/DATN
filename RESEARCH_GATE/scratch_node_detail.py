from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from bs4 import BeautifulSoup
import codecs
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
import threading
import time
from webdriver_manager.chrome import ChromeDriverManager
import threading
import sys, signal
from playwright.sync_api import sync_playwright

nodeType = {
  "paper": 1,
  "author": 2,
  "source ": 3
}
id = 0
cookie = False;
content_types = ['Article', 'Research', 'Chapter', 'Conference Paper']
df_author = pd.DataFrame(columns=['ner_id', 'link', 'name', 'orcid', 'email', 'affiliation']) 
df_links = pd.read_csv('new_link.csv')
df_queue = pd.read_csv('new_queue.csv')
df_ner = pd.read_csv('new_node.csv')
df_paper = pd.read_csv('new_paper.csv')
base_url = 'https://www.researchgate.net/'
df_error = pd.DataFrame(columns=['id', 'url'])
file = open("log_detail.txt", "w", encoding="utf-8")

def insert_author_node(paper_soup, paper, node_ids):
	global id, df_queue, df_ner, df_links
	title_container = paper.find('div', class_='nova-legacy-v-publication-item__title').find('a')
	paper_link = title_container.get("href")
	authors = paper_soup.find_all('div', class_='nova-legacy-v-person-list-item__title')
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
				node_ids.append(df_ner.loc[df_ner['link'] == author_link]['id'].values[0])
			else:
				node_ids.append(id)
				id = id + 1
				df_ner = df_ner._append({'id': id, 'name': author_name,'type': 2, 'link': author_link, 'count': 1},  ignore_index=True)
				file.write(f"\ninsert author {author_name}")
				df_queue = df_queue._append({'id': id, 'type': 2, 'link': author_link}, ignore_index=True)
	return df_ner, node_ids

def insert_paper_node(paper_soup, match, node_ids):
	global id, df_queue, df_ner, df_links, df_paper
	title_container = match.find('div', class_='nova-legacy-v-publication-item__title').find('a')
	paper_name = title_container.text
	paper_link = title_container.get("href")
	li_elements = paper_soup.find(class_='research-detail-header-section__metadata-after-square-logo').find_all('div', class_='nova-legacy-e-text')
	doi = ''
	for li in li_elements:
		if li.span and li.text.startswith('DOI: '):
			doi = li.span.text.split(':')[1]
			break	
	if paper_link in df_ner['link'].values:
		df_ner.loc[df_ner['link'] == paper_link, 'count'] += 1
		file.write(f"\npaper {paper_name} existed")
		node_ids.append(df_ner.loc[df_ner['link'] == paper_link]['id'].values[0])
	else:
		node_ids.append(id)
		id = id + 1
		df_ner = df_ner._append({'id': id, 'name': paper_name,'type': 1, 'link': paper_link, 'count': 1}, ignore_index=True)
		file.write(f"\ninsert paper {paper_name}")
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

def scratch_author_data(ner_id, page, browser2, url):
	global df_author,df_error
	file.write(f"\nstart scratching {url}")
	try:
		page.goto(base_url+url, timeout=80000)
		author_soup = BeautifulSoup(page.content(),'lxml')
		print(author_soup)
		author_profile = author_soup.find("div", class_="profile-header-details-wrapper")
		author_name = author_profile.find("h1").text
		affiliation = []
		if author_profile.find('a', class_='gtm-institution-item'):
			affiliation.insert(0, author_profile.find('a', class_='gtm-institution-item').find('span').text.strip())
		if author_soup.find('div', class_="js-target-affiliations-list"):
			for item in author_soup.find('div', class_="js-target-affiliations-list").find_all('div', class_='gtm-institution-item'):
				metadata = '-' + item.find('ul', class_='nova-legacy-v-entity-item__meta-data').text.strip() if item.find('ul', class_='nova-legacy-v-entity-item__meta-data') else ''
				affiliation.insert(0, item.find('div', class_='nova-legacy-v-entity-item__title').find('b').text + metadata)
		author_affiliation = '; '.join(affiliation)
		print(author_name, author_affiliation, '=====\n')
		df_author = df_author._append({'ner_id': ner_id, 'link': url, 'name': author_name, 'affiliation': author_affiliation}, ignore_index=True)
		file.write(f"{ner_id}, {url}, {author_name}, {author_affiliation}")
		publications = author_soup.find('div', id='research-items').find('div', class_='profile-content-item')
		scratch_list_data(publications, page, browser2, url, 1)
		file.write(f"\nsuccess scratching {url}")
	except Exception as e:
	    # Error handling and logging
			file.write(f"\nAn error occurred: {str(e)}")
			print(f"An error occurred: {str(e)}")
			df_error = df_error._append({id: ner_id, "url": url}, ignore_index=True)

def scratch_list_data(publications, page, browser2, url, current_page):
	global id, df_queue, df_ner, df_links, df_error, cookie
	file.write(f"\nstart scratching list of {url}")
	print(f"\nstart scratching list of {url}")
	has_next_page = False
	try:
		matches = publications.find_all("div", class_="nova-legacy-v-publication-item")
		print('fuck')
		context = browser2.new_context()
		new_page = context.new_page()
		count = 0;
		for match in matches:
			print('fuckyou')
			node_ids = []
			#get paper
			type = match.find("span", class_="nova-legacy-v-publication-item__badge").text
			if type is None or type not in content_types:
				continue;
			count += 1
			if(count > 10):
				count = 0 
				context.close()
				context = browser2.new_context()
				new_page = context.new_page()
			title_container = match.find('div', class_='nova-legacy-v-publication-item__title').find('a')
			paper_link = title_container.get("href")
			new_page.goto(f"{paper_link}", timeout=80000)
			has_show_more = new_page.query_selector_all('.js-show-more-authors')
			if(has_show_more):
				new_page.click('.js-show-more-authors')
				new_page.wait_for_timeout(2000)
			paper_soup = BeautifulSoup(new_page.content(),'lxml')
			df_ner, node_ids = insert_paper_node(paper_soup, match, node_ids)
			#get author list
			df_ner, node_ids = insert_author_node(paper_soup, match, node_ids)
			df_links = insert_link(node_ids)
		pagination = publications.find(class_="nova-legacy-c-card__footer-content")
		print(pagination)
		has_next_page = pagination.find("a", attrs={"rel": "next"})
		print(has_next_page)
		if(has_next_page): 
			print('\nhave next page')
			context.close()
			current_page += 1
			page.goto(f"{base_url}{url}/{current_page}", timeout=80000)
			soup = BeautifulSoup(page.content(),'lxml')
			author_soup = BeautifulSoup(page.content(),'lxml')
			new_publications = author_soup.find('div', id='research-items').find('div', class_='profile-content-item')
			scratch_list_data(new_publications, page, browser2, url, current_page)
	except Exception as e:
    # Error handling and logging
		file.write(f"\nAn error occurred: {str(e)}")
		has_next_page = False
		print(f"An error occurred: {str(e)}")
		df_error = df_error._append({id: page, "url": url}, ignore_index=True)
	finally:	
		context.close()

with sync_playwright() as p:
	browser = p.chromium.launch(headless=False)
	page = browser.new_page()
	browser2 = p.chromium.launch(headless=False)
	# page.goto(f"https://www.researchgate.net/search/publication?q=Big%2BData&page=2", timeout=50000)
	# search_query = ['haha']
	base_url = 'https://www.researchgate.net/'
	try:
		id = len(df_queue)
		author_count = 0
		for index, row in df_queue.iterrows():
		    if row["type"] == 2:
		    	scratch_author_data(row["id"], page, browser2, row["link"])    
		    	author_count += 1
		    	file.write(f"author count: {author_count}")
		    if row["type"] == 1:
		    	continue
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

		df_ner.to_csv('after_node.csv', index=True)
		df_links.to_csv('after_link.csv', index=True)
		df_queue.to_csv('after_queue.csv', index=True)
		df_paper.to_csv('after_paper.csv', index=True)
		df_author.to_csv('after_author.csv', index=True)
		df_error.to_csv('after_error.csv', index=True)
		browser.close()
		browser2.close()
		file.close()


