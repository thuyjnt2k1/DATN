# from parsel import Selector
# from playwright.sync_api import sync_playwright
# import json, re 
# import time


# def scrape_researchgate_profile(profile: str):
#     with sync_playwright() as p:
        
#         profile_data = {
#             "basic_info": {},
#             "about": {},
#             "co_authors": [],
#             "publications": [],
#         }
        
#         browser = p.chromium.launch(headless=False, slow_mo=50)
#         page = browser.new_page()
#         page.goto(f"https://www.researchgate.net/publication/379379605_Systematic_Literature_Review_on_the_Role_of_Big_Data_in_IoT_Security", timeout=50000)
#         page.click('.js-show-more-authors')
#         page.wait_for_timeout(2000)
#         selector = Selector(text=page.content())

#         print(selector.css(".nova-legacy-v-person-list-item__title .nova-legacy-e-link span::text").getall())
#         print(selector.css(".research-detail-header-section__title::text").get())
#         print(selector.css(".js-show-more-authors .nova-legacy-e-link::text").get())

#         browser.close()
        
    
# scrape_researchgate_profile(profile="Agnis-Stibe")

from parsel import Selector
from playwright.sync_api import sync_playwright
import json


def scrape_researchgate_publications(query: str):
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36")
        
        publications = []
        page_num = 1

        while True:
            page.goto(f"https://www.researchgate.net/search/publication?q={query}&page={page_num}", timeout=80000)
            selector = Selector(text=page.content())
            
            for publication in selector.css(".nova-legacy-c-card__body--spacing-inherit"):
                title = publication.css(".nova-legacy-v-publication-item__title .nova-legacy-e-link--theme-bare::text").get().title()
                title_link = f'https://www.researchgate.net{publication.css(".nova-legacy-v-publication-item__title .nova-legacy-e-link--theme-bare::attr(href)").get()}'
                publication_type = publication.css(".nova-legacy-v-publication-item__badge::text").get()
                publication_date = publication.css(".nova-legacy-v-publication-item__meta-data-item:nth-child(1) span::text").get()
                publication_doi = publication.css(".nova-legacy-v-publication-item__meta-data-item:nth-child(2) span").xpath("normalize-space()").get()
                publication_isbn = publication.css(".nova-legacy-v-publication-item__meta-data-item:nth-child(3) span").xpath("normalize-space()").get()
                authors = publication.css(".nova-legacy-v-person-inline-item__fullname::text").getall()
                source_link = f'https://www.researchgate.net{publication.css(".nova-legacy-v-publication-item__preview-source .nova-legacy-e-link--theme-bare::attr(href)").get()}'

                publications.append({
                    "title": title,
                    "link": title_link,
                    "source_link": source_link,
                    "publication_type": publication_type,
                    "publication_date": publication_date,
                    "publication_doi": publication_doi,
                    "publication_isbn": publication_isbn,
                    "authors": authors
                })

            print(f"page number: {page_num}")

            # checks if next page arrow key is greyed out `attr(rel)` (inactive) and breaks out of the loop
            if page_num == 100:
                break
            else:
                page_num += 1


        print(json.dumps(publications, indent=2, ensure_ascii=False))

        browser.close()
        
    
scrape_researchgate_publications(query="coffee")