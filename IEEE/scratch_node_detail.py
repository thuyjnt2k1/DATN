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

nodeType = {
  "paper": 1,
  "author": 2,
  "source ": 3
}
id = 0
# df_ner = pd.DataFrame(columns=['id', 'type', 'name', 'link', 'count'])
# df_links = pd.DataFrame(columns=['from', 'to', 'count'])
# df_queue = pd.DataFrame(columns=['id', 'type', 'link']) #Để lưu trữ link tạm thời
df_author = pd.DataFrame(columns=['ner_id', 'link', 'name', 'orcid']) 
df_paper = pd.DataFrame(columns=['ner_id', 'link', 'title', 'doi'])
base_url = 'https://ieeexplore.ieee.org'
df_error = pd.DataFrame(columns=['id', 'url'])
options2 = Options()
options2.headless = True
driver2 = webdriver.Chrome(options=options2) # Setting up the Chrome driver
# driver2.implicitly_wait(10)

def insert_author_node(authors, node_ids):
	global id, df_queue, df_ner, df_links
	for author in authors:
			author_link = author.get("href")
			author_name = author.text
			if author_link in df_ner['link'].values:
				df_ner.loc[df_ner['link'] == author_link, 'count'] += 1
				print("author", author_name, "existed")
				node_ids.append(df_ner.loc[df_ner['link'] == author_link]['id'].values[0])
			else:
				node_ids.append(id)
				id = id + 1
				df_ner = df_ner._append({'id': id, 'name': author_name,'type': 2, 'link': author_link, 'count': 1}, ignore_index=True)
				print("insert author", author_name)
				df_queue = df_queue._append({'id': id, 'type': 2, 'link': author_link}, ignore_index=True)
	return df_ner, node_ids

def insert_paper_node(paper, node_ids):
	global id, df_queue, df_ner, df_links, driver2
	paper_link = paper.get("href")
	paper_name = paper.text
	if paper_link in df_ner['link'].values:
		df_ner.loc[df_ner['link'] == paper_link, 'count'] += 1
		print("paper", paper_name, "existed")
		node_ids.append(df_ner.loc[df_ner['link'] == paper_link]['id'].values[0])
	else:
		node_ids.append(id)
		id = id + 1
		df_ner = df_ner._append({'id': id, 'name': paper_name,'type': 1, 'link': paper_link, 'count': 1}, ignore_index=True)
		print("insert paper", paper_name)
		df_queue = df_queue._append({'id': id, 'type': 1, 'link': paper_link}, ignore_index=True)
		scratch_paper_data(id, driver2, paper_link)
		# driver2.quit()
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

def scratch_author_data(ner_id, driver, url):
	global df_author,df_error
	print("\nstart scratching ", url)
	try:
		driver.get(base_url+url)
		time.sleep(5) # Sleep for 6 seconds
		author_soup = BeautifulSoup(driver.page_source,'lxml')
		container = author_soup.find("div",class_="author-profile-container")
		#get bio
		author_profile = container.find("div", class_="author-bio")
		author_name = author_profile.find("h1").find("span").text
		author_orcid = author_profile.find("xpl-orcid").find("a").get("href") if author_profile.find("xpl-orcid") else ''
		df_author = df_author._append({'ner_id': ner_id, 'link': url, 'name': author_name, 'orcid': author_orcid}, ignore_index=True)
		print(ner_id, url, author_name, author_orcid)
		current_url = base_url + url + f"&returnType?history=no&returnType=SEARCH&sortType=newest"
		scratch_list_data(driver, current_url)
		print("\nsuccess scratching ", url)
	except Exception as e:
	    # Error handling and logging
	    print(f"An error occurred: {str(e)}")
	    df_error = df_error._append({id: ner_id, "url": url}, ignore_index=True)

def scratch_paper_data(ner_id, driver, url):
	global id, df_queue, df_ner, df_links, df_paper, df_error
	print("\nstart scratching ", url)
	try:
		driver.get(base_url+url)
		# time.sleep(3) # Sleep for 6 seconds
		paper_soup = BeautifulSoup(driver.page_source,'lxml')
		title = paper_soup.find("h1",class_="document-title").find("span").text
		doi = paper_soup.find("div", class_ = "stats-document-abstract-doi").find("a").text
		df_paper = df_paper._append({'ner_id':ner_id, 'link': url, 'title': title, 'doi': doi}, ignore_index=True)
		print(ner_id, url, title, doi)
	except Exception as e:
	    # Error handling and logging
	    print(f"An error occurred: {str(e)}")
	    df_error = df_error._append({id: ner_id, "url": url}, ignore_index=True)

def scratch_list_data(driver, url):
	global id, df_queue, df_ner, df_links
	print("\nstart scratching ", url)
	page = 1
	has_next_page = True
	retry = 1
	entry_time = 3
	while True:
		current_url = url + f"&pageNumber={page}"
		print("\nStart scratching page ", current_url)
		try:
			driver.get(current_url)
			time.sleep(entry_time) # Sleep for 6 seconds
			element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "xplMainContentLandmark")))
			soup = BeautifulSoup(driver.page_source,'lxml')
			matches = soup.find_all("xpl-results-item")
			for match in matches:
				node_ids = []
				#get paper
				paper = match.find("h3").find("a")
				df_ner, node_ids = insert_paper_node(paper, node_ids)

				#get author list
				authors_list = match.find("xpl-authors-name-list")
				# print('\n', authors_list);
				authors = authors_list.find_all("a")
				# print('\n', authors);
				df_ner, node_ids = insert_author_node( authors, node_ids)

				df_links = insert_link(node_ids)

			pagination = soup.find(class_="pagination-bar")
			has_next_page = soup.find("li", class_="next-btn")
			if(matches and has_next_page is None):
				break;
			if(has_next_page): 
				page += 1
				retry = 0
				entry_time = 5
			else: 
				retry +=1
				entry_time += 3
			if(page == 120):
				has_next_page = None
				retry = 5
			# has_next_page = False
		except Exception as e:
		    # Error handling and logging
		    print(f"An error occurred: {str(e)}")
		    df_error = df_error._append({id: ner_id, "url": url}, ignore_index=True)
		    df_ner.to_csv('new_node.csv', index=True)
		    df_links.to_csv('new_link.csv', index=True)
		    df_queue.to_csv('new_queue.csv', index=True)
		if( (has_next_page is None or not has_next_page) and retry > 3):
		 	break;


options = Options()
options.headless = True
driver = webdriver.Chrome(options=options) # Setting up the Chrome driver
driver.implicitly_wait(10)

# search_query = ['haha']
search_query = ['("Full%20Text%20.AND.%20Metadata":Big%20Data)']#,'("Full%20Text%20.AND.%20Metadata":Deep%20Learning)'
search_query_string = '%20OR%20'.join(search_query)

base_url = 'https://ieeexplore.ieee.org'
base_filter_url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&ranges=2010_2024_Year&refinements=ContentType:Conferences&refinements=ContentType:Journals&refinements=ContentType:Magazines"
current_url = base_filter_url + f"&queryText={search_query_string}"
# scratch_list_data(driver, current_url)

df_links = pd.read_csv('final_link.csv')
df_queue = pd.read_csv('final_queue.csv')
df_ner = pd.read_csv('final_node.csv')
id = len(df_queue)
author_count = 0
for index, row in df_queue.iterrows():
    if row["type"] == 2:
    	scratch_author_data(row["id"], driver, row["link"])    
    	author_count += 1
    	if(author_count > 120):
    		continue
    if row["type"] == 1:
      scratch_paper_data(row["id"], driver, row["link"])
    if row["id"] == 1000:
    	break

# scratch_author_data(id, driver, '/author/38247425300')
# scratch_author_data(id, driver2, '/author/37277371500')
# scratch_paper_data(id, driver, '/document/8949228')

# def test_logic():
# 	print("fuckkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
# 	options2 = Options()
# 	options2.headless = True
# 	driver2 = webdriver.Chrome(options=options2) # Setting up the Chrome driver
# 	driver2.implicitly_wait(10)
# 	scratch_paper_data(id, driver2, '/document/8949228')
# 	driver2.quit()

# t = threading.Thread(name='Test {}', target=test_logic)
# t.start()
# t.join()

print(df_ner)
print(df_links)
# print(matches)
# print(df_queue)
# print(df_paper)
# print(df_author)
print(df_error)

df_ner.to_csv('new_node.csv', index=True)
df_links.to_csv('new_link.csv', index=True)
df_queue.to_csv('new_queue.csv', index=True)
df_paper.to_csv('new_paper.csv', index=True)
df_author.to_csv('new_author.csv', index=True)

driver.quit()
driver2.quit()