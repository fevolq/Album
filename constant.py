#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/22 17:26
# FileName:

AuthTable = 'auth'  # 图集作者
AuthAlbumTable = 'auth_album'  # 作者的图集
AlbumTable = 'album'  # 图集
OriginAuthAlbumTable = 'origin_auth_album'  # 各来源的作者图集
OriginAlbumTable = 'origin_album'  # 各来源图集
OriginImageTable = 'origin_image'  # 各来源图集的图片链接

MQ_QUEUE = 'album'  # rabbit队列名称
MQ_DEAD_EXCHANGE = f'dead_{MQ_QUEUE}_exchange'  # rabbit死信交换机
MQ_DEAD_QUEUE = f'dead_{MQ_QUEUE}'  # rabbit死信队列
