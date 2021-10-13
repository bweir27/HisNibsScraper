# HisNibsScraper
This repository contains the Python code used to scrape the product listings from [HisNibs.com](http://hisnibs.com/), 
insert them into a MongoDB collection, which will then be used to build a proposed redesign of the site.

## Setup
In order for this webscraper to function properly, you must download the version of `chromedriver` that matches your version of Google Chrome, and place it at the root-level of this directory.
`chromedriver` can be dowloaded [here](https://chromedriver.chromium.org/downloads)

## Approach
The general plan for this project is to:
1. Gather the URLs of each brand's product pages
2. Determine keywords that can be used to differentiate actual product listings from the rest of the page's content (very few selectors used on original site, so we are forced to use text/Regex-based keywords)
3. Begin scraping
    1. For each brand/URL pairing ...
    2. Use [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to extract elements that contain one of the keywords
    3. Filter the list of found elements by those that contain a "$" (price) in their text
    4. Map each of the filtered elements' text to `Pen` objects using Regular Expressions, focusing on Name, Price, and whether or not the product is SoldOut
    5. Add the `brand` and `srcURL` (where the pen was found on the current site) attributes to each `Pen` object found on this page, using the known values from the enclosing loop
    6. Append each of the new `Pen` objects to a master list
4. Insert each of the `Pen`s in the master list (see step 3vi) into a MongoDB Collection

