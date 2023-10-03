#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/22 15:08
# FileName: 根据图集任务，制作图集，并记录及更新

import asyncio
import logging
from typing import List

from dao import sql_builder, mysqlDB
from module.bean import bean
from module.telegra import upload
from utils import util
import constant


class Album:
    """
    下发图集任务，并记录数据库
    """

    def __init__(self, origin: str, end_point: str, **kwargs):
        # 任务数据（根据任务，来进行下发图集任务）
        self.origin = origin.lower()
        self.end_point = end_point
        self.hash_str = bean.gen_unique_origin_album(self.origin, end_point)
        self.kwargs = kwargs

        # 元数据（各来源的数据）
        self.title: str = ''
        self.auths: List[dict] = []  # [{name: ..., uid: ...}, ...]
        self.images: List = []

        self.uri = None  # 制作的图集资源
        self.__hit = True  # 是否找到元数据
        self.has_record = self.get_record()
        self._load_metadata()

    def get_record(self) -> bool:
        """
        是否已有图集的制作记录
        :return:
        """
        sql, args = sql_builder.gen_select_sql(constant.AlbumTable, ['end_point'],
                                               condition={'hash': {'=': self.hash_str}})
        res = mysqlDB.execute(sql, args)['result']
        if res:
            self.uri = res[0]['end_point']
            return True
        return False

    def _load_metadata(self):
        """
        根据队列消息，从指定表中获取元数据
        :return:
        """
        if self.has_record:
            return

        title_sql, title_args = sql_builder.gen_select_sql(constant.OriginAlbumTable, ['title'],
                                                           condition={'hash': {'=': self.hash_str}})
        title_res = mysqlDB.execute(title_sql, title_args)['result']
        if not title_res:
            logging.warning(f'来源：{self.origin}，end_point：{self.end_point}，hash：{self.hash_str} 未找到图集')
            self.__hit = False
            return
        self.title = title_res[0]['title']

        auth_sql = f'SELECT {constant.AuthTable}.uid AS uid, {constant.AuthTable}.name AS name' \
                   f' FROM {constant.AuthTable}' \
                   f' LEFT JOIN {constant.OriginAuthAlbumTable}' \
                   f' ON {constant.AuthTable}.uid = {constant.OriginAuthAlbumTable}.uid' \
                   f' WHERE {constant.OriginAuthAlbumTable}.hash = %s'
        auth_res = mysqlDB.execute(auth_sql, [self.hash_str])['result']
        self.auths = auth_res

        image_sql, image_args = sql_builder.gen_select_sql(constant.OriginImageTable, ['url'],
                                                           condition={'hash': {'=': self.hash_str}})
        image_res = mysqlDB.execute(image_sql, image_args)['result']
        self.images = [item['url'] for item in image_res]

    def _add_album(self):
        """
        记录图集
        :return:
        """
        if not self.uri:
            return

        sql_with_args_list = []
        # 作者图集
        auth_album_sql, auth_album_args = sql_builder.gen_insert_sqls(constant.AuthAlbumTable,
                                                                      [{
                                                                          'uid': auth['uid'],
                                                                          'end_point': self.uri,
                                                                          'origin': self.origin,
                                                                      } for auth in self.auths])
        sql_with_args_list.append({'sql': auth_album_sql, 'args': auth_album_args})

        # 图集
        album_sql, album_args = sql_builder.gen_insert_sql(constant.AlbumTable,
                                                           {'title': self.title, 'end_point': self.uri,
                                                            'hash': self.hash_str, 'update_at': util.now_time()})
        sql_with_args_list.append({'sql': album_sql, 'args': album_args})

        res = mysqlDB.execute_many(sql_with_args_list)
        if res['success']:
            logging.info(f'图集录入成功，origin：{self.origin}，title：{self.title}，end_point：{self.uri}')
        else:
            logging.error(f'图集录入失败，origin：{self.origin}，title：{self.title}，end_point：{self.uri}')

    async def _update_origin(self):
        """
        更新来源表
        :return:
        """
        if not self.uri:
            return

        sql, args = sql_builder.gen_update_sql(constant.OriginAlbumTable,
                                               {'album': self.uri, 'update_at': util.now_time()},
                                               conditions={'hash': {'=': self.hash_str}})
        res = mysqlDB.execute(sql, args, raise_error=False)
        if res['success']:
            logging.info(f'来源：{self.origin}，title：{self.title} 更新成功。')
        else:
            logging.info(f'来源：{self.origin}，title：{self.title} 更新失败。album： {self.uri}')

    def run(self):
        if not self.has_record:
            logging.info(f'Start make album：{self.origin} - {self.title}')
            self.uri = upload.run(self.title, self.images,
                                  auth='，'.join([auth['name'] for auth in self.auths]), origin=self.origin,
                                  **self.kwargs)
            if not self.uri:
                logging.error(f'origin：{self.origin}，title：{self.title}，hash：{self.hash_str} 上传图集失败。')
                return False

            self._add_album()
        asyncio.run(self._update_origin())
        return True


def run(*args, **kwargs):
    """
    参数来源于消息队列
    :param args:
    :param kwargs:
    :return:
    """
    return Album(*args, **kwargs).run()


if __name__ == '__main__':
    import getopt
    import sys

    from utils import log_util

    log_util.init_logging(stream_level='INFO')

    origin_ = None
    end_point_ = None

    opts, _ = getopt.getopt(sys.argv[1:], "o:e:", ["origin=", "end_point="])
    opts = dict(opts)
    if opts.get("-o"):
        origin_ = str(opts.get("-o"))
    elif opts.get("--origin"):
        origin_ = str(opts.get("--origin"))
    if opts.get("-e"):
        end_point_ = str(opts.get("-e"))
    elif opts.get("--end_point"):
        end_point_ = str(opts.get("--end_point"))

    assert all([origin_, end_point_]), '缺少参数'

    run(origin_, end_point_)
