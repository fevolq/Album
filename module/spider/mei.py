#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/10/5 18:03
# FileName:

import logging
from typing import List

from lxml import etree

from module.bean.fetch import Fetch
from module.spider import Origin
from utils import pools


class Mei(Origin):
    Host = 'https://www.meimeimei.org'
    Name = 'mei'

    def __init__(self, end_point, auths: List):
        super().__init__()
        self.end_point = self.resolve_end_point(end_point)
        self.__auths = [auth.strip() for auth in auths if auth.strip()] or ['其他']

        self.__title = None
        self.__images = []

        self.pages = 1
        self.page_base_uri = ''

        self.fetch = Fetch(False)

    @property
    def title(self):
        return self.__title

    @property
    def auths(self):
        return self.__auths

    @property
    def images(self):
        return self.__images

    @classmethod
    def resolve_end_point(cls, end_point):
        return end_point.strip().strip('/')

    def fetch_again(self, url, *args, **kwargs):
        resp = self.fetch.request(url, *args, **kwargs)
        if resp and resp.status_code != 200:
            raise Exception(f'error url: {url}\n{resp.text}')
        html = etree.HTML(resp.content.decode('gbk'))
        return html, html.xpath('//div[@id="nr"]/p/img/@src')

    def fetch_selenium(self, url):
        until_conf = {'until': {'id_tag': 'nr'}}
        resp_text = self.fetch.fetch_response_with_selenium(url, until=until_conf.get('until'),
                                                            until_not=until_conf.get('until_not'))
        return etree.HTML(resp_text)

    def fetch_response(self, url, *args, **kwargs):
        html, hint = self.fetch_again(url, *args, **kwargs)
        if not hint:
            html = self.fetch_selenium(url)
        return html

    def solve(self, html):
        self.__title = html.xpath('//ul[@class="bread"]/li')[-1].xpath('./a/@title')[0]
        self.__images.append(self.solve_image(html))
        a_pages = html.xpath('//div[@class="chapterpage"]/a')
        self.pages = int(a_pages[-2].xpath('./text()')[0])
        self.page_base_uri = a_pages[-1].xpath('./@href')[0].split('_')[0]

    @classmethod
    def solve_image(cls, html):
        image_url = html.xpath('//div[@id="nr"]/p/img/@src')[0]
        return image_url

    def run(self):
        url = f'{Mei.Host}/{self.end_point}/'

        html = self.fetch_response(url, again=3)

        self.solve(html)
        logging.info(f'origin：{Mei.Name}，end_point: {self.end_point} 有 {self.pages} 页')

        # # 单线程
        # tmp_result = []
        # for page_ in range(2, self.pages + 1):
        #     logging.info(f'origin：{Mei.Name}，end_point: {self.end_point} start page: {page_}')
        #     page_url = f'{Mei.Host}/{self.end_point}/{self.page_base_uri}_{page_}.html'
        #
        #     _html, _hint = self.fetch_again(page_url, again=1)
        #
        #     _image_url = self.solve_image(_html)
        #     tmp_result.append({
        #         'image': _image_url,
        #         'hint': _hint,
        #         'page_url': page_url
        #     })

        def do_page(page):
            # 使用selenium时，不可用多线程，会造成链接覆盖。因此，失败的链接只能传出，再依次处理
            _page_url = f'{Mei.Host}/{self.end_point}/{self.page_base_uri}_{page}.html'
            _html, _hint = self.fetch_again(_page_url, again=3)
            _image_url = self.solve_image(_html) if _hint else None
            return {
                'image': _image_url,
                'hint': _hint,
                'page_url': _page_url
            }

        args = [[(page, )] for page in range(2, self.pages + 1)]
        tmp_result = pools.execute_event(do_page, args)

        for page_result in tmp_result:
            if page_result['hint']:
                image_url = page_result['image']
            else:
                html = self.fetch_selenium(page_result['page_url'])
                image_url = self.solve_image(html)
            self.__images.append(image_url)


if __name__ == '__main__':
    end_point_ = ''
    auths_ = []

    obj = Mei(end_point=end_point_, auths=auths_)
    obj.run()
    print(obj.images)
    print(len(obj.images))
