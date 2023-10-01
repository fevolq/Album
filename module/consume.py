#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/23 16:44
# FileName: 监听图集任务队列，并下发给 album

import logging

import constant
from module import album
from module.bean import bean
from module.mq import rabbit


class Consume:

    def __init__(self, queue: str = constant.MQ_QUEUE):
        self.queue = queue

        self.mq = rabbit.Param(with_dead_exchange=True)

    def start(self, origin: str = None, end_point: str = None):
        """
        监听消息队列
        :param origin: 指定来源
        :param end_point: 指定图集资源
        :return:
        """
        logging.info(f'监听配置：origin： {origin}，end_point：{end_point}')
        header = bean.Header(origin=origin, end_point=end_point) if any([origin, end_point]) else None

        self.mq.start_consuming(album.run, headers=header)
        if self.mq.is_closed():
            self.start(origin=origin, end_point=end_point)

    def stop(self):
        self.mq.stop_consuming()


if __name__ == '__main__':
    import getopt
    import sys

    from utils import log_util

    log_util.init_logging(stream_level='INFO')

    Consume().start()

    # origin_ = None
    # end_point_ = None
    #
    # opts, _ = getopt.getopt(sys.argv[1:], "o:e:", ["origin=", "end_point="])
    # opts = dict(opts)
    # if opts.get("-o"):
    #     origin_ = str(opts.get("-o"))
    # elif opts.get("--origin"):
    #     origin_ = str(opts.get("--origin"))
    # if opts.get("-e"):
    #     end_point_ = str(opts.get("-e"))
    # elif opts.get("--end_point"):
    #     end_point_ = str(opts.get("--end_point"))
    #
    # consume = Consume()
    # consume.start(origin_, end_point_)
