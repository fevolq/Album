import constant
from module.mq import rabbit


class ReloadDead:
    """
    重新加载死信消息，将死信消息放回原始队列
    """

    def __init__(self, start_queue, end_queue):
        """
        消息从 end_queue >> start_queue
        :param start_queue: 消息的初始队列（死信队列）
        :param end_queue: 死信消息的存放队列（死信交换机路由的目标）
        """
        self.start_mq = rabbit.Param(with_dead_exchange=True, queue=start_queue)
        self.end_mq = rabbit.Param(with_dead_exchange=False, queue=end_queue)

    # 读取死信消息
    def load_dead_msg(self, **data):
        msg_headers = data.pop('msg_headers')
        self.re_producer(data, headers=msg_headers.get_value())
        return True

    # 重新投递消息
    def re_producer(self, data, headers):
        self.start_mq.producer(data, headers=headers)

    # 读取死信消息
    def run(self):
        self.end_mq.start_consuming(self.load_dead_msg)


if __name__ == '__main__':
    from utils import log_util

    log_util.init_logging(stream_level='INFO')

    ReloadDead(constant.MQ_QUEUE, constant.MQ_DEAD_QUEUE).run()

    # # 中转。注意更改对应的with_dead_exchange
    # ReloadDead('demo', constant.MQ_QUEUE).run()
    # ReloadDead(constant.MQ_QUEUE, 'demo').run()
