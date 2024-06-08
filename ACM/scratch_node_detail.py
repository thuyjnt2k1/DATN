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

nodeType = {
  "paper": 1,
  "author": 2,
  "source ": 3
}
id = 0
cookie = False;
content_types = ['research-article', 'article', 'short-paper', 'demonstration', 'section', 'wip', 'column','poster']
df_author = pd.DataFrame(columns=['ner_id', 'link', 'name', 'orcid', 'email', 'affiliation']) 
base_url = 'https://dl.acm.org'
df_error = pd.DataFrame(columns=['id', 'url'])
file = open("log_detail.txt", "w", encoding="utf-8")

# use to scratch author
options2 = Options()
options2.headless = True
driver2 = webdriver.Chrome(options=options2)

# use to scratch affiliation
options3 = Options()
options3.headless = True
driver3 = webdriver.Chrome(options=options3)

def insert_author_node(authors, node_ids):
	global id, df_queue, df_ner, df_links
	print('\nscratching author')
	for author_container in authors:
			author = author_container.find('a')
			author_link = author.get("href")
			author_name = author.text
			if author_link in df_ner['link'].values:
				df_ner.loc[df_ner['link'] == author_link, 'count'] += 1
				file.write(f"\nauthor {author_name} existed")
				print(f"\nauthor {author_name} existed")
				node_ids.append(df_ner.loc[df_ner['link'] == author_link]['id'].values[0])
			else:
				node_ids.append(id)
				id = id + 1
				df_ner = df_ner._append({'id': id, 'name': author_name,'type': 2, 'link': author_link, 'count': 1}, ignore_index=True)
				file.write(f"\ninsert author {author_name}")
				print(f"\ninsert author {author_name}")
				df_queue = df_queue._append({'id': id, 'type': 2, 'link': author_link}, ignore_index=True)
				scratch_author_data(id, author_link)
	return df_ner, node_ids

def insert_paper_node(paper, node_ids, doi):
	global id, df_queue, df_ner, df_links, df_paper
	paper_link = paper.find("a").get("href")
	paper_name = paper.text
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
		print(doi, 'dsdasd\n')
		print(paper_name, 'dsdasd\n')
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

def scratch_author_data(ner_id, url):
	global df_author,df_error
	file.write(f"\nstart scratching {url}")
	try:
		driver2.get(base_url+url)
		element = WebDriverWait(driver2, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "list-of-institutions")))
		author_soup = BeautifulSoup(driver2.page_source,'lxml')
		author_profile = author_soup.find("div", class_="item-meta__info")
		author_name = author_profile.find("h2").text
		author_orcid = author_profile.find('a', attrs={"aria-label": "ORCID"}).get("href") if author_profile.find('a', attrs={"aria-label": "ORCID"}) else ''
		author_email = author_profile.find('a', attrs={"aria-label": "Author’s Email"}).get("href") if author_profile.find('a', attrs={"aria-label": "Author’s Email"}) else ''
		affiliation = []
		for item in author_profile.find('ul', class_="list-of-institutions").find_all('a'):
			# affiliation.insert(0, item.text)
			driver3.get(base_url+item.get('href'))
			addressSoup = BeautifulSoup(driver3.page_source,'lxml').find('div', class_='item-meta__info')
			affiliation.insert(0,  item.text.rstrip() + ' - ' + ' '.join(addressSoup.find('span', class_='address').text.split()))
		author_affiliation = '; '.join(affiliation)
		print(author_name, author_orcid, author_affiliation, '=====\n')
		df_author = df_author._append({'ner_id': ner_id, 'link': url, 'name': author_name, 'orcid': author_orcid, 'email': author_email, 'affiliation': author_affiliation}, ignore_index=True)
		file.write(f"{ner_id}, {url}, {author_name}, {author_orcid}, {author_affiliation}, {author_email}")
		file.write(f"\nsuccess scratching {url}")
	except Exception as e:
	    # Error handling and logging
	    print(f"An error occurred: {str(e)}")
	    df_error = df_error._append({id: ner_id, "url": url}, ignore_index=True)

def scratch_list_data(driver, url):
	global id, df_queue, df_ner, df_links, df_error, cookie
	print(f"\n\nstart scratching {url}")
	file.write(f"\nstart scratching {url}")
	page = 0
	has_next_page = False
	retry = 1
	entry_time = 2
	while True:
		current_url = url + f"&startPage={page}"
		file.write(f"\n\nStart scratching page {current_url}")
		try:
			driver.get(current_url)
			element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "search-result__profile-page")))
			if cookie == False: 
				driver.find_element(By.CSS_SELECTOR, '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection').click()
				cookie = True;
			try: 
				for elements in driver.find_elements(By.CSS_SELECTOR, '.removed-items-count'):
					elements.click()
			except Exception as e:
				df_error = df_error._append({id: page, "url": url}, ignore_index=True)
			soup = BeautifulSoup(driver.page_source,'lxml')
			matches = soup.find_all("li", class_="search__item")
			for match in matches:
				node_ids = []
				#get paper
				paper = match.find("h5", class_="issue-item__title")
				type = match.find("div", class_="issue-heading").text.lower()
				if type is None or type not in content_types:
					print(type)
					continue;
				doi = match.find("div", class_="issue-item__detail").find('a').get('href')
				print(doi)
				if(doi is None):
					continue
				df_ner, node_ids = insert_paper_node(paper, node_ids, doi)
				#get author list
				authors = match.find('ul', class_='loa').find_all("li")
				df_ner, node_ids = insert_author_node(authors, node_ids)

				df_links = insert_link(node_ids)

			pagination = soup.find(class_="pagination")
			has_next_page = soup.find("a", class_="pagination__btn--next")
			if(matches and has_next_page is None):
				break;
			if(has_next_page): 
				page += 1
				retry = 0
				entry_time = 2
			else: 
				retry +=1
				entry_time += 3
			if(page == 40):
				has_next_page = None
				retry = 5
			# has_next_page = False
		except Exception as e:
		    # Error handling and logging
				file.write(f"\nAn error occurred: {str(e)}")
				print(e)
				has_next_page = False
				retry +=1
				df_error = df_error._append({id: page, "url": url}, ignore_index=True)
		finally:
			if( (has_next_page is None or not has_next_page) and retry > 3):
				break;


options = Options()
options.headless = True
driver = webdriver.Chrome(options=options) # Setting up the Chrome driver
driver.implicitly_wait(10)

base_url = 'https://dl.acm.org'

df_links = pd.read_csv('new_link.csv', index_col=False)
df_queue = pd.read_csv('new_queue.csv', index_col=False)
df_ner = pd.read_csv('new_node.csv', index_col=False)
df_paper = pd.read_csv('new_paper.csv', index_col=False)
df_author = pd.read_csv('new_author.csv', index_col=False)

try:
	id = len(df_queue)
	author_count = 0
	for index, row in df_queue.iterrows():
	    if row["type"] == 2:
	    	# scratch_author_data(row["id"], driver, row["link"])
	    	current_url = base_url + row["link"] + f"/publications?pageSize=50"
	    	scratch_list_data(driver, current_url) 
	    	author_count += 1
	    	file.write(f"author count: {author_count}")
	    if row["type"] == 1:
	    	continue

except KeyboardInterrupt:
	file.write('Stop from terminal')
	print('terminal stop')
finally:
	print('Saving data')
	file.write(df_ner.to_string())
	file.write(df_links.to_string())
	# file.write(matches.to_string)
	# file.write(df_queue.to_string)
	file.write(df_paper.to_string())
	file.write(df_author.to_string())
	file.write(df_error.to_string())

	df_ner.to_csv('after_node1.csv', index=True)
	df_links.to_csv('after_link1.csv', index=True)
	df_queue.to_csv('after_queue1.csv', index=True)
	df_paper.to_csv('after_paper1.csv', index=True)
	df_author.to_csv('after_author1.csv', index=True)
	df_error.to_csv('after_error1.csv', index=True)
	print('/n close driver')
	driver.quit()
	driver2.quit()
	driver3.quit()
	print('/n close file')
	file.close()


driver.quit()