#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/30 16:04
# FileName:

from typing import List

from module.spider import Origin


class Template(Origin):
    """
    模板
    """
    Name = ''

    def __init__(self, end_point, *, auths: List, **kwargs):
        super().__init__()
        self.end_point = self.resolve_end_point(end_point)
        self.__auths = [auth.strip() for auth in auths if auth.strip()] or ['其他']

        self.__title = kwargs.get('title', None)
        self.__images = []

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
        return end_point

    def run(self):
        raise Exception('模板类不可实例化')
