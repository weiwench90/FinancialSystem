#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import datetime
import json
import time
from utils.str_utils import str2datetime
from typing import List, Dict
import os

headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        )
}
def symbol2code(symbol):
    ts = int(datetime.datetime.now().timestamp() * 1000)
    url = f"https://www1.hkexnews.hk/search/prefix.do"
    payload = {
        "callback": "callback",
        "lang": "ZH",
        "type": "A",
        "name": f"{symbol:05d}" if isinstance(symbol, int) else symbol,
        "market": "SEHK",
        "_": ts
    }
    
    response = requests.get(url, params=payload, headers=headers)
    ret = response.text.strip()
    if ret.startswith("callback(") and ret.endswith(");"):
        ret = ret[len("callback("):-2]
        
    return json.loads(ret).get("stockInfo", [])

def symbol2code_delisted(symbol):
    ts = int(datetime.datetime.now().timestamp() * 1000)
    url = "https://www1.hkexnews.hk/search/prefix.do"
    payload = {
        "callback": "callback",
        "lang": "ZH",
        "type": "I",
        "name": f"{symbol:05d}" if isinstance(symbol, int) else symbol,
        "market": "SEHK",
        "_": ts
    }
    response = requests.get(url, params=payload, headers=headers)
    ret = response.text.strip()
    if ret.startswith("callback(") and ret.endswith(");"):
        ret = ret[len("callback("):-2]
        
    return json.loads(ret).get("stockInfo", [])


def get_stock_announcements_html(symbol:str|int=None, stockId:str|int=None):
    if symbol is None and stockId is None:
        return []
    if not stockId:
        # 获取stockId
        stock_info = symbol2code(symbol)
        time.sleep(1)  # 避免请求过快
        if stock_info:
            stockId = stock_info[0]["stockId"]
        else:
            return []
    url = f"https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=zh"
    payload = {
        "lang": "zh",
        "category": 0,
        "market": "SEHK",
        "searchType": 1,
        "documentType": -1,
        "t1code": -2,
        "t2Gcode": -2,
        "t2code": -2,
        "stockId": stockId,
        "from": "20070625",
        "to": datetime.datetime.now().strftime("%Y%m%d"),
        "MB-Daterange": 0,
        "title": "",
    }
    response = requests.post(url, data=payload, headers=headers)
    return response.text


from bs4 import BeautifulSoup

def parse_announcements(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 找到公告表格
    table = soup.find('table', class_='table sticky-header-table table-scroll table-mobile-list')
    
    announcements = []
    
    # 遍历表格行（跳过表头）
    rows = table.find('tbody').find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        
        if len(cells) >= 4:
            # 解析发放时间
            release_time = cells[0].get_text(strip=True)
            release_time = release_time.replace('發放時間: ', '')
            
            # 解析股份代号
            stock_code = cells[1].get_text(strip=True)
            stock_code = stock_code.replace('股份代號: ', '')
            
            # 解析股份简称
            stock_name = cells[2].get_text(strip=True)
            stock_name = stock_name.replace('股份簡稱: ', '')
            
            # 解析文件信息
            doc_cell = cells[3]
            
            # 获取公告类型
            headline_div = doc_cell.find('div', class_='headline')
            doc_type = headline_div.get_text(strip=True) if headline_div else ''
            
            # 获取文件链接和标题
            doc_link_div = doc_cell.find('div', class_='doc-link')
            if doc_link_div:
                link_element = doc_link_div.find('a')
                if link_element:
                    doc_title = link_element.get_text(strip=True)
                    doc_url = link_element.get('href', '')
                    
                    # 获取文件大小
                    size_span = doc_link_div.find('span', class_='attachment_filesize')
                    file_size = size_span.get_text(strip=True) if size_span else ''
                    
                    announcement = {
                        'DATE_TIME': release_time,
                        'STOCK_CODE': stock_code,
                        'STOCK_NAME': stock_name,
                        'FILE_TYPE': doc_type,
                        'TITLE': doc_title,
                        'FILE_LINK': doc_url, # https://www1.hkexnews.hk/+doc_url
                        'FILE_INFO': file_size
                    }
                    
                    announcements.append(announcement)
    
    return announcements

def get_stock_announcements_direct(symbol:str|int=None, 
                                   stockId:str|int=None,
                                   tier1:int=-2,
                                   tier2:int=-2,
                                   tier2G:int=-2,
                                   until:datetime.datetime=None):
    if symbol is None and stockId is None:
        return []
    if not stockId:
        # 获取stockId
        stock_info = symbol2code(symbol)
        time.sleep(1)  # 避免请求过快
        if stock_info:
            stockId = stock_info[0]["stockId"]
        else:
            return []
    
    url = "https://www1.hkexnews.hk/search/titleSearchServlet.do?"
    payload = {
        "sortDir": 0,
        "sortByOptions": "DateTime",
        "category": 0,
        "market": "SEHK",
        "stockId": stockId,
        "documentType": -1,
        "fromDate": "20070625",
        "toDate": datetime.datetime.now().strftime("%Y%m%d"),
        "title": "",
        "searchType": 1,
        "t1code": tier1,
        "t2Gcode": tier2G,
        "t2code": tier2,
        "rowRange": 100,
        "lang": "zh"
    }
    response = requests.get(url, params=payload, headers=headers)
    ret: Dict = response.json()
    announcements: List = json.loads(ret.get("result", "[]"))
    # 转换其中的DATE_TIME的格式
    for ann in announcements:
        ann["DATE_TIME"] = str2datetime(ann["DATE_TIME"], dayfirst=True)
    announcements.sort(key=lambda x: x["DATE_TIME"])
    if until:
        if announcements[0]["DATE_TIME"] < until:
            return [ann for ann in announcements if ann["DATE_TIME"] > until]
    
    total_cnt = ret.get("recordCnt", 100)
    time.sleep(1)  # 避免请求过快
    if total_cnt > 100:
        payload["rowRange"] = (total_cnt//100 + 1) * 100
        response = requests.get(url, params=payload, headers=headers)
        ret: Dict = response.json()
    announcements: List = json.loads(ret.get("result", "[]"))
    # {'FILE_INFO': '235KB', 
    # 'NEWS_ID': '11798686', 
    # 'SHORT_TEXT': '公告及通告 - [董事會召開日期]<br/>', 
    # 'TOTAL_COUNT': '577', 
    # 'DOD_WEB_PATH': '', 
    # 'STOCK_NAME': '新濠國際發展', 
    # 'TITLE': '董事會會議召開日期', 
    # 'FILE_TYPE': 'PDF', 
    # 'DATE_TIME': '18/08/2025 16:31', 
    # 'LONG_TEXT': '公告及通告 - [董事會召開日期]', 
    # 'STOCK_CODE': '00200', 
    # 'FILE_LINK': '/listedco/listconews/sehk/2025/0818/2025081800287_c.pdf'}
    for ann in announcements:
        ann["DATE_TIME"] = str2datetime(ann["DATE_TIME"], dayfirst=True)
    return announcements



if __name__ == "__main__":
    # html_content = get_stock_announcements_html(200)
    # announcements = parse_announcements(html_content)
    
    announcements = get_stock_announcements_direct(symbol=9992, tier1=40000)
    print(announcements)
    # for ann in announcements:
    #     title = ann['TITLE']
    #     file_type = ann['FILE_TYPE'].lower()
    #     url = "https://www1.hkexnews.hk/" + ann['FILE_LINK'].lstrip("/")
    #     break
    
    