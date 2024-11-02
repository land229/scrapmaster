import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
import re
import sqlite3
import csv

class GoogleImagesSpider(scrapy.Spider):
    name = 'google_images'
    start_urls = ['https://www.google.com']

    def __init__(self):
        self.driver = webdriver.Chrome()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Rechercher des images avec une requête spécifique
        query = "Bénin"
        num_images = 10
        num_pages = 2

        images = []
        descriptions = []

        for page in range(num_pages):
            start_index = page * 100
            url = f"https://www.google.com/search?q={query}&tbm=isch&start={start_index}"
            self.driver.get(url)
            body = self.driver.page_source
            scrapy_selector = Selector(text=body)
            response = HtmlResponse(url=self.driver.current_url, body=body, encoding='utf-8')

            image_tags = scrapy_selector.css('img.t0fcAb')
            description_tags = scrapy_selector.css('div.bRMDJf')

            images.extend([image_tag.attrib['src'] for image_tag in image_tags])
            descriptions.extend([description_tag.xpath('string()').get() for description_tag in description_tags])

        descriptions = [re.sub(r'[^\w\s]', '', desc) for desc in descriptions]

        # Sauvegarder les données dans une base de données SQLite
        self.save_to_database(images[:num_images], descriptions[:num_images], 'benin_tourism_images.db')

        # Sauvegarder les données dans un fichier CSV
        self.save_to_csv(images[:num_images], descriptions[:num_images], 'benin_tourism_images.csv')

    def save_to_database(self, images, descriptions, database_name):
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS images (
                          id INTEGER PRIMARY KEY,
                          image TEXT,
                          description TEXT
                          )''')
        for image, description in zip(images, descriptions):
            cursor.execute("INSERT INTO images (image, description) VALUES (?, ?)", (image, description))
        conn.commit()
        conn.close()

    def save_to_csv(self, images, descriptions, filename):
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Image', 'Description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for image, description in zip(images, descriptions):
                writer.writerow({'Image': image, 'Description': description})

    def closed(self, reason):
        self.driver.quit()

