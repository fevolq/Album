#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/22 15:01
# FileName: 上传图片并获取图集路径

import logging
from typing import List, Union

from telegraph import Telegraph

from module.bean.fetch import Fetch
from utils import pools, util, rate_limit
from utils.async_queue import AsyncQueue


class UploadAlbum:
    """
    上传发布图集
    """

    ShortName = 'Album'
    Host = 'https://telegra.ph'
    AuthorUrl = None

    MaxUploadRate = 10  # 图片上传的最大频率（/分）
    MaxMiss = 3  # 允许的最大图片丢失数量

    def __init__(self, title: str, images: List[str], **kwargs):
        """

        :param title:
        :param images:  [图片链接 或 本地路径]
        :param kwargs: {auth: 作者, ..., from_local: 本地, extra: {爬虫实例透传的数据，如: header}}
        """
        assert title and images, '缺少参数'
        self.title = title
        self.images = images
        self.kwargs = kwargs
        self.auth: str = kwargs['auth']

        self.telegraph = Telegraph()
        self.telegraph.create_account(short_name=UploadAlbum.ShortName, author_name=f'{self.auth}')
        self.upload_limiter = rate_limit.RateLimiter(UploadAlbum.MaxUploadRate, 60, name='upload')

        self.end_point = ''

    @util.catch_error(raise_error=False)
    def _load_image(self, image) -> Union[dict, None]:
        """
        读取图片二进制
        :param image: 图片链接，或本地路径
        :return: [{image: 原链接, content: 图片二进制内容}]
        """
        from_local = self.kwargs.get('from_local', False)  # 本地文件

        logging.info(f'Start load: {image}')
        content = None
        if from_local:
            with open(image, 'rb') as f:
                content = f.read()
        else:
            # resp = requests.get(image, headers=self.kwargs.get('headers', None))
            result = Fetch.request(image, headers=self.kwargs.get('extra', {}).get('headers', None), again=3)
            resp = result['res']
            if resp.status_code == 200:
                content = resp.content
            else:
                logging.error(f'Failure load：{image} , Status_code: {resp.status_code}')
        logging.info(f'End load: {image}')
        return {
            'url': image,
            'content': content,
        }

    def _load_images(self) -> List[Union[dict, None]]:
        """
        读取图片二进制
        :return: [{image: 原链接, content: 图片二进制内容}]
        """

        # result = []
        # for image_ in self.images:
        #     content = self._load(image_)
        #     result.append(content)

        result = pools.execute_event(self._load_image, [[(image_,)] for image_ in self.images])

        return result

    @util.catch_error(raise_error=False)
    def _upload_image(self, image: dict) -> str:
        """
        上传单张图片
        :return:
        """
        logging.info(f'Start upload: {image["url"]}')
        if not image or not image['content']:
            if image:
                logging.warning(f'图片：{image["url"]} 内容为空')
            return ''

        with self.upload_limiter:
            url = f'{UploadAlbum.Host}/upload'
            result = Fetch.request(url, method='POST', again=3, files={'file': ('file', image['content'], 'image/jpg')})
        resp = result['res']
        data = resp.json()[0]
        if 'error' in data:
            logging.warning(f'Error upload: {data["error"]}')
            return ''
        src = resp.json()[0]['src']
        logging.info(f'End upload: {image["url"]}')
        return src

    def _upload_images(self, images: List[dict]) -> List[str]:
        """
        上传多张图片
        :param images:
        :return:
        """
        # result = []
        # for img_content in images_content:
        #     img_url = self._upload_image(img_content)
        #     result.append(img_url)

        result = pools.execute_event(self._upload_image, [[(image,)] for image in images if image],
                                     maxsize=8, force_pool=True)

        return result

    def _new_upload(self) -> List[str]:
        task = AsyncQueue(name=self.title)
        task.add_producer_with_pool(self._load_image, [[(image,)] for image in self.images], times=4)
        task.add_consumer(self._upload_image)
        task.run()

        return task.get_result()

    def _publish(self, images: List[str]):
        """
        发布图集
        :param images: 图片链接
        :return:
        """
        logging.info(f'Publish: {self.title}')
        htmls = [f'<img src="{image}">' for image in images if image]
        if len(self.images) - len(htmls) >= UploadAlbum.MaxMiss:
            logging.error(f'title：{self.title}，{len(self.images)}张图片丢失数量：{len(self.images) - len(htmls)}，超出阈值{UploadAlbum.MaxMiss}')
            return

        html = ''.join(htmls)
        resp = self.telegraph.create_page(f'[{UploadAlbum.ShortName}] {self.title}', html_content=html,
                                          author_name=self.auth, author_url=UploadAlbum.AuthorUrl)
        if resp:
            self.end_point = resp['path']
            logging.info(f'图集 {self.title} 发布成功。{UploadAlbum.Host}/{self.end_point}')

    def run(self):
        # images = self._load_images()
        # images_url = self._upload_images(images)
        images_url = self._new_upload()

        self._publish(images_url)


def run(*args, **kwargs):
    album = UploadAlbum(*args, **kwargs)
    album.run()
    return album.end_point
