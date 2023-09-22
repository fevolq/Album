#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/2/27 16:04
# FileName:

class DbException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
