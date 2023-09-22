#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/22 17:35
# FileName:

from utils import util


def gen_unique_origin_album(origin: str, end_point: str) -> str:
    """
    对不同来源的图集，生成唯一字符
    :param origin:
    :param end_point:
    :return:
    """
    return util.md5(f'{origin}.{end_point}')


def gen_uid(name: str) -> str:
    """
    生成uid
    :param name:
    :return:
    """
    return util.md5(name.lower())


class Header:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __eq__(self, other):
        """
        任意属性相等即可
        :param other:
        :return:
        """
        kwargs = self.__dict__
        other_kwargs = other.__dict__

        for k, v in kwargs.items():
            if k not in other_kwargs:
                continue
            if v == other_kwargs[k]:
                return True

        return False

    def get_value(self):
        return self.__dict__
