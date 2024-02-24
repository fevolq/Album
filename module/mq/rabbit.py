#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/3/27 16:11
# FileName: rabbitmq

import json
import logging

import pika

import config
import constant
from module.bean import bean


class Param:
    """
    参数模式
    """
    default_conf = {
        'host': config.RABBIT_HOST,
        'port': config.RABBIT_PORT,
        'username': config.RABBIT_USER,
        'password': config.RABBIT_PWD,
    }

    def __init__(self, mq_conf: dict = None, with_dead_exchange=True, queue=None):
        self.coon = None
        self.channel = None
        self._link(mq_conf)

        self.queue = None
        self._prepare(with_dead_exchange, queue)

    def _link(self, mq_conf):
        """
        连接
        :param mq_conf:
        :return:
        """
        conf = self.default_conf  # 通过实例改动类属性，只会影响当前实例，不会影响其他
        if mq_conf:
            conf.update(mq_conf)
        host = conf['host']
        port = conf['port']
        username = conf['username']
        password = conf['password']

        credentials = pika.PlainCredentials(username, password)
        options = {
            'host': host,
            'port': port,
            'virtual_host': '/',
            'heartbeat': 600,  # 心跳
        }
        if username:
            options.update({'credentials': credentials})
        self.conn = pika.BlockingConnection(pika.ConnectionParameters(**options))
        self.channel = self.conn.channel()

    def _prepare(self, with_dead_exchange, queue=None):
        """
        准备队列
        :param with_dead_exchange: 基于死信队列
        :param queue: 队列名称
        :return:
        """
        if with_dead_exchange:
            # 死信队列的交换机与队列名，使用常量
            self.queue = constant.MqQueue
            routing_key = ''
            self.declare_queue(constant.MqDeadQueue, routing_key=routing_key)  # 声明普通队列（死信交换机 >>）
            self.declare_exchange(constant.MqDeadExchange)  # 声明死信交换机
            self.channel.queue_bind(queue=constant.MqDeadQueue, exchange=constant.MqDeadExchange,
                                    routing_key=routing_key)
            self.declare_queue(self.queue, to_dead_exchange=True)  # 声明死信队列（>> 死信交换机）
        else:
            # 普通队列。一般在获取死信消息时使用，queue = constant.MqDeadQueue
            assert queue, '缺少 queue'
            self.queue = queue
            self.declare_queue(queue)

    def declare_queue(self, queue, to_dead_exchange=False, **options):
        """
        声明队列（普通队列、死信队列）
        :param queue:
        :param to_dead_exchange: 绑定死信交换机
        :param options:
        :return:
        """
        args = {}
        if to_dead_exchange:
            args = {
                'x-dead-letter-exchange': options.get('exchange', constant.MqDeadExchange),
                'x-dead-letter-routing-key': options.get('routing-key', ''),
            }
        self.channel.queue_declare(queue=queue, durable=True, arguments=args)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.confirm_delivery()  # 确认消息已发送，避免一些消息未发送到队列，主程序便已结束

    def declare_exchange(self, exchange):
        """
        声明交换机
        :param exchange:
        :return:
        """
        self.channel.exchange_declare(exchange=exchange, exchange_type='direct', durable=True)

    def start_consuming(self, func, headers: bean.Header = None):
        """
        消费者开始监听
        :param func:
        :param headers: 消息头。
        :return:
        """

        def callback(ch, method, properties, body):
            logging.info(f'{self.queue} received message')
            msg_headers = bean.Header(**properties.headers)
            if headers is not None and msg_headers != headers:  # 不是指定类型的消息时，放回队列
                # TODO：会持续循环
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                ...
            else:
                data = json.loads(body.decode())
                res = func(**data, msg_headers=msg_headers)
                try:
                    if res:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                        logging.warning(f'消费者处理失败，进入死信队列')
                # except pika.exceptions.ChannelClosedByBroker:
                #     self.channel.start_consuming()
                except Exception as e:
                    logging.warning(type(e), str(e))

        logging.info(f'{self.queue} 开始监听...')
        self.channel.basic_consume(
            queue=self.queue,
            auto_ack=False,  # 手动应答
            on_message_callback=callback,
        )
        self.channel.start_consuming()

    def stop_consuming(self):
        self.channel.stop_consuming()

    def producer(self, data: dict, headers: dict):
        """
        生产者
        :param data: 必须为键值对
        :param headers: 消息头
        :return:
        """
        assert isinstance(data, dict)
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # 持久化
                content_type='application/json',
                headers=headers,
            )
        )
        # return self.channel.wait_for_confirms()      # 可等待确认消息

    def is_closed(self):
        return self.channel.is_closed()
