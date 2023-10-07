#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/10/3 15:09
# FileName:

import logging
import re
from typing import List

from lxml import etree

from module.bean.fetch import Fetch
from module.spider import Origin


class Telegra(Origin):
    Host = 'https://telegra.ph'
    Name = 'telegra'

    def __init__(self, end_point, auths: List):
        super().__init__()
        self.end_point = self.resolve_end_point(end_point)
        self.__auths = [auth.strip() for auth in auths if auth.strip()] or ['其他']

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
        end_point = super().resolve_end_point(end_point)
        return end_point.strip().strip('/')

    def fetch_response(self, url):
        return self.fetch.request(url)['res']

    def _solve(self, resp):
        html = etree.HTML(resp.content.decode('utf-8'))
        self.__title = html.xpath('//article[@id="_tl_editor"]/h1/text()')[0]

        pattern = '<img src="(.*?)">'
        urls = re.findall(pattern, resp.text)
        self.__images = [f'{self.Host}{url}' for url in urls]

    def run(self):
        url = f'{Telegra.Host}/{self.end_point}'
        resp = self.fetch_response(url)
        if resp.status_code != 200:
            logging.error(f'origin：{Telegra.Name}，end_point：{self.end_point} 请求失败，status_code：{resp.status_code}')
            return

        self._solve(resp)


if __name__ == '__main__':
    from utils import log_util

    log_util.init_logging(stream_level='INFO')

    end_point_ = ''
    auths_ = []

    obj = Telegra(end_point=end_point_, auths=auths_)
    obj.run()
    print(obj.auths)
    print(obj.images)
    print(len(obj.images))
