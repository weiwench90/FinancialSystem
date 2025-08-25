#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
from typing import Union, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def clean_ctrl(s: str) -> str:
    # 把除了 \n \r \t 的其他控制字符转成 \uXXXX
    s = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', lambda m: '\\u%04x' % ord(m.group(0)), s)
    # 把裸 Tab 也转义（保险起见）
    s = s.replace('\t', '\\t')
    return s

def extract_json(text):
    start = text.find("```json")
    if start == -1:
        try:
            return json.loads(clean_ctrl(text.strip()))
        except json.JSONDecodeError:
            logger.error(f"JSON 解析失败1:{text[:100]}...")
            return text

    start += len("```json")
    while start < len(text) and text[start] in " \t\r\n":
        start += 1

    # 从后往前找最后一个```作为结束标记
    end = text.rfind("```")
    if end <= start:
        end = len(text)

    block = text[start:end].strip()

    try:
        return json.loads(clean_ctrl(block))
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {str(e)}")
        logger.error(f"问题块: {block}")
        return block
