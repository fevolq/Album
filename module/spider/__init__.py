#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/9/29 22:28
# FileName: 爬虫模块

"""
注：外部必须以绝对路径导入 from module import spider
"""

import os
import inspect
import importlib

from module.spider.origin import Origin

current_dir = os.path.dirname(os.path.abspath(__file__))


# 查找子类
def get_subclasses(module_path, base_class):
    module_name = os.path.basename(module_path)
    subclasses = []
    for filename in os.listdir(module_path):
        if not filename.endswith('.py') or filename == '__init__.py':
            continue

        sub_name = f'module.{module_name}.{filename[:-3]}'  # 此处使用的是绝对导入
        module = importlib.import_module(sub_name)

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if inspect.isclass(obj) and issubclass(obj, base_class) and obj != base_class:
                subclasses.append(obj)
    return subclasses


adapter = {
    cls.Name: cls
    for cls in get_subclasses(current_dir, Origin)
    if cls.Name
}

if __name__ == '__main__':
    print(adapter)
