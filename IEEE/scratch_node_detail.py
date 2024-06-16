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
from playwright.sync_api import sync_playwright, expect

nodeType = {
  "paper": 1,
  "author": 2,
  "source ": 3
}
id = 0
# df_ner = pd.DataFrame(columns=['id', 'type', 'name', 'link', 'count'])
# df_links = pd.DataFrame(columns=['from', 'to', 'count'])
# df_queue = pd.DataFrame(columns=['id', 'type', 'link']) #Để lưu trữ link tạm thời
# df_author = pd.DataFrame(columns=['ner_id', 'link', 'name', 'orcid', 'email', 'affiliation']) 
# df_paper = pd.DataFrame(columns=['ner_id', 'link', 'title', 'doi'])
base_url = 'https://ieeexplore.ieee.org'
df_error = pd.DataFrame(columns=['id', 'url'])
file = open("log_detail.txt", "w", encoding="utf-8")
new_author_node_list = []

playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False)
page = browser.new_page()
browser2 = playwright.chromium.launch(headless=False)
page2 = browser2.new_page()
browser3 = playwright.chromium.launch(headless=False)
page3 = browser3.new_page()

def insert_author_node(authors, node_ids):
	global id, df_queue, df_ner, df_links, new_author_node_list
	for author in authors:
			author_link = author.get("href")
			author_name = author.text
			if author_link in df_ner['link'].values:
				df_ner.loc[df_ner['link'] == author_link, 'count'] += 1
				print("author", author_name, "existed")
				node_ids.append(df_ner.loc[df_ner['link'] == author_link]['id'].values[0])
				# scratch_author_data(df_ner.loc[df_ner['link'] == author_link]['id'].values[0], driver2, author_link)
			else:
				id = id + 1
				node_ids.append(id)
				new_author_node_list.append(id)
				df_ner = df_ner._append({'id': id, 'name': author_name,'type': 2, 'link': author_link, 'count': 1}, ignore_index=True)
				print("insert author", author_name)
				df_queue = df_queue._append({'id': id, 'type': 2, 'link': author_link}, ignore_index=True)
				scratch_author_data(id, author_link)
	return df_ner, node_ids

def insert_paper_node(paper, node_ids):
	global id, df_queue, df_ner, df_links
	paper_link = paper.get("href")
	paper_name = paper.text
	if paper_link in df_ner['link'].values:
		df_ner.loc[df_ner['link'] == paper_link, 'count'] += 1
		print("paper", paper_name, "existed")
		node_ids.append(df_ner.loc[df_ner['link'] == paper_link]['id'].values[0])
		# scratch_paper_data(df_ner.loc[df_ner['link'] == paper_link]['id'], driver2, paper_link)
	else:
		id = id + 1
		node_ids.append(id)
		df_ner = df_ner._append({'id': id, 'name': paper_name,'type': 1, 'link': paper_link, 'count': 1}, ignore_index=True)
		print("insert paper", paper_name)
		df_queue = df_queue._append({'id': id, 'type': 1, 'link': paper_link}, ignore_index=True)
		scratch_paper_data(id, paper_link)
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
	print("\nstart scratching ", url)
	try:
		page3.goto(base_url+url)
		# time.sleep(5) # Sleep for 6 seconds
		waitelement = page3.wait_for_selector("#authorProfile", timeout = 10000)
		author_soup = BeautifulSoup(page3.content(),'lxml')
		container = author_soup.find("div",class_="author-profile-container")
		#get bio
		author_profile = container.find("div", class_="author-bio")
		author_name = author_profile.find("h1").find("span").text
		author_orcid = author_profile.find("xpl-orcid").find("a").get("href") if author_profile.find("xpl-orcid") else ''
		affiliations = []
		for item in author_profile.find('div', class_='current-affiliation').find_all('div', recursive=False):
			if(len(item.find_all('div')) == 1):
				affiliations.insert(0, item.text)
			else:
				address = []
				for i, div_element in enumerate(item.find_all('div')):
					if i>0:
						address.append(div_element.text)
				affiliations.insert(0, ' '.join(address))
		affiliation_text = '; '.join(affiliations)
		df_author = df_author._append({'ner_id': ner_id, 'link': url, 'name': author_name, 'orcid': author_orcid, 'affiliation': affiliation_text}, ignore_index=True)
		print(ner_id, url, author_name, author_orcid, affiliation_text)
		current_url = base_url + url + f"&returnType?history=no&returnType=SEARCH&sortType=newest"
		print("\nsuccess scratching ", url)
	except Exception as e:
	    # Error handling and logging
	    print(f"An error occurred: {str(e)}")
	    df_error = df_error._append({id: ner_id, "url": url}, ignore_index=True)

def scratch_paper_data(ner_id, url):
	global id, df_queue, df_ner, df_links, df_paper, df_error
	print("\nstart scratching ", url)
	try:
		page2.goto(base_url+url)
		waitelement = page2.wait_for_selector(".document-main", timeout = 10000)
		paper_soup = BeautifulSoup(page2.content(),'lxml')
		title = paper_soup.find("h1",class_="document-title").find("span").text
		doi = paper_soup.find("div", class_ = "stats-document-abstract-doi").find("a").text
		df_paper = df_paper._append({'ner_id':ner_id, 'link': url, 'title': title, 'doi': doi}, ignore_index=True)
		print(ner_id, url, title, doi)
	except Exception as e:
	    # Error handling and logging
	    print(f"An error occurred: {str(e)}")
	    df_error = df_error._append({id: ner_id, "url": url}, ignore_index=True)

def scratch_list_data(url):
	global id, df_queue, df_ner, df_links, page, df_error, new_author_node_list
	print("\nstart scratching ", url)
	current_page = 1
	has_next_page = False
	retry = 1
	entry_time = 10000
	new_author_node_list = []
	while True:
		current_url = url + f"&pageNumber={current_page}"
		print("\nStart scratching page ", current_url)
		try:
			page.goto(current_url, timeout = entry_time)
			waitelement = page.wait_for_selector(".List-results-items", timeout = entry_time)
			# element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "xplMainContentLandmark")))
			soup = BeautifulSoup(page.content(),'lxml')
			matches = soup.find_all("xpl-results-item")
			for match in matches:
				node_ids = []
				#get paper
				paper = match.find("h3").find("a")
				if(paper is None):
					continue
				df_ner, node_ids = insert_paper_node(paper, node_ids)

				#get author list
				authors_list = match.find("xpl-authors-name-list")
				# print('\n', authors_list);
				authors = authors_list.find_all("a")
				# print('\n', authors);
				df_ner, node_ids = insert_author_node(authors, node_ids)
				print('\n*****insert link*******\n',node_ids)
				df_links = insert_link(node_ids)
			pagination = soup.find(class_="pagination-bar")
			has_next_page = soup.find("li", class_="next-btn")
			if(matches and has_next_page is None):
				break;
			if(has_next_page):
				current_page += 1
				retry = 0
				entry_time = 10000
			else: 
				retry +=1
				entry_time += 3000
		except Exception as e:
				retry +=1
				entry_time += 3000
				page.close()
				page = browser.new_page(no_viewport=True)
				file.write(f"\nAn error occurred: {str(e)}")
				print(f"An error occurred: {str(e)}")
				df_error = df_error._append({id: id, "url": url}, ignore_index=True)
		print('\n******\n',retry, has_next_page)
		if((has_next_page is None or not has_next_page) and retry > 3):
		 	break;
	print('\n**************\n',new_author_node_list)
	for node in new_author_node_list:
		new_node = df_ner.loc[df_ner['id'] == node, 'link'].values[0]
		current_url = base_url + new_node + f"&returnType?history=no&returnType=SEARCH&sortType=newest"
		scratch_list_data(current_url)


# options = Options()
# options.headless = True
# driver = webdriver.Chrome(options=options) # Setting up the Chrome driver
# driver.implicitly_wait(10)

# search_query = ['haha']
search_query = ['("Full%20Text%20.AND.%20Metadata":Big%20Data)']#,'("Full%20Text%20.AND.%20Metadata":Deep%20Learning)'
search_query_string = '%20OR%20'.join(search_query)

base_url = 'https://ieeexplore.ieee.org'
base_filter_url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&ranges=2010_2024_Year&refinements=ContentType:Conferences&refinements=ContentType:Journals&refinements=ContentType:Magazines"
current_url = base_filter_url + f"&queryText={search_query_string}"
# scratch_list_data(driver, current_url)

df_links = pd.read_csv('new_link.csv', index_col=0)
# df_queue = pd.read_csv('new_queue.csv')
df_ner = pd.read_csv('new_node.csv', index_col=0)
df_author = pd.read_csv('new_author.csv', index_col=0)
df_paper = pd.read_csv('new_paper.csv', index_col=0)

try:
	# scratch_list_data('https://ieeexplore.ieee.org/author/37283921800&returnType?history=no&returnType=SEARCH&sortType=newest')
	df_queue = df_ner[df_ner['type'] == 2].nlargest(20, 'count').reset_index(drop=True)
	print(df_queue)
	id = len(df_ner)
	author_count = 0
	index = 0
	while True:
		if(index == len(df_queue)):
			break;
		row = df_queue.iloc[index]
		print('=====================================\n',index, row)
		index = index + 1
		if row["type"] == 2:
			# scratch_author_data(row["id"], driver, row["link"])
			current_url = base_url + row["link"] + f"&returnType?history=no&returnType=SEARCH&sortType=newest"
			# current_url = base_url + row["link"] + f"/publications?pageSize=50"
			print(current_url)
			scratch_list_data(current_url)
			author_count += 1
			file.write(f"author count: {author_count}")
		elif row["type"] == 1:
			continue;		

	# for index, row in df_queue.iterrows():
	#     if row["type"] == 2:
	#     	current_url = base_url + row["link"] + f"&returnType?history=no&returnType=SEARCH&sortType=newest"
	#     	scratch_list_data(driver, current_url)
	#     	author_count += 1
	#     	if(author_count > 120):
	#     		continue
	#     if row["type"] == 1:
	#     	continue
	#     if row["id"] == 1000:
	#     	break
except KeyboardInterrupt:
		file.write('Stop from terminal')
finally:
# scratch_author_data(id, driver, '/author/37087584615')
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
	print(df_queue)
	print(df_paper)
	print(df_author)
	print(df_error)

	df_ner.to_csv('after_node1.csv', index=True)
	df_links.to_csv('after_link1.csv', index=True)
	df_queue.to_csv('after_queue1.csv', index=True)
	df_paper.to_csv('after_paper1.csv', index=True)
	df_author.to_csv('after_author1.csv', index=True)

	browser.close()
	browser2.close()
	browser3.close()
	file.close()