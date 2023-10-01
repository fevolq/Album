#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/10/1 18:02
# FileName:

import io

from PIL import Image


class ReImage:
    """
    更改图片属性
    """

    def __init__(self, binary: bytes = None):
        """

        :param binary: 图片二进制
        """
        self.image = self.__load(io.BytesIO(binary))

    @classmethod
    def __load(cls, binary):
        return Image.open(binary)

    def resize_small(self, rate=1, max_size: int = None, resample=Image.LANCZOS):
        """
        将图片尺寸变小
        :param rate:
        :param max_size: width 和 height 中最大的可选尺寸
        :param resample:
        :return:
        """
        width, height = self.image.size
        if max_size:
            width_rate = min(max_size / width, 1)
            height_rate = min(max_size / height, 1)
        else:
            width_rate = height_rate = 1

        rate = min(rate, width_rate, height_rate)
        size = (int(width * rate), int(height * rate))
        self.image = self.image.resize(size, resample)

        # print(f'({width}, {height}) => {self.image.size}')
        return self

    def get_value(self, fmt='JPEG'):
        """

        :param fmt: 图片的类型
        :return:
        """
        with io.BytesIO() as output:
            self.image.save(output, format=fmt)
            binary = output.getvalue()

        self.image = self.__load(io.BytesIO(binary))
        return binary
