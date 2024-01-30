#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/22 17:26
# FileName:

# Upload
AlbumShortName = 'Album'  # telegraph个人账号的短名称
AlbumAuthorUrl = None  # telegraph图集中作者的引导链接
UploadMaxRate = 20  # 图片上传的最大频率（/分）
UploadMaxMiss = 3   # 允许的最大图片丢失数量

# TABLE
AuthTable = 'auth'  # 图集作者
AuthAlbumTable = 'auth_album'  # 作者的图集
AlbumTable = 'album'  # 图集
OriginAuthAlbumTable = 'origin_auth_album'  # 各来源的作者图集
OriginAlbumTable = 'origin_album'  # 各来源图集
OriginImageTable = 'origin_image'  # 各来源图集的图片链接

# RabbitMQ
MqQueue = 'album'  # rabbit队列名称
MqDeadExchange = f'dead_{MqQueue}_exchange'  # rabbit死信交换机
MqDeadQueue = f'dead_{MqQueue}'  # rabbit死信队列
