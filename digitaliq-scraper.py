import os
import re
import requests
from lxml import html

MAIN_URL = "https://digitaliq.gr"
CATEGORY_PATTERN = r'<a href="(https://digitaliq.gr/product-category/([^"]+)/)">([^<>]+)</a>'

class Extractor:
    def __init__(self):
        self.session = requests.Session()

    def start(self):
        self.csvfile = open('result.csv', 'w', encoding='utf-8')
        self.create_folder('./images')
        print('Categories, Title, Price, Extra Price, Product Id', file=self.csvfile, flush=True)
        categories = self.load_categories()
        for name in categories.keys():
            category = categories[name]
            print('#'*category['level'], ' ', category['title'])
            if not category['leaf']:
                continue
            self.load_product_categories(category)
            
        self.csvfile.close()

    def download_image(self, get_url, image_name):
        if os.path.exists(image_name):
            return
        response = requests.get(get_url)
        with open(image_name, 'wb') as f:
            f.write(response.content)

    def extract_products(self, url):
        resp = self.session.get(url)
        tree = html.fromstring(resp.text)
        nav_element = tree.xpath('//main/nav')[0]
        categories = nav_element.text_content()
        product_elements = tree.xpath('//main/div/ul/li')
        for product_element in product_elements:
            title_tag = product_element.xpath('./div[@class="product-content"]/h5/a')[0]
            price_tags = product_element.xpath('./div[@class="product-content"]/div/h5/ins')
            if len(price_tags) > 0:
                price_tag = price_tags[0]
                del_price_tag = product_element.xpath('./div[@class="product-content"]/div/h5/del')[0]
                product = {
                    'Categories': categories,
                    'Title': title_tag.text_content(),
                    'Price': price_tag.text_content(),
                    'Extra Price': del_price_tag.text_content(),
                    'url': title_tag.get('href'),
                }
            else:
                price_tag = product_element.xpath('./div[@class="product-content"]/div/h5')[0]
                product = {
                    'Categories': categories,
                    'Title': title_tag.text_content(),
                    'Price': price_tag.text_content(),
                    'Extra Price': '',
                    'url': title_tag.get('href'),
                }
            self.extract_product(product)

    def create_folder(self, path):
        try:
            if not os.path.exists(path):
                os.mkdir(path)
        except:
            pass

    def extract_product(self, product):
        resp = self.session.get(product['url'])
        print('$$$ : ', product['Title'])
        tree = html.fromstring(resp.text)
        # image_container = tree.xpath('//div[@class="slick-track"]')
        image_container = tree.xpath('//div[@class="agni-single-products-gallery-wrapper"]')[0]
        images = image_container.xpath('.//img')
        product_id = tree.xpath('//main/div')[1].get('id')
        self.create_folder(f'./images/{product_id}')
        ind = 1
        for image in images:
            print(f'--- product image {ind}')
            self.download_image(image.get('src'), f"./images/{product_id}/{ind}.jpg")
            ind += 1
        print(f"{product['Categories']}, {product['Title']}, {product['Price']}, {product['Extra Price']}, {product_id}", file=self.csvfile, flush=True)

    def load_product_categories(self, category):
        resp = self.session.get(category['url'])
        tree = html.fromstring(resp.text)
        href_elements = tree.xpath('//main/div/ul/li/a')
        for href in href_elements:
            print('#'*(category['level'] + 1), href.text_content().strip())
            self.extract_products(href.get('href'))

    def load_categories(self):
        categories = dict()
        resp = self.session.get(MAIN_URL)
        matches = re.findall(CATEGORY_PATTERN, resp.text)
        for match in matches:
            name = match[1]
            parent_name = "/".join(name.split("/")[:-1])
            if len(parent_name) == 0:
                categories[name] = {'url': match[0], 'title': match[2], 'level': len(name.split("/")), 'leaf': True}
            else:
                categories[name] = {'url': match[0], 'title': match[2], 'level': len(name.split("/")), 'leaf': True}
                categories[parent_name]['leaf'] = False
        return categories

def main():
    extracotr = Extractor()
    extracotr.start()

if __name__ == "__main__":
    main()