#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os

def download_file(url, filename=None, save_path="."):
    """
    下载PDF文件
    """
    try:
        # 发送GET请求
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # 检查请求是否成功
        
        # 如果没有指定文件名，从URL中提取
        if filename is None:
            filename = url.split('/')[-1]
        
        # 保存文件
        if save_path:
            filename = save_path.rstrip("/") + "/" + filename
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"文件已成功下载：{filename}")
        print(f"文件大小：{len(response.content)} 字节")
        
    except requests.exceptions.RequestException as e:
        print(f"下载失败：{e}")
    except Exception as e:
        print(f"保存文件时出错：{e}")
