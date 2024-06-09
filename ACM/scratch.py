from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

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
cookie = False;
df_ner = pd.DataFrame(columns=['id', 'type', 'name', 'link', 'count'])
df_links = pd.DataFrame(columns=['from', 'to', 'count'])
df_queue = pd.DataFrame(columns=['id', 'type', 'link']) #Để lưu trữ link tạm thời
df_author = pd.DataFrame(columns=['ner_id', 'link', 'name', 'orcid', 'email', 'affiliation'])  
df_paper = pd.DataFrame(columns=['ner_id', 'link', 'title', 'doi'])
base_url = 'https://dl.acm.org'
df_error = pd.DataFrame(columns=['id', 'url'])
content_types = ['research-article', 'short-paper', 'demonstration', 'section', 'wip', 'column','poster']
file = open("log.txt", "w", encoding="utf-8")

# # use to scratch author
# options2 = Options()
# options2.headless = True
# driver2 = webdriver.Chrome(options=options2)

# # use to scratch affiliation
# options3 = Options()
# options3.headless = True
# driver3 = webdriver.Chrome(options=options3)

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

def insert_author_node(authors, node_ids):
	global id, df_queue, df_ner, df_links
	for author in authors:
			author_link = author.find("a").get("href")
			author_name = author.find("span").text
			if author_link in df_ner['link'].values:
				df_ner.loc[df_ner['link'] == author_link, 'count'] += 1
				file.write(f"\nauthor {author_name} existed")
				node_ids.append(df_ner.loc[df_ner['link'] == author_link]['id'].values[0])
			else:
				node_ids.append(id)
				id = id + 1
				df_ner = df_ner._append({'id': id, 'name': author_name,'type': 2, 'link': author_link, 'count': 1}, ignore_index=True)
				file.write(f"\ninsert author {author_name}")
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

def scratch_list_data(driver, url):
	global id, df_queue, df_ner, df_links, df_error, cookie
	file.write(f"\n\nstart scratching {url}")
	print(f"\nstart scratching {url}")
	page = 0
	has_next_page = False
	retry = 1
	entry_time = 2
	while True:
		current_url = url + f"&startPage={page}"
		file.write(f"\n\nStart scratching page {current_url}")
		print(f"\nStart scratching page {current_url}")
		try:
			driver.get(current_url)
			time.sleep(entry_time) # Sleep for 6 seconds
			element = WebDriverWait(driver, entry_time).until(EC.presence_of_element_located((By.ID, "pb-page-content")))
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
				doi = match.find("a", class_="issue-item__doi")
				if(doi is None):
					continue
				df_ner, node_ids = insert_paper_node(paper, node_ids, doi.get('href'))
				#get author list
				authors = match.find_all("span", class_="hlFld-ContribAuthor")
				df_ner, node_ids = insert_author_node( authors, node_ids)

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
				print(f"An error occurred: {str(e)}")
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

# search_query = ['haha']
search_query_string = '&field1=AllField&text1=Big+Data'

base_filter_url = "https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&expand=dl&AfterYear=2010&BeforeYear=2024&pageSize=50"
current_url = base_filter_url + search_query_string

try:
	for content in content_types:
		scratch_list_data(driver, current_url+'&ContentItemType='+content)
except KeyboardInterrupt:
	file.write('Stop from terminal')
	print('Stop from terminal')
finally:
	print('Stop from terminal')
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
	print('/n close driver')
	driver.quit()
	driver2.quit()
	driver3.quit()
	print('/n close file')
	file.close()

# author_count = 0
# for index, row in df_queue.iterrows():
#     if row["type"] == 2:
#     	author_count += 1
#     	if author_count > 200:
#     		continue
#     	scratch_author_data(row["id"], driver, row["link"])    
#     if row["type"] == 1:
#       scratch_paper_data(row["id"], driver, row["link"])
#     if row["id"] == 1000:
#     	break

# flag = 0
# queue_size = len(df_queue)

# while flag < queue_size:
#     # if df_queue.iloc[flag]["type"] == 2:
#         # scratch_author_data(df_queue.iloc[flag]["id"], driver, df_queue.iloc[flag]["link"])    
#     if df_queue.iloc[flag]["type"] == 1:
#         scratch_paper_data(df_queue.iloc[flag]["id"], driver, df_queue.iloc[flag]["link"])
#     file.write(flag)
#     flag += 1

# scratch_author_data(id, driver, '/author/37277371500')
# scratch_paper_data(id, driver, '/document/8949228')

