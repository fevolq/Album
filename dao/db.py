#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2022/10/26 17:13
# FileName: 单连接

import pymysql


class Db:

    def __init__(self, mode: str, db_name: str = None, db_conf=None):
        self._mode = mode
        self.__db_name = db_name
        self.__db_conf = db_conf

        self.__coon = None
        self.__client = None

    @property
    def coon(self):
        return self.__coon

    @property
    def client(self):
        return self.__client

    def __enter__(self):
        if self._mode.lower() == 'mysql':
            self.__client = self.__coon = mysql_conn(self.__db_name, self.__db_conf)
        return self.__coon

    def __exit__(self, exc_type, exc_val, exc_tb):
        close_db(self.__coon, self.__client)


def close_db(conn, client):
    try:
        conn.close()
    except:
        pass
    try:
        client.close()
    except:
        pass


def mysql_conn(db_name, db_conf):
    conn = pymysql.connect(
        host=db_conf['host'],
        port=db_conf['port'],
        user=db_conf['user'],
        password=db_conf['password'],
        db=db_name,
        connect_timeout=15,
        charset='utf8',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn
