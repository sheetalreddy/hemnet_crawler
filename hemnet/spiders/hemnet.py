import scrapy
import time
import json
#import cfscrape
#from fake_useragent import UserAgent
from .decoder import Decoder
from scrapy import signals
from pydispatch import dispatcher
import csv



class QuotesSpider(scrapy.Spider):
    name = "hemnet"
    # *** Change this url for your prefered search from hemnet.se ***
    start_urls = ['https://www.hemnet.se/salda/bostader?location_ids%5B%5D=17821&expand_locations=1000&item_types%5B%5D=villa&item_types%5B%5D=radhus&item_types%5B%5D=bostadsratt']
    globalIndex = 0
    results = []
    dict_writer = None
    


    def __init__(self):

        dispatcher.connect(self.spider_closed, signals.spider_closed)



    def parse(self, response):
        
        for ad in response.css("ul#search-results.sold-results > li.sold-results__normal-hit > a::attr('href')"):
            adUrl = ad.get()
            #ua = UserAgent(cache=False)
            #token, agent = cfscrape.get_tokens(adUrl, ua['google chrome'])
            #yield scrapy.Request(url=adUrl, cookies=token, headers={'User-Agent': agent}, callback=self.parseAd)
            time.sleep(3)
            yield scrapy.Request(url=adUrl, callback=self.parseAd)


        nextPage = response.css("a.next_page::attr('href')").get()
        if nextPage is not None:
            time.sleep(2)
            yield response.follow(nextPage, callback=self.parse)


    def parseAd(self, response):
        
        address = response.css("h1.hcl-heading.hcl-heading--size1::text").extract()
        address = address[1].replace('\n','')
        sold_date = response.css("p.sold-property__metadata.qa-sold-property-metadata >time::attr('datetime')").get()
        slutprice = response.css("div.sold-property__top-details > div.sold-property__price > span.sold-property__price-value::text").get()
        print(sold_date)
        attrLabel=[]
        attrValue=[]
        for attr in response.css("div.sold-property__details > dl.sold-property__price-stats > dt.sold-property__attribute"):
            attrLabel.append(attr.css("dt.sold-property__attribute::text").get())
        for attr in response.css("div.sold-property__details > dl.sold-property__price-stats > dd.sold-property__attribute-value"):
            price=attr.css("dd.sold-property__attribute-value::text").extract()
            if price!= None:
                if len(price) > 1:
                  price[1]=price[1].replace(u'\xa0','')
                  price_last=price[1].replace('\n','')
                else:
                  price_last=price[0].replace(u'\xa0','')

            attrValue.append(price_last)
        for attr in response.css("div.sold-property__details > dl.sold-property__attributes > dt.sold-property__attribute"):
            attrLabel = attrLabel + [(attr.css("dt.sold-property__attribute::text").get())]
        
        for attr in response.css("div.sold-property__details > dl.sold-property__attributes > dd.sold-property__attribute-value"):
            price=attr.css("dd.sold-property__attribute-value::text").get()
            if price!= None:
                price=price.replace(u'\xa0','')
            attrValue.append(price)

        res = dict(zip(attrLabel, attrValue))
        res['address']=address
        res['Sale price'] = slutprice
        res['Sale Date'] = sold_date
        self.results.append(res)
        


    def spider_closed(self, spider):
        with open('hemnet.json', 'w') as fp:
            json.dump(self.results, fp)
        with open('housing_västerås.csv', 'w',newline='') as output_file:
            #names = ['Pris per kvadratmeter','Tomträttsavgäld','Sale price','Sale Date', 'Begärt pris', 'Prisutveckling', 'Bostadstyp', 'Balkong', 'Våning','Upplåtelseform', 'Antal rum', 'Boarea', 'Biarea', 'Uteplats', 'Byggår', 'Avgift/månad', 'Driftskostnad','address','Tomtarea']
            self.dict_writer = csv.DictWriter(output_file, self.results[0].keys())
            self.dict_writer.writeheader()
            self.dict_writer.writerows(self.results)
