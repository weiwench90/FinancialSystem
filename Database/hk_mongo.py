#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymongo
from typing import Dict, List
import datetime
from utils.str_utils import str2datetime
import pytz

class HkAnnouncementsDB:
    def __init__(self, db_name='SEHK'):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/", tz_aware=True, tzinfo=pytz.UTC)
        self.db = self.client[db_name]
        self.ann_col = self.db['announcements']
        self.report_ann_col = self.db['report_announcements']
        self.stock_info_col = self.db['stock_info']
        self.stock_info_zh_col = self.db['stock_info_zh']
        
    def stock_symbol_list(self):
        return self.stock_info_col.distinct('Stock Code', {'Category': 'Equity'})
    
    def update_stocks_info(self, stock_infos: List[Dict]):
        for stock_info in stock_infos:
            stock_code = stock_info.get('Stock Code', '')
            if not stock_code:
                continue
            stock_info['Stock Code'] = f"{stock_code:05d}"
            # 检查是否已存在该股票信息
            existing_info = self.stock_info_col.find_one({'Stock Code': stock_code})
            if existing_info:
                # 更新现有记录
                self.stock_info_col.update_one({'_id': existing_info['_id']}, {'$set': stock_info})
            else:
                # 插入新记录
                self.stock_info_col.insert_one(stock_info)
    
    def update_stocks_info_zh(self, stock_infos: List[Dict]):
        for stock_info in stock_infos:
            stock_code = stock_info.get('股份代號', '')
            if not stock_code:
                continue
            stock_info['Stock Code'] = f"{stock_code:05d}"
            # 检查是否已存在该股票信息
            existing_info = self.stock_info_zh_col.find_one({'Stock Code': stock_code})
            if existing_info:
                # 更新现有记录
                self.stock_info_zh_col.update_one({'_id': existing_info['_id']}, {'$set': stock_info})
            else:
                # 插入新记录
                self.stock_info_zh_col.insert_one(stock_info)

    def insert_announcement(self, announcement: Dict, ann_type: str="report"):
        _col = self.report_ann_col if ann_type == "report" else self.ann_col
        stock_code = announcement.get('STOCK_CODE', '')
        if len(stock_code) > 5:
            begin_code = stock_code[:5]
            end_code = stock_code[-5:]
            if begin_code[0] == '0':
                announcement['STOCK_CODE'] = begin_code
            elif end_code[0] == '0':
                announcement['STOCK_CODE'] = end_code

        file_link = announcement.get('FILE_LINK', "")
        if self.find_announcements({'FILE_LINK': file_link}):
            return
        if isinstance(announcement, dict):
            _col.insert_one(announcement)
        else:
            raise ValueError("Announcement must be a dictionary")
    
    def insert_announcements(self, announcements: List[Dict], ann_type: str="report"):
        _col = self.report_ann_col if ann_type == "report" else self.ann_col
        for ann in announcements:
            stock_code = ann.get('STOCK_CODE', '')
            if len(stock_code) > 5:
                begin_code = stock_code[:5]
                end_code = stock_code[-5:]
                if begin_code[0] == '0':
                    ann['STOCK_CODE'] = begin_code
                elif end_code[0] == '0':
                    ann['STOCK_CODE'] = end_code
            
        _col.insert_many(announcements)

    def find_announcements(self, query: Dict={}, ann_type: str="report") -> List[Dict]:
        _col = self.report_ann_col if ann_type == "report" else self.ann_col
        return list(_col.find(query))
    
    def find_last_announcement(self, query: Dict, ann_type: str="report") -> Dict:
        _col = self.report_ann_col if ann_type == "report" else self.ann_col
        return _col.find_one(query, sort=[('DATE_TIME', pymongo.DESCENDING)])
    
    def correct_stock_code_of_announcements(self, ann_type: str="report"):
        _col = self.report_ann_col if ann_type == "report" else self.ann_col
        all_docs = _col.find()
        for doc in all_docs:
            stock_code = doc.get('STOCK_CODE', '')
            if len(stock_code) <= 5:
                continue
            begin_code = stock_code[:5]
            end_code = stock_code[-5:]
            if begin_code[0] == '0':
                doc['STOCK_CODE'] = begin_code
            elif end_code[0] == '0':
                doc['STOCK_CODE'] = end_code
            else:
                continue
            _col.update_one({'_id': doc['_id']}, {'$set': doc})
            
    
    def correct_datetime_of_announcements(self, ann_type: str="report"):
        _col = self.report_ann_col if ann_type == "report" else self.ann_col
        all_docs = _col.find()
        for doc in all_docs:
            url = doc.get('FILE_LINK', '')
            if not url:
                continue
            eles = url.split('/')
            yymmdd = f"{eles[-3]}{eles[-2]}"
            url_date = str2datetime(yymmdd)
            date_time: datetime.datetime = doc.get('DATE_TIME', None)
            # 转成北京时区
            date_time = date_time.astimezone(pytz.timezone('Asia/Shanghai')) if date_time else None
            if not date_time:
                continue
            date_time = date_time
            if abs(date_time - url_date).days <= 2:
                continue
            if int(date_time.strftime("%d")) > 12:
                continue
            date_time_ex_str = date_time.strftime("%Y-%d-%m %H:%M:%S")
            date_time_ex = str2datetime(date_time_ex_str)
            
            if abs(date_time_ex - url_date).days > abs(date_time - url_date).days and date_time > url_date:
                continue
            
            if abs(date_time_ex - url_date).days <= 2 or \
                (int(date_time_ex.strftime("%m")) <= 12 and int(date_time_ex.strftime("%d")) <= 12 and date_time_ex > url_date):
                doc['DATE_TIME'] = date_time_ex
                _col.update_one({'_id': doc['_id']}, {'$set': doc})
            
            
            
    def close(self):
        self.client.close()