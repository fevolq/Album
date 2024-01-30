#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/10/1 16:47
# FileName: 根据（监听的）爬虫任务，下发 spider 任务至 Image，并发布消息至图集队列

import json
import logging

import constant
from module.Image import Image
from module.mq import rabbit


class Producer:

    def __init__(self, queue: str = constant.MqQueue):
        self.queue = queue

        self.mq = rabbit.Param(with_dead_exchange=True)

    def produce(self, data, headers):
        """
        发布图集任务
        :param data:
        :param headers:
        :return:
        """
        logging.info(f'发送消息：{json.dumps(data, ensure_ascii=False)}')
        self.mq.producer(data=data, headers=headers)

    def start(self):
        """
        监听爬虫任务队列，下发爬虫任务
        :return:
        """
        pass

    def run(self, tasks):
        for task in tasks:
            spider = Image(**task)
            success = spider.main()
            if success:
                spider_msg = spider.get_msg()
                self.produce(spider_msg['data'], spider_msg['headers'])
            else:
                logging.error(f'spider任务失败')


if __name__ == '__main__':
    from utils import log_util

    log_util.init_logging(stream_level='INFO')

    spider_tasks = [
        # {'origin': '', 'end_point': '', 'auths': ['']},
    ]

    Producer().run(spider_tasks)
