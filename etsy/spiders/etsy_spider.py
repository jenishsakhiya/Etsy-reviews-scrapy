import scrapy
import datetime
import json
from scrapy.selector import Selector
from scrapy.utils.python import to_bytes
class EtsySpider(scrapy.Spider):
    name = 'reviews'
    start_urls = [
        'https://www.etsy.com/shop/PolinaIvanova',
        'https://www.etsy.com/shop/MasterOak',
        'https://www.etsy.com/shop/reyesremedies',
        'https://www.etsy.com/shop/miasboutiquefinds',         
        'https://www.etsy.com/shop/DanisCustomCrafts'
    ]

    def parse(self, response):
        # print(response.body)
        seller_name = response.xpath(
            './/div[contains(@class, "shop-name-and-title-container")]/h1/text()'
            ).extract_first()
        
        description = response.xpath(
            './/div[contains(@class, "shop-name-and-title-container")]/p[@data-key="headline"]/text()'
            ).extract_first()
        description = description.strip() if description else None
        
        logo_url = response.xpath(
            './/div[@data-editable-img="shop-icon"]/img/@src'
        ).extract_first()
        logo_url = logo_url.split('?', 1)[0] if logo_url else None

        reported_rating = response.xpath(
            './/a[@href="#reviews"]//input[@name="rating"]/@value'
        ).extract_first()
        try:
            reported_rating = round(float(reported_rating), 1) if reported_rating else None
        except ValueError as e:
            print("Invalid value for Float-type conversion:", reported_rating)
    
        reviews_count = response.xpath(
            './/div[contains(@class, "reviews-total")]/div/div[span[contains(@class,"stars-svg")]]/following-sibling::div/text()'
        ).extract_first()
        reviews_count = reviews_count.strip(')').strip('(') if reviews_count else None

        profile_item = {}
        profile_item['seller_name'] = seller_name
        profile_item['description'] = description
        profile_item['logo_url'] = logo_url
        profile_item['reported_rating'] = reported_rating
        profile_item['reviews_count'] = reviews_count
        
        # Collecting Reviews
        reviews_list = self.collect_reviews(response, [])
        print(reviews_list)
        # next_page = response.xpath(
        #     './/nav[@role="navigation"]/ul/li/a[span[contains(text(), "Next page")]]/@href'
        # ).extract_first()
        shop_name = response.xpath(
            './/script[contains(text(), "window.Etsy")]/text()'
        ).re_first(r'"shop_name":"(.*?)"')
        page = 2
        print(shop_name)
        next_page = 'https://www.etsy.com/api/v3/ajax/bespoke/public/neu/specs/'\
                    'shop-reviews?log_performance_metrics=false&specs%5Bshop-reviews%5D%5B%5D='\
                    'Shop2_ApiSpecs_Reviews&specs%5Bshop-reviews%5D%5B1%5D%5Bshopname%5D='\
                    f'{shop_name}&specs%5Bshop-reviews%5D%5B1%5D%5Bpage%5D={page}&specs%5B'\
                    'shop-reviews%5D%5B1%5D%5Breviews_per_page%5D=10&specs%5Bshop-reviews'\
                    '%5D%5B1%5D%5Bshould_hide_reviews%5D=true&specs%5Bshop-reviews%5D%5B1%5D%5'\
                    'Bis_in_shop_home%5D=true&specs%5Bshop-reviews%5D%5B1%5D%5Bsort_option%5D=Relevancy'
        
        yield scrapy.Request(
            next_page,
            meta={
                'shop_name' : shop_name,
                'page' : 2,
                'reviews_list' : reviews_list,
                'profile_item' : profile_item
            },
            callback=self.parse_reviews
        )

    def parse_reviews(self, response):
        json_resp = json.loads(response.body)
        resp_html = json_resp['output']['shop-reviews']
        resp_html = resp_html.replace('\"','"')
        resp = Selector(text=resp_html)
        page = response.meta.get('page')
        page += 1
        print(response.url, page)
        reviews_list = response.meta.get('reviews_list')
        profile_item = response.meta.get('profile_item')
        shop_name = response.meta.get('shop_name')
        next_page = 'https://www.etsy.com/api/v3/ajax/bespoke/public/neu/specs/'\
                    'shop-reviews?log_performance_metrics=false&specs%5Bshop-reviews%5D%5B%5D='\
                    'Shop2_ApiSpecs_Reviews&specs%5Bshop-reviews%5D%5B1%5D%5Bshopname%5D='\
                    f'{shop_name}&specs%5Bshop-reviews%5D%5B1%5D%5Bpage%5D={page}&specs%5B'\
                    'shop-reviews%5D%5B1%5D%5Breviews_per_page%5D=10&specs%5Bshop-reviews'\
                    '%5D%5B1%5D%5Bshould_hide_reviews%5D=true&specs%5Bshop-reviews%5D%5B1%5D%5'\
                    'Bis_in_shop_home%5D=true&specs%5Bshop-reviews%5D%5B1%5D%5Bsort_option%5D=Relevancy'

        reviews_list = self.collect_reviews(resp, reviews_list)
        
        if page <= 3 and next_page:
            yield scrapy.Request(
                next_page,
                meta={
                    'page': page,
                    'reviews_list': reviews_list,
                    'profile_item': profile_item
                },
                callback=self.parse_reviews
            )
        else:
            output_json = {
                'profile_data': profile_item,
                'reviews': reviews_list
            }
            print(output_json)
            seller_name = profile_item['seller_name']
            filename = f'JSON/{seller_name}.json'
            with open(filename, 'w') as jsonfile:
                json.dump(output_json, jsonfile, indent=4)


    def collect_reviews(self, response, reviews_list):
        for review_li in response.xpath('.//ul[@class="reviews-list"]/li'):
            reviewer_name = review_li.xpath(
                './/p/a[contains(@href, "/people/")]/text()'
            ).extract_first()

            review_date = review_li.xpath(
                './/p[a[contains(@href, "/people/")]]/text()'
            ).extract()
            review_date = ''.join(review_date).strip().strip('on ')
            try:
                review_date = datetime.datetime.strptime(
                    review_date, "%b %d, %Y").strftime('%Y-%m-%d') if review_date else None
            except Exception as e:
                print(e)

            review_text = review_li.xpath(
                './/div/p[contains(@class, "break-word")]/text()'
            ).extract_first()
            review_text = review_text.strip() if review_text else None

            rating = review_li.xpath(
                './/input[@name="rating"]/@value'
            ).extract_first()
            try:
                rating = round(
                    float(rating), 1) if rating else None
            except ValueError as e:
                print("Invalid value for Float-type conversion:", rating)

            profile_picture_url = review_li.xpath(
                '//div[contains(@class, "flag-img")]/img/@src'
            ).extract_first()

            review_item = {}
            review_item['reviewer_name'] = reviewer_name
            review_item['review_date'] = review_date
            review_item['review_text'] = review_text
            review_item['rating'] = rating
            review_item['profile_picture_url'] = profile_picture_url
            reviews_list.append(review_item)
        return reviews_list
