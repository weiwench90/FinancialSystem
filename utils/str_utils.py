#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata
import datetime
from zoneinfo import ZoneInfo
from dateutil import parser, tz

BJ_TZ = ZoneInfo("Asia/Shanghai")


def convert_chinese_date_units(s: str) -> str:
    # 首先做一次全角到半角的归一化
    s = unicodedata.normalize('NFKC', s)
    # 再把年/月/日换成 '-' 或空串
    s = s.replace('年', '-').replace('月', '-').replace('日', '')
    return s

def str2datetime(date_str, dayfirst=False) -> datetime.datetime:
    # 既支持 datetime 也支持字符串
    if isinstance(date_str, datetime.datetime):
        dt = date_str
    else:
        s = convert_chinese_date_units(str(date_str))
        dt = parser.parse(s, dayfirst=dayfirst)  # 有时区会解析成 aware，无时区是 naive

    # 如果没有时区，默认当作北京时间
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BJ_TZ)  # 解释为“北京时间的这刻”
    return dt

from opencc import OpenCC

def convert_traditional_to_simplified(text: str) -> str:
    # t2s: 繁体到简体
    cc = OpenCC('t2s')
    return cc.convert(text)

def convert_simplified_to_traditional(text: str) -> str:
    # s2t: 简体到繁体
    cc = OpenCC('s2t')
    return cc.convert(text)