#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/30 20:57
# FileName:

import logging
from typing import List

from lxml import etree

from module.bean.fetch import Fetch
from module.spider import Origin


class MmmRed(Origin):
    Host = 'https://mmm.red'
    Name = 'mmm'

    def __init__(self, end_point, auths: List = None):
        super().__init__()
        self.end_point = self.resolve_end_point(end_point)
        self.__auths = auths or []

        self.__title = None
        self.__images = []

        self.fetch = Fetch()

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

    def fetch_response(self, url):
        return self.fetch.request(url)['res']

    def _solve(self, html):
        self.__title = html.xpath('//div[@class="content"]/div[1]/h3/span/text()')[0]
        # self.__auths = [html.xpath('//div[@class="content"]/div[2]/a[2]/text()')[0]]  # 多作者无法解析

        images_div = html.xpath('//div[@id="masonry"]/div')
        for div in images_div:
            fancybox = div.xpath('./@data-fancybox')
            if not fancybox or fancybox[0] != 'gallery':
                continue

            image = 'https:' + div.xpath('./img/@data-original')[0]
            self.__images.append(image)

    def run(self):
        url = f'{MmmRed.Host}/art/{self.end_point}'
        resp = self.fetch_response(url)
        if resp.status_code != 200:
            logging.error(f'origin：{MmmRed.Name}，end_point：{self.end_point} 请求失败，status_code：{resp.status_code}')
            return

        self._solve(etree.HTML(resp.content.decode('utf-8')))


if __name__ == '__main__':
    end_point_ = ''
    auths_ = []

    obj = MmmRed(end_point=end_point_, auths=auths_)
    obj.run()
    print(obj.images)
    print(len(obj.images))
