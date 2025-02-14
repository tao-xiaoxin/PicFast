#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 日志文件路径
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 挂载静态目录
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# jinja2 模版文件路径
JINJA2_TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
