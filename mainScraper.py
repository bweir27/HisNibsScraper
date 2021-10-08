from selenium import webdriver
from bs4 import BeautifulSoup
from pymongo import MongoClient
import pprint
import json
import re
import queue
import time
import numpy

# Webdriver Setup
from Pen import Pen

options = webdriver.ChromeOptions()
print(options)
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")
# options.binary_location = "./chromedriver"
driver = webdriver.Chrome(executable_path="./chromedriver")

# The pages we want to scrape products from
product_pages = {
    # Conklin scrapes working
    "conklin": [
        "http://hisnibs.com/all_american.htm",  # Conklin All American
        "http://hisnibs.com/duragraph.htm",  # Conklin Duragraph
        "http://hisnibs.com/herringbone_3.htm",  # Conklin Herringbone
        "http://hisnibs.com/minigraph.htm",  # Conklin Minigraph
        "http://hisnibs.com/nozac.htm",  # Conklin Nozac
        "http://hisnibs.com/stylograph_2.htm",  # Conklin Stylograph
    ],
    # Monteverde scrapes working
    "monteverde": [
        "http://hisnibs.com/jewelria.htm",  # Monteverde Jewelria
        "http://hisnibs.com/intima.htm",  # Monteverde Intima
        # "http://hisnibs.com/monza.htm",  # Monteverde Monza -- FIXME: No consistent capture groups
        "http://hisnibs.com/regatta_sport.htm",  # Monteverde Regatta Sport
        "http://hisnibs.com/prima.htm",  # Monteverde Prima
    ],
    # Pilot Scrapes working
    "pilot": [
        "http://hisnibs.com/kakuno.htm",  # Pilot Kakuno
    ],
    # Dollar scrapes working
    "dollar": [
        "http://hisnibs.com/717i.htm",  # 717i
        "http://hisnibs.com/sp-10.htm",
    ]
}

# the keywords we will use to identify where those products are
product_keywords = [
    r"CK7",  # Conklin All-American, Herringbone, Minigraph, Nozax
    r"Duragraph",  # Conklin Duragraph
    r"Stylograph",
    r"MV",  # Monteverde Jewelria, Intima, Regatta Sport
    r"Prima",  # Monteverde Prima
    r"Kak",  # Pilot Kakuno, only match "kak" to ignore the headache associated with matching the umlaut over the U
    r"717i",  # Dollar 717i Solid color and 717i Transparent demonstrator pens
    r"SP-10",  # Dollar SP-10 syringe-filler
]
"""
Capture groups:
[0]: name of pen
[1]: price
[2]: sold out status
"""
capture_groups_by_brand = {
    "conklin": re.compile(
        "((?:CK7|Duragraph|Stylograph).*)(?:\s{2,})(\$\d+\.\d{2}){1,2}(?:\s*)(sold\sout)*",
        re.I),
    "monteverde": re.compile(
        "((?:MV|Prima|Stylograph).*)(?:\s{2,})(\$?[0-9]+\.[0-9]{2}){1,2}(?:\s*)(?:(?:retired,\s)?(?:permanently)?)(?:\s)(sold\sout|retired)*",
        re.I),
    # "monteverde": re.compile(
    #     "((?:MV|Prima|Stylograph).*)(?:\s{2,})(\$?\d+\.\d{2}){1,2}(?:\s*)(?:(?:retired,\s)?(?:permanently)?)(?:\s)(sold\sout|retired)*",
    #     re.I
    # ),
    "pilot": re.compile(
        "(Kak.*fountain\spen)(?:\s{2,})(\$[0-9]{1,}\.[0-9]{2,})(?:\s*)(sold\sout)*",
        re.I),
    "dollar": re.compile(
        "(?:Dollar\s)((717i|SP-10)\s.*)(\$[0-9]+\.[0-9]+)", re.I
    )
}


# MATCH_ALL = r'.*'


# def flatten(t):
#     return [item for sublist in t for item in sublist]


# Once we have the list of strings for our products, filter them with this function
def filter_product_string(product):
    return product is not None and '$' in product


def map_product_strings_to_product_names(prod_str):
    if not type(prod_str) == str:
        return None
    return prod_str.split('  ')[0]


def map_product_string_to_product_listing(prod_str):
    if not type(prod_str) == str:
        return None

    # The product names (usually) have multiple spaces after them
    prodName = prod_str.split('  ')[0]

    # Prices are formatted $##.##, but we just want the numbers
    prices = re.findall(r"\d\d\.\d\d", prod_str)
    # Handle when two prices are listed or there is a sale -- take the last price listed
    price = float(prices[len(prices) - 1])

    # if any matches are found, soldOut = True
    soldOut = len(re.findall(re.compile("sold out", flags=re.I), prod_str)) > 0
    retired = len(re.findall(re.compile("retired", flags=re.I), prod_str)) > 0

    pen = {
        "name": prodName,
        "price": price,
        "inStock": not (soldOut or retired)
    }
    # pprint.pprint(pen)
    return pen


maxFoundElems = float('-inf')
# To serve as temp DBs
penListings = []
penObjs = []
allProductListings = []

for brand in product_pages.keys():
    # Product Brand
    print(brand)
    for page in product_pages[brand]:
        # The URL of the page to be scraped
        # print(page)
        # get the contents of the page
        product_page = driver.get(page)
        soup_file = driver.page_source
        soup = BeautifulSoup(soup_file, 'html.parser')

        #  From that page, we want to start finding our capture groups
        """
        Capture Groups: 
            - keyword: pen name, up to 1st "&nbsp;"
            - /^\$[0-9]\.[0-9]$/: price
            - /sold out/: inStock
        """
        models = list()

        found = []
        # print('\n\n')
        for keyword in product_keywords:
            foundElems = driver.find_elements_by_xpath(xpath=f'//*[contains(text(), "{keyword}")]')
            # Update maxFoundElems
            if len(foundElems) > maxFoundElems:
                maxFoundElems = len(foundElems)

            for elem in foundElems:
                # print(f'elem: {elem.text}')
                if elem and hasattr(elem, 'text'):
                    elemText = str('')
                    """
                    Handle Conklin All-American Yellowstone, all Jewelria, and all Kakura listings 
                        not being contained in same element
                    """
                    nestedListing = any(keyword.startswith(x) for x in ['MV', 'Kak']) or \
                                    any(x in elem.text for x in ["Yellowstone", "Nozac"])
                    if nestedListing:
                        parent = elem.find_element_by_xpath("..")
                        elemText = parent.text
                    else:
                        elemText = elem.text
                    found.append(elemText)
                    print(elemText)

        found = list(
            map(
                map_product_string_to_product_listing,
                list(
                    filter(
                        filter_product_string,
                        found
                    )
                )
            )
        )
        # add srcUrl and brand to listing
        for p in found:
            p['srcUrl'] = page
            p['brand'] = brand
            penObjs.append(
                Pen(
                    brand=brand.capitalize(),
                    name=p['name'],
                    price=p['price'],
                    srcUrl=page,
                    inStock=p['inStock']
                )
            )
            allProductListings.append(p)
            penListings.append(p)

        print("\n\n")

print('All Product Listings:')
pprint.pprint(allProductListings)
penNames = list(map(lambda x: x['name'], allProductListings))
pprint.pprint(penNames)

# print('\nPEN OBJS:')
# for p in penObjs:
#     print(p)

print(f'Number of pens found: {len(penObjs)}')

#  TODO: BENCHMARK - just get all paragraphs, filter in based on paragraphs that start w keywords (e.g CK for Conklin or MV for Monteverde)

"""
Capture Groups: 
    - keyword: pen name, up to 1st "&nbsp;"
    - /^\$[0-9]\.[0-9]$/: price
    - /sold out/: inStock
"""

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

time.sleep(2)
driver.close()

# Now, we want to insert all of those pens into our Actual database

client = MongoClient()  # connects on default host
# client = MongoClient('localhost',27017))  # explicit connect command

db = client.hisNibsDB
# remove entire collection, i.e. all docs in hisNibsDB.pens
db.pens.drop()
# the collection we will create
penDB = db.pens

for pen in penObjs:
    penDB.insert_one({
        "brand": pen.brand,
        "name": pen.name,
        "price": pen.price,
        "srcUrl": pen.srcUrl,
        "inStock": pen.inStock
    })

for obj in penDB.find():
    print(obj)

print(penDB.count_documents({}))

print(f'MaxFoundElems:\t{maxFoundElems}')
