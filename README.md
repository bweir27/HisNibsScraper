# HisNibsScraper
This repository contains the code used to scrape the product listings from [HisNibs](http://hisnibs.com/), to then be used to build a proposed redesign of the site.


## Approach
The general plan for this project is to:
```angular2
build Queue of brands (name, link to dedicated page)
While Queue of brands != empty
    brand.url.pop() -> click
    build Q of brand's list of series/models (name, link to dedicated page showing color/variant offerings)
    While Queue of brand series/models != empty
        models.url.pop() -> click
        get each listing of varying colors, product codes, prices, etc.
        push Pen w/ populated info to DB
```
