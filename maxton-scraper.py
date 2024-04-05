import requests
import re
import os
import json
from lxml import html

CATEGORY_PATTERN = r'{[^{}]*"category_id":"(\d+)","name":"([^"]+)","href":"([^"]+)"[^{}]+}'

class Scraper():
    def __init__(self) -> None:
        self.session = requests.Session()
        self.categories = []
        self.create_folder('./images')
        pass

    def create_folder(self, path):
        try:
            if not os.path.exists(path):
                os.mkdir(path)
        except:
            pass
        
    def download_image(self, get_url, image_path):
        if os.path.exists(image_path):
            return
        response = requests.get(get_url)
        with open(image_path, 'wb') as f:
            f.write(response.content)

    def load_categories(self):
        categories = []
        response = self.session.get('https://www.maxtondesign.co.uk/')
        matches = re.findall(CATEGORY_PATTERN, response.text)
        category_type = 1
        for match in matches:
            if match[1] == 'Body Kits':
                continue
            if match[1] == 'ALFA ROMEO':
                category_type = 2
            categories.append({'id': match[0], 'name': match[1], 'url': match[2].replace('\\/', '/'), 'type': category_type})
        return categories
    
    def get_products(self, category, page):
        if category['type'] == 1:
            params = {
                'route': 'product/product/getProducts', 
                'category_id': category['id'],
                'sort': 'default',
                'page': f'{page}',
                'filter_category_id': '',
                'filter_filter': '',
            }
        else:
            params = {
                'route': 'product/product/getProducts', 
                'category_id': '0',
                'sort': 'default',
                'page': f'{page}',
                'filter_category_id': category['id'],
                'filter_filter': '',
            }
        resp = self.session.get('https://www.maxtondesign.co.uk/index.php', timeout=3000, params=params)
        results = json.loads(resp.text)
        if results['products'] and len(results['products']) > 0:
            return results['products']
        return None

    def load_products(self, category):
        page = 1
        while True:
            products = self.get_products(category, page)
            if products is None:
                break
            for product in products:
                print('$$$ PRODUCT : ', product['name'])
                product['Category'] = category['name']
                self.get_product_info(product)
            page += 1
    
    def get_product_info(self, product):
        resp = self.session.get(product['href'], timeout=3000)
        tree = html.fromstring(resp.text)
        elements = tree.xpath('//table[@class="table table--clean"]/tr')
        for element in elements:
            td_elements = element.xpath('./td')
            key = td_elements[0].text_content().strip().replace(':', '')
            value = td_elements[1].text_content().strip()
            product[key] = value
        desc = tree.xpath("//div[@id = 'accordion-data1']")
        product['Description'] = html.tostring(desc[0])
        print(f'{product['product_id']}, {product['Category']}, {product['name']}, {product['price']}, {product['Brand']}, {product['Product Code']}, {product['Fits Only']}, {product.get('Collection', '')}, {product['Description']}', file=self.resfile, flush=True)
        self.create_folder(f"./images/{product['product_id']}")
        image_container = tree.xpath('//div[@class="product__image-container"]')[0]
        image_tags = image_container.xpath('.//img')
        ind = 1
        for image_tag in image_tags:
            print('--- product image ', ind)
            self.download_image(image_tag.get('src'), f"./images/{product['product_id']}/{ind}.jpg")
            ind += 1

    def start(self):
        self.resfile = open('result.csv', 'w', encoding='utf=8')
        print(f"Product Id, Category, Title, Price, Brand, Product Code, Fits Only, Collection, Description", file=self.resfile, flush=True)
        categories = self.load_categories()
        for category in categories:
            print("### CATEGORY : ", category['id'], ':', category['name'], )
            if category['type'] == 1:
                continue
            self.load_products(category)
        self.resfile.close()



def main():
    scraper = Scraper()
    scraper.start()
    
if __name__ == "__main__":
    main()