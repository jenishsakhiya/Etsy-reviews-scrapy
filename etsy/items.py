# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ProfileItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    seller_name = scrapy.Field()
    description = scrapy.Field()
    logo_url = scrapy.Field()
    reported_rating = scrapy.Field()
    reviews_count = scrapy.Field()
    pass


class ReviewItem(scrapy.Item):
    reviewer_name = scrapy.Field()
    review_text = scrapy.Field()
    review_date = scrapy.Field()
    rating = scrapy.Field()
    profile_picture_url = scrapy.Field()
