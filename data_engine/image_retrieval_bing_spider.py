import requests
from lxml import etree
import os
from multiprocessing.dummy import Pool
import json
import time
from PIL import Image

class BingImagesSpider:
    thread_amount = 1000
    per_page_images = 30
    count = 0
    success_count = 0
    ignore_chars = ['|', '.', '，', ',', '', '',
                    '/', '@', ':', '：', ';', '；', '[', ']', '+', ' - ']
    image_types = ['jpg', 'png','jpeg']
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    }
    bing_image_url_pattern = 'https://www.bing.com/images/async?q={}&first={}&count={}&mmasync=1'

    def __init__(self, domain, keywords, amount, save_url, json_path):
        self.domain = domain
        self.json_path = json_path
        self.keywords = keywords
        self.keyword = None
        self.amount = amount
        self.path = save_url
        self.item_list = []
        self.thread_pool = Pool(self.thread_amount)

    def __del__(self):
        self.thread_pool.close()
        self.thread_pool.join()

    def request_homepage(self, url):
        return requests.get(url, headers=self.headers)

    def parse_homepage_response(self, response):
        tree = etree.HTML(response.text)
        m_list = tree.xpath('//*[@class="imgpt"]/a/@m')

        info_list = []
        for m in m_list:
            dic = json.loads(m)
            image_title = dic['t']
            for char in self.ignore_chars:
                image_title = image_title.replace(char, ' ')
            image_title = image_title.replace(
                "   ", " ").replace("  ", " ").strip()

            image_type = dic['murl'].split('.')[-1]
            if image_type not in self.image_types:
                image_type = 'jpg'

            info = dict()
            info['image_title'] = image_title
            info['image_type'] = image_type
            info['image_md5'] = dic['md5']
            info['image_url'] = dic['murl']

            info_list.append(info)
        return info_list

    def request_and_save_image(self, info):
        try:
            bing_tag = info['image_title']
            filename = '{}.{}'.format(
                self.domain + '_' + str(int(time.time() * 1e6))[-10:], info['image_type']) 
            filepath = os.path.join(self.path, filename)

            response = requests.get(info['image_url'], headers=self.headers, timeout=1.5)
            with open(filepath, 'wb') as fp:
                fp.write(response.content)
            
            self.count += 1
            self.success_count += 1
            self.item_list.append({
                'image_path': filename,
                'bing_tag': bing_tag,
                'retrieval_keyword': self.keyword,
                'source': "bing",
            })

        except Exception as e:
            self.count += 1

    def deduplication(self, info_list):
        result = []
        md5_set = set()
        for info in info_list:
            if info['image_md5'] not in md5_set:
                result.append(info)
                md5_set.add(info['image_md5'])
        return result

    def run_all(self):
        print("*** spider ***")
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        self.keyword = None
        self.item_list = []
        for keyword in self.keywords:
            self.keyword = keyword
            print(f'keyword: {keyword}')
            self.run()
            time.sleep(5)

        print('done, save total ' +
              str(len(self.item_list)) + ' images.')
        with open(self.json_path, 'a', encoding='utf-8') as output_file:
            for item in self.item_list:
                output_file.write(json.dumps(item, ensure_ascii=False) + '\n')

    def run(self):
        homepage_urls = []
        for i in range(int(self.amount/self.per_page_images * 3) + 1):
            url = self.bing_image_url_pattern.format(
                self.keyword, i*self.per_page_images, self.per_page_images)
            homepage_urls.append(url)
        print('homepage_urls len {}'.format(len(homepage_urls)))

        homepage_responses = self.thread_pool.map(
            self.request_homepage, homepage_urls)

        info_list = []
        for response in homepage_responses:
            try:
                result = self.parse_homepage_response(response)
                info_list += result
            except Exception as e:
                pass
        print('info amount before deduplication', len(info_list))

        info_list = self.deduplication(info_list)
        print('info amount after deduplication', len(info_list))
        info_list = info_list[: self.amount]
        print('info amount after split', len(info_list))

        self.thread_pool.map(self.request_and_save_image, info_list)

        print('{} done. Total {} successfully downloaded, {} failed.'.format(self.keyword,
                                                                             self.success_count, self.count - self.success_count))


def read_keywords(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines]
        return list(set(lines))

def remove_broken(image_path):
    images = os.listdir(image_path)
    i = 0
    for image_name in images:
        try:
            image = Image.open(image_path + "/" + image_name)
        except Exception as e:
            i+= 1
            os.remove(image_path + "/" + image_name)
            continue
    print("remove ", i," images")


if __name__ == "__main__":
    root_path = 'MMInstruct'
    domain_list = ["poster"]
    os.makedirs(os.path.join(root_path, 'bing_images'), exist_ok=True)
    os.makedirs(os.path.join(root_path, 'bing_images/json'), exist_ok=True)
    for domain in domain_list:
        keywords = read_keywords(root_path + "keywords/" + domain + ".txt")
        print(f'keywords: {keywords}') 
        count = 15 
        save_path = os.path.join(root_path, 'bing_images', domain)
        os.makedirs(save_path, exist_ok=True)
        json_path = root_path + '/bing_images/json/' + domain + '.jsonl'
        spider = BingImagesSpider(domain, keywords, count, save_path, json_path)
        spider.run_all()

        remove_broken(save_path)
        
    print('done all.')
