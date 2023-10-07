#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/24 15:16
# FileName: 基于队列的异步生产消费任务

import logging
import queue
import threading
from typing import List

from utils import pools

MAXSIZE = 10


class StopFlag:

    def __init__(self): ...


class AsyncQueue:

    def __init__(self, name='', *, maxsize=MAXSIZE):
        """

        :param name: 任务名称
        :param maxsize: 队列最大值
        """
        self.name = name
        self.q = queue.Queue(maxsize=maxsize)
        self.__producer_thread = None
        self.__consumer_thread = None

        self._result = []  # 结果

    def __repr__(self):
        return self.name

    # 解析参数
    @staticmethod
    def get_params(params):
        args = params[0] if isinstance(params[0], (tuple, list)) else []
        kwargs = params[-1] if isinstance(params[-1], dict) else {}
        return args, kwargs

    def get_result(self):
        return self._result

    def add_producer(self, callback, args_list: List = None, *, times: int = 0):
        """
        注册生产者
        :param callback: 生产者的回调方法
        :param args_list: 参数组成的数组。[[(args1, args2,), {'key1': value1, 'key2': value2}], ]
        :param times: 生产者执行的次数。当args_list为空时生效
        :return:
        """
        assert self.__producer_thread is None, '生产者已注册，不可重复注册'

        # 获取执行次数
        args_length = len(args_list) if args_list else 0
        times = args_length or times
        assert times > 0, '参数异常，导致执行次数为0'

        def producer():
            for index in range(times):
                args, kwargs = self.get_params(args_list[index])
                data = callback(*args, **kwargs)
                self.q.put(data)

        self.__producer_thread = threading.Thread(target=producer)

    def add_producer_with_pool(self, callback, args_list: List = None, *, times: int = 0, maxsize=4):
        """
        注册生产者（多协程）（Warning: 结果的顺序不可靠）
        :param callback: 生产者的回调方法
        :param args_list: 参数组成的数组
        :param times: 生产者执行的次数。当args_list为空时生效
        :param maxsize: 最大同时执行的数量
        :return:
        """
        assert self.__producer_thread is None, '生产者已注册，不可重复注册'

        # 获取执行次数
        args_length = len(args_list) if args_list else 0
        times = args_length or times
        assert times > 0, '参数异常，导致执行次数为0'

        def producer():
            """
            中间生产者，负责启动多个生产者同时运行
            :return:
            """

            def func(index):
                if args_list:
                    args, kwargs = self.get_params(args_list[index])
                    data = callback(*args, **kwargs)
                else:
                    data = callback()
                self.q.put(data)

            pools.execute_event(func, [[(i,)] for i in range(times)], maxsize=maxsize)

        self.__producer_thread = threading.Thread(target=producer)

    def add_consumer(self, callback):
        """
        注册消费者
        :param callback: 消费者回调
        :return:
        """
        assert self.__consumer_thread is None, '消费者已注册，不可重复注册'

        def consumer():
            while True:
                data = self.q.get()
                if isinstance(data, StopFlag):
                    logging.info(f'异步队列：{self.name}——消费者完成')
                    break

                self._result.append(callback(data))
                self.q.task_done()

        self.__consumer_thread = threading.Thread(target=consumer)

    def add_consumer_with_pool(self, callback, *, maxsize=4):
        """
        注册消费者（多协程）（Warning: 结果的顺序不可靠）
        :param callback:
        :param maxsize: 最大同时执行的数量
        :return:
        """
        assert self.__consumer_thread is None, '消费者已注册，不可重复注册'

        def consumer():
            """
            中间消费者，负责启动多个消费者同时运行
            :return:
            """

            def func():
                while True:
                    data = self.q.get()
                    if isinstance(data, StopFlag):
                        self.q.put(data)  # 重新放回队列，给其他协程的消费者退出使用
                        logging.info(f'异步队列：{self.name}——当前消费者已完成，等待其他协程的消费者完成...')
                        break

                    self._result.append(callback(data))
                    self.q.task_done()

            pools.execute_event(func, times=maxsize, maxsize=maxsize)

        self.__consumer_thread = threading.Thread(target=consumer)

    def run(self):
        assert self.__producer_thread, '请注册生产者：add_producer/add_producer_with_pool'
        assert self.__consumer_thread, '请注册消费者：add_consumer'

        logging.info(f'异步队列：{self.name}——启动')

        self.__producer_thread.start()
        self.__consumer_thread.start()

        self.__producer_thread.join()  # 等待生产者线程结束
        logging.info(f'异步队列：{self.name}——生产者退出')
        self.q.put(StopFlag())  # 添加队列结束标志
        self.__consumer_thread.join()  # 等待消费者线程结束
        logging.info(f'异步队列：{self.name}——消费者退出')
