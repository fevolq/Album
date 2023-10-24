#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/5/5 13:58
# FileName:

import random
import threading

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


agent_list = [
   'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',
   'Mozilla/5.0 (Linux; Android 9; SM-N9500 Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/76.0.3809.89 Mobile Safari/537.36 T7/11.20 SP-engine/2.16.0 baiduboxapp/11.20.0.14 (Baidu; P1 9)',
   'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50',
   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
   'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
]


def get_user_agent():
    return random.choice(agent_list)


class Fetch:

    def __init__(self, headless=True):
        self.browser = Browser(headless)

    @classmethod
    def request(cls, url, method='GET', headers=None, again=1, **kwargs):
        """
        requests请求
        :param url:
        :param method:
        :param headers:
        :param again: 异常重复次数
        :param kwargs:
        :return: {res: 请求的返回, times: 请求的次数}
        """
        result = {'res': None, 'times': 0}

        def do():
            result['times'] += 1
            _headers = {
                'user-agent': get_user_agent(),
            }
            headers_ = {} if headers is None else headers
            _headers.update(headers_)

            return requests.request(method, url, headers=_headers, **kwargs)

        num = 0
        while num <= again - 1:
            try:
                result['res'] = do()
                break
            except:
                num += 1

        return result

    def fetch_response_with_selenium(self, url, *args, **kwargs):
        """
        selenium模拟浏览器请求
        :param url:
        :return:
        """
        return self.browser.fetch_response(url, *args, **kwargs)


class Browser:

    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        # 构造单例
        if hasattr(cls, 'instance'):
            return cls.instance

        # 线程锁
        with cls._lock:
            if not hasattr(cls, 'instance'):
                cls.instance = super(Browser, cls).__new__(cls)
            return cls.instance

    def __init__(self, headless=True):
        """

        :param headless: selenium——无界面模式
        """
        self.headless = headless
        self._driver = None

    def __load_driver(self):
        if self._driver is None:
            chrome_options = Options()
            # linux环境所需
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('start-maximized')
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument('--disable-browser-side-navigation')
            chrome_options.add_argument('enable-automation')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('enable-features=NetworkServiceInProcess')
            if self.headless:
                # 无界面模式
                chrome_options.add_argument('--headless')

            # if config.WebDriverPath:
            #     self._driver = webdriver.Chrome(executable_path=config.WebDriverPath, options=chrome_options)
            # else:
            self._driver = webdriver.Chrome(options=chrome_options)

    def get_driver(self):
        if self._driver is None:
            self.__load_driver()
        return self._driver

    def fetch_response(self, url, until=None, until_not=None):
        driver = self.get_driver()
        driver.get(url)

        until_not_conf, until_conf = [], []
        until = until if until else {}
        until_not = until_not if until_not else {}
        if until.get('class_tag'):
            until_conf.append((By.CLASS_NAME, until['class_tag']))
        if until.get('id_tag'):
            until_conf.append((By.ID, until['id_tag']))
        if until_not.get('class_tag'):
            until_not_conf.append((By.CLASS_NAME, until_not['class_tag']))
        if until_not.get('id_tag'):
            until_not_conf.append((By.ID, until_not['id_tag']))
        if not until_conf:
            WebDriverWait(driver, 10)
        else:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(*until_conf)
            )
        if until_not_conf:
            WebDriverWait(driver, 10).until_not(
                EC.presence_of_element_located(*until_not_conf)
            )
        return driver.page_source

    def __del__(self):
        if self._driver:
            self._driver.quit()
