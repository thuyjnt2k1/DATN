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

def insert_author_node(new_page, paper, node_ids):
	global id, df_queue, df_ner, df_links
	title_container = paper.find('div', class_='nova-legacy-v-publication-item__title').find('a')
	paper_link = title_container.get("href")
	print(paper_link)
	new_page.goto(f"{base_url}{paper_link}", timeout=80000)
	has_show_more = new_page.query_selector_all('.js-show-more-authors')
	if(has_show_more):
		new_page.click('.js-show-more-authors')
		page.wait_for_timeout(2000)
	soup = BeautifulSoup(new_page.content(),'lxml')
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
				node_ids.append(df_ner.loc[df_ner['link'] == author_link]['id'].values[0])
			else:
				node_ids.append(id)
				id = id + 1
				df_ner = df_ner._append({'id': id, 'name': author_name,'type': 2, 'link': author_link, 'count': 1},  ignore_index=True)
				file.write(f"\ninsert author {author_name}")
				df_queue = df_queue._append({'id': id, 'type': 2, 'link': author_link}, ignore_index=True)
	return df_ner, node_ids

def insert_paper_node(paper, node_ids):
	global id, df_queue, df_ner, df_links, df_paper
	title_container = paper.find('div', class_='nova-legacy-v-publication-item__title').find('a')
	paper_link = title_container.get("href")
	paper_name = title_container.text
	li_elements = paper.find_all('li', class_='nova-legacy-v-publication-item__meta-data-item')
	doi = ''
	for li in li_elements:
		if li.span and li.span.text.startswith('DOI: '):
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

def scratch_list_data(driver, browser2, url):
	global id, df_queue, df_ner, df_links, df_error
	file.write(f"\n\nstart scratching {url}")
	print(f"\nstart scratching {url}")
	page = 1
	has_next_page = False
	retry = 1
	entry_time = 5
	while True:
		context = browser2.new_context()
		new_page = context.new_page()
		current_url = url + f"&page={page}"
		file.write(f"\n\nStart scratching page {current_url}")
		print(f"\nStart scratching page {current_url}")
		try:
			driver.goto(current_url, timeout=80000)
			soup = BeautifulSoup(driver.content(),'lxml')
			matches = soup.find_all("div", class_="nova-legacy-v-publication-item")
			for match in matches:
				node_ids = []
				#get paper
				type = match.find("span", class_="nova-legacy-v-publication-item__badge").text
				if type is None or type not in content_types:
					continue;
				df_ner, node_ids = insert_paper_node(match, node_ids)
				#get author list
				df_ner, node_ids = insert_author_node(new_page, match, node_ids)
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
				retry +=1
				df_error = df_error._append({id: page, "url": url}, ignore_index=True)
		finally:
			context.close()
			if(retry > 3):
				break;

with sync_playwright() as p:
	browser = p.chromium.launch(headless=False)
	page = browser.new_page()
	browser2 = p.chromium.launch(headless=False)
	# page.goto(f"https://www.researchgate.net/search/publication?q=Big%2BData&page=2", timeout=50000)

	# search_query = ['haha']
	search_query_string = 'q=Big%2BData'

	base_url = 'https://www.researchgate.net/'
	base_filter_url = "https://www.researchgate.net/search/publication?"
	current_url = base_filter_url + search_query_string

	try:
		scratch_list_data(page, browser2, current_url)
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


