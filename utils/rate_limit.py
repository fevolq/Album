#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/25 11:24
# FileName: 频率限制器

import threading
import time
from typing import Union


class RateLimiter:
    """
    频率限制器
    """

    def __init__(self, max_times: int, time_window: Union[int, float], *, name='',
                 offset: Union[int, float] = 0, loop=True):
        """

        :param max_times: 最大频率
        :param time_window: 频率的时间窗口（s）
        :param name:
        :param offset: 偏差（加锁至功能方法的时间差）
        :param loop: 遇到限制时，是否自循环等待
        """
        self.max_times = max_times
        self.time_window = time_window
        self.__name = name
        self.offset = offset
        self.loop = loop

        self.timestamps = []
        self.lock = threading.Lock()

    def __repr__(self):
        return self.__name

    def __enter__(self):
        while not self.acquire():
            if self.loop:
                time.sleep(1)  # 等待1秒后重试
            else:
                return None
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def acquire(self):
        current_time = time.time()
        self.timestamps = [t for t in self.timestamps if t >= current_time - self.time_window]

        def check_lock():
            return len(self.timestamps) < self.max_times

        if check_lock():
            with self.lock:  # 多线程同时到达，但timestamps只余一个空位，则其他线程需要重新判断条件
                if not check_lock():
                    return False
                self.timestamps.append(current_time + self.offset)
            return True
        else:
            return False


"""
# example：
import requests
from utils import pools

limiter = RateLimiter(5, 10, name='demo', offset=0.3)


# offset 即为①至②的时间间隔


def request(url):
    with limiter:  # 锁 ①
        print(time.time(), url)
        requests.get('https://www.baidu.com')  # url请求（到达） ②
        return None


# for i in range(10):
#     request(i)

pools.execute_event(request, args_list=[[(i,)] for i in range(10)])
"""
