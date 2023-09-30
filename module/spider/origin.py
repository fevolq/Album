#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/29 22:22
# FileName:

from abc import ABCMeta, abstractmethod


class Origin(metaclass=ABCMeta):
    Name = None

    def __init__(self):
        self.__title = None
        self.__auths = []  # 当来源处可解析出作者时，进行覆盖
        self.__images = []  # 完整链接
        self.__extra = {}

    @property
    @abstractmethod
    def title(self):
        return self.__title

    @property
    @abstractmethod
    def auths(self):
        return self.__auths

    @property
    @abstractmethod
    def images(self):
        return self.__images

    @property
    def extra(self):
        return self.__extra

    @classmethod
    def resolve_end_point(cls, end_point):
        """
        重新解析 end_point
        :param end_point:
        :return:
        """
        return end_point

    @abstractmethod
    def run(self): ...
