#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/22 15:48
# FileName: 根据 spider 任务，下发 spider，并记录

import logging
from typing import List, Union

import constant
from dao import sql_builder, mysqlDB
from utils import util
from module import spider
from module.bean import bean


class Image:
    """
    下发爬取任务，记录数据库
    """

    def __init__(self, origin, end_point, *, auths: Union[List, str] = None, **kwargs):
        """

        :param origin:
        :param end_point:
        :param auths: 图集的作者，对于可以获取作者的来源，adapter会将自己的auths改写，故存储时以adapter.auths为准
        :param kwargs:
        """
        self.origin = origin.lower()
        assert self.origin in spider.adapter, f'error origin: {self.origin}'
        self.end_point = spider.adapter[self.origin].resolve_end_point(end_point)

        auths = auths or ['其他']
        auths = auths.split(',') if isinstance(auths, str) else auths
        self.__auths = [auth.strip() for auth in auths if auth.strip()]
        self.kwargs = kwargs

        self.hash_str = bean.gen_unique_origin_album(self.origin, self.end_point)

        self.adapter = spider.adapter[self.origin](self.end_point, auths=self.__auths, **kwargs)
        self.has_record = self.get_record()

    def __repr__(self):
        return f'{self.origin}: {self.end_point}'

    def get_record(self) -> bool:
        sql, args = sql_builder.gen_select_sql(constant.OriginAlbumTable, ['title'],
                                               condition={'hash': {'=': self.hash_str}}, limit=1)
        res = mysqlDB.execute(sql, args)['result']
        if res:
            title = res[0]['title']
            logging.info(f'origin：{self.origin}，end_point：{self.end_point} 已存在记录：{title}')
            return True
        return False

    def _add_origin_album(self):
        """
        添加记录
        :return:
        """
        # 作者
        auth_ids = []
        for auth in self.adapter.auths:
            auth_sql, auth_args = sql_builder.gen_select_sql(constant.AuthTable, ['uid'],
                                                             condition={'name': {'=': auth}}, limit=1)
            auth_res = mysqlDB.execute(auth_sql, auth_args)['result']
            if len(auth_res) == 0:
                uid = bean.gen_uid(auth)
                auth_row = {'uid': uid, 'name': auth}
                auth_sql, auth_args = sql_builder.gen_insert_sql(constant.AuthTable, auth_row)
                logging.info(f'增加作者：{auth}，uid：{uid}')
                mysqlDB.execute(auth_sql, auth_args)
            else:
                uid = auth_res[0]['uid']
            auth_ids.append(uid)

        sql_with_args = []
        # 各来源图集
        album_sql, album_args = sql_builder.gen_insert_sql(constant.OriginAlbumTable,
                                                           {
                                                               'title': self.adapter.title,
                                                               'end_point': self.end_point,
                                                               'origin': self.origin,
                                                               'hash': self.hash_str,
                                                               'update_at': util.now_time()
                                                           }, update_cols=['update_at'])
        sql_with_args.append({'sql': album_sql, 'args': album_args})
        # 作者图集
        auth_album_rows = [{'uid': uid, 'hash': self.hash_str} for uid in auth_ids]
        auth_album_sql, auth_album_args = sql_builder.gen_insert_sqls(constant.OriginAuthAlbumTable, auth_album_rows,
                                                                      update_cols=['hash'])
        sql_with_args.append({'sql': auth_album_sql, 'args': auth_album_args})
        # 图集图片
        image_rows = [{'index': index, 'url': image, 'hash': self.hash_str}
                      for index, image in enumerate(self.adapter.images)]
        image_sql, image_args = sql_builder.gen_insert_sqls(constant.OriginImageTable, image_rows, update_cols=['hash'])
        sql_with_args.append({'sql': image_sql, 'args': image_args})
        res = mysqlDB.execute_many(sql_with_args)
        if not res['success']:
            logging.error(f'{res["result"]}')
        else:
            logging.info(f'origin：{self.origin}，end_point：{self.end_point}，'
                         f'auths：{",".join(self.adapter.auths)}，title：{self.adapter.title}'
                         f' 保存图片成功：{len(self.adapter.images)}张。')
        return res['success']

    def get_msg(self):
        data = {
            'origin': self.origin,
            'end_point': self.end_point,
            'extra': self.adapter.extra
        }
        headers = {
            'origin': self.origin,
            'end_point': self.end_point,
        }
        return {
            'data': data,
            'headers': headers
        }

    def main(self):
        if self.has_record:
            return True

        logging.info(f'Start spider album：{self.origin} - {self.end_point}')
        self.adapter.run()  # 启动爬虫
        logging.info(f'End spider album：{self.origin} - {self.end_point}')
        if not self.adapter.images:
            logging.error(f'origin：{self.origin}，end_point：{self.end_point} 爬取图片失败。')
            return False

        if not self._add_origin_album():
            logging.error(f'origin：{self.origin}，end_point：{self.end_point} 保存源数据失败。')
            return False

        return True


if __name__ == '__main__':
    import getopt
    import sys

    from utils import log_util

    log_util.init_logging(stream_level='INFO')

    origin_ = ''
    end_point_ = ''
    auths_ = ['']

    opts, _ = getopt.getopt(sys.argv[1:], "o:e:a:", ["origin=", "end_point=", "auths="])
    opts = dict(opts)
    if opts.get("-o"):
        origin_ = str(opts.get("-o"))
    elif opts.get("--origin"):
        origin_ = str(opts.get("--origin"))
    if opts.get("-e"):
        end_point_ = str(opts.get("-e"))
    elif opts.get("--end_point"):
        end_point_ = str(opts.get("--end_point"))
    if opts.get("-a"):
        auths_ = str(opts.get("-a"))
    elif opts.get("--auths"):
        auths_ = str(opts.get("--auths"))

    assert all([origin_, end_point_]), '缺少参数'

    Image(origin_, end_point_, auths=auths_).main()
