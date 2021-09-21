from selenium import webdriver
from bs4 import BeautifulSoup
import pprint
import json
import re
import queue

# Setup
options = webdriver.ChromeOptions()
print(options)
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")
# options.binary_location = "./chromedriver"
driver = webdriver.Chrome(executable_path="./chromedriver")


# where we want to start
homePageUrl = 'http://hisnibs.com/'
homePage = driver.get(homePageUrl)
soup_file = driver.page_source
soup = BeautifulSoup(soup_file, 'html.parser')

# inventory_pagenames = ['pen', 'monteverde', 'ink']
inventory_pagenames = ['conklin']

def return_to_homepage():
    homePage = driver.get(homePageUrl)
    soup_file = driver.page_source
    soup = BeautifulSoup(soup_file, 'html.parser')


def map_links_and_titles(htmlElem):
    linkUrl = ''
    if htmlElem.attrs['href']:
        linkUrl = htmlElem.attrs['href']
    text = htmlElem.text
    return {"link": linkUrl, "title": text}


def filter_inventory_pages(page):
    pageTitle = page["title"]
    if not pageTitle:
        return False
    for name in inventory_pagenames:
        if re.search(f'{name}', pageTitle, re.IGNORECASE):
            return True
    return False


def filter_product_listings(elem):
    if not elem.children:
        return False
    children = list(elem.children)
    if len(children) <= 1:
        return False
    for c in children:
        if c.name and c.name == 'b' and c.children:
            c_children = list(c.children)
            if len(c_children) > 1 and c_children[1].name == 'font':
                return True
    return False


def map_product_html_to_obj(html):
    print(html)
    details = list(list(html.children)[0].children)
    name = details[0].text.replace('\xa0', '').replace('\n', '')
    price_sec = details[1]
    print(price_sec)
    if price_sec.name == 'strike':
        price_sec = details[2]
    price = -1
    if len(list(price_sec.children)) > 0:
        price = list(price_sec.children)[0].text
    # price = details[1].text
    print(f'NAME: {name}')
    print(f'PRICE: {price}')
    return {"name": name, "price": price}


print(soup.title)
nav = soup.select("nobr > a")

# Map to just href and title
print('\nMAPPED/FILTERED Links w titles:')
navLinks = list(filter(filter_inventory_pages, list(map(map_links_and_titles, nav))))
for i in navLinks:
    print(i)


BRANDS = list(map(lambda x: x["title"].replace('\xa0', ' '), navLinks))
print('BRANDS:')
pprint.pprint(BRANDS)

# Now that we have the list of product pages we want to scrape, we can begin ...
"""
APPROACH:

build Queue of brands (name, link to dedicated page)
While Queue of brands != empty
    brand.url.pop() -> click
    build Q of brand's list of series/models (name, link to dedicated page showing color/variant offerings)
    While Queue of brand series/models != empty
        models.url.pop() -> click
        get each listing of varying colors, product codes, prices, etc.
        push Pen w/ populated info to DB
"""

# To serve as temp DB
pens = []

# while len(filtered_links) > 0:
currPage = navLinks.pop(0)
print(currPage)
driver.get(homePageUrl + currPage['link'])
soup_file = driver.page_source
soup = BeautifulSoup(soup_file, 'html.parser')

# now, we are typically at the page that displays the different models available
#   we want to make this another queue, as we will dive into each of these pages as well
models = soup.select("p[align=left] > b > a")
for m in models:
    print(m)

modelPages = list(map(map_links_and_titles, models))
for m1 in modelPages:
    print(m1)

nextPage = modelPages.pop(0)
print(nextPage)
driver.get(homePageUrl + nextPage['link'])
soup_file = driver.page_source
soup = BeautifulSoup(soup_file, 'html.parser')

# now, we are typically at the page that displays the different COLORS of the product w/ its price
models = soup.select("p[align=left]")
models_list = list(filter(filter_product_listings, models))
print('\n\nFILTERED PRODUCTS: ')
for m in models_list:
    print(m)

mapped_list = list(map(map_product_html_to_obj, models_list))
print('\n\nMAPPED PRODUCTS: ')
for m in mapped_list:
    print(m)
#
# nextPage = modelPages = list(map(map_links_and_titles, models))
# for m1 in modelPages:
#     print(m1)




defaultPen = {
    'code': 'Unknown',
    'brand': 'Unknown',
    'series': 'Unknown',
    'name': 'Unknown',
    'color': 'color',
    'price': 'Unknown',
    'img': 'Unknown',
    'srcUrl': 'Unknown'
}

# listings = driver.find_elements_by_xpath("//p[@align='left']")
# pprint.pprint(listings)
# print(listings)

# driver.close()


