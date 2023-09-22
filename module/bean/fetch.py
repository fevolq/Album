#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/5/5 13:58
# FileName:

import random

import requests


agent_list = [
   'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',
   'Mozilla/5.0 (Linux; Android 9; SM-N9500 Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/76.0.3809.89 Mobile Safari/537.36 T7/11.20 SP-engine/2.16.0 baiduboxapp/11.20.0.14 (Baidu; P1 9)',
   'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50',
   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
   'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
]


def get_user_agent():
    return random.choice(agent_list)


class Fetch:

    def __init__(self, headless=True): ...
        # self.browser = Browser(headless)

    @classmethod
    def request(cls, url, method='GET', headers=None, again=1, **kwargs):
        """
        requests请求
        :param url:
        :param method:
        :param headers:
        :param again: 异常重复次数
        :param kwargs:
        :return: {res: 请求的返回, times: 请求的次数}
        """
        result = {'res': None, 'times': 0}

        def do():
            result['times'] += 1
            _headers = {
                'user-agent': get_user_agent(),
            }
            headers_ = {} if headers is None else headers
            _headers.update(headers_)

            return requests.request(method, url, headers=_headers, **kwargs)

        num = 0
        while num <= again - 1:
            try:
                result['res'] = do()
                break
            except:
                num += 1

        return result
