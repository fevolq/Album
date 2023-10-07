#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2022/11/4 18:15
# FileName:

import concurrent.futures
import multiprocessing
from typing import List

import gevent
from gevent.pool import Pool
from gevent import monkey

PROCESS_POOL_SIZE = 4
THREAD_POOL_SIZE = 4
GEVENT_POOL_SIZE = 4


def execute_process(callback, args_list: List = None, *, times: int = 0, maxsize=4):
    """
    多进程
    :param callback: 单进程的执行方法
    :param args_list: 单进程的参数组成的数组。[[(args1, args2,), {'key1': value1, 'key2': value2}], ]
    :param times: 执行的次数。当args_list为空时，生效，否则使用args_list的数量来判断
    :param maxsize: 进程池数量
    :return:
    """
    maxsize = max(maxsize, PROCESS_POOL_SIZE)

    # 获取执行次数
    args_length = len(args_list) if args_list else 0
    times = args_length or times
    assert times > 0, '参数异常，导致执行次数为0'
    pools = min(times, maxsize)

    # 解析参数
    def get_params(params):
        args = params[0] if isinstance(params[0], (tuple, list)) else []
        kwargs = params[-1] if isinstance(params[-1], dict) else {}
        return args, kwargs

    with multiprocessing.Pool(processes=pools) as executor:
        futures = []
        for i in range(times):
            if args_list:
                item_args, item_kwargs = get_params(args_list[i])
                future = executor.apply_async(callback, args=item_args, kwds=item_kwargs)
            else:
                future = executor.apply_async(callback)
            futures.append(future)

        # 获取任务的结果
        result = [future.get() for future in futures]

    return result


def execute_thread(callback, args_list: List = None, *, times: int = 0, maxsize: int = 4):
    """
    多线程
    :param callback: 单线程的执行方法
    :param args_list: 单线程的参数组成的数组。[[(args1, args2,), {'key1': value1, 'key2': value2}], ]
    :param times: 执行的次数。当args_list为空时，生效，否则使用args_list的数量来判断
    :param maxsize: 线程池数量
    :return:
    """
    maxsize = max(maxsize, THREAD_POOL_SIZE)

    # 获取执行次数
    args_length = len(args_list) if args_list else 0
    times = args_length or times
    assert times > 0, '参数异常，导致执行次数为0'
    maxsize = min(times, maxsize)

    # 解析参数
    def get_params(params):
        args = params[0] if isinstance(params[0], (tuple, list)) else []
        kwargs = params[-1] if isinstance(params[-1], dict) else {}
        return args, kwargs

    with concurrent.futures.ThreadPoolExecutor(max_workers=maxsize) as executor:
        futures = []
        for i in range(times):
            if args_list:
                item_args, item_kwargs = get_params(args_list[i])
                future = executor.submit(callback, *item_args, **item_kwargs)
            else:
                future = executor.submit(callback)
            futures.append(future)

        # 获取任务的结果
        result = [future.result() for future in futures]
    return result


def execute_event(callback, args_list: List = None, *, times: int = 0, maxsize=4):
    """
    多协程
    :param callback: 单协程的执行方法
    :param args_list: 单协程的参数组成的数组。[[(args1, args2,), {'key1': value1, 'key2': value2}], ]
    :param times: 执行的次数。当args_list为空时，生效，否则使用args_list的数量来判断
    :param maxsize: 协程池数量
    :return:
    """
    monkey.patch_socket()  # 识别IO阻塞

    maxsize = max(maxsize, GEVENT_POOL_SIZE)

    # 获取执行次数
    args_length = len(args_list) if args_list else 0
    times = args_length or times
    assert times > 0, '参数异常，导致执行次数为0'
    pools = min(times, maxsize)

    # 解析参数
    def get_params(params):
        args = params[0] if isinstance(params[0], (tuple, list)) else []
        kwargs = params[-1] if isinstance(params[-1], dict) else {}
        return args, kwargs

    def func(index):
        if args_list:
            args, kwargs = get_params(args_list[index])
            return callback(*args, **kwargs)
        else:
            return callback()

    gevent_pool = gevent.pool.Pool(pools)
    task_list = [gevent_pool.spawn(func, i) for i in range(times)]
    gevent.joinall(task_list)

    result = [task.value for task in task_list]
    return result
