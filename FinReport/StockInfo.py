#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .sehk_api.hk_api import (
    symbol2code, get_stock_announcements_direct
)
from utils.download import download_file
from Database.hk_mongo import HkAnnouncementsDB
import pandas as pd
from utils.str_utils import convert_traditional_to_simplified
import time
import datetime
import os

mongo_db = HkAnnouncementsDB()

class HkStockInfo:
    def __init__(self, symbol):
        self.symbol = symbol
        self.report_file_root = f"/home/data/SEHK/FinReports/{self.symbol}/"
        info = symbol2code(symbol)
        if info:
            self.name = info[0]["name"]
            self.stockId = info[0]["stockId"]

    def update_announcements(self, ann_type: str="report"):
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
        last_record = mongo_db.find_last_announcement({'STOCK_CODE': self.symbol}, ann_type=ann_type)
        if last_record:
            until = last_record["DATE_TIME"]
        else:
            until = None
        if ann_type == "report":
            tier1 = 40000
        else:
            tier1 = 10000
        cur_date = datetime.datetime.now(tz=datetime.timezone.utc)
        if until and (cur_date - until).days < 1:
            return False
        cur_announcements = get_stock_announcements_direct(stockId=self.stockId,
                                                           tier1=tier1, 
                                                           until=until)
        if cur_announcements:
            mongo_db.insert_announcements(cur_announcements, ann_type=ann_type)
        return True
    
    
    def download_report_files(self):
        anns = mongo_db.find_announcements({'STOCK_CODE': self.symbol}, ann_type="report")
        anns2 = mongo_db.find_announcements({'STOCK_CODE': self.symbol}, ann_type="normal")
        for ann in anns + anns2:
            title = ann['TITLE']
            for keyword in ["年报", "中报", "季报", 
                            "全年业绩", "年度业绩", "半年度业绩", "中期业绩", "季度业绩",
                            "年度报告", "半年度报告", "中期报告", "季度报告", 
                            "盈利公告", "盈利预告", "业绩公告", "业绩预告"]:
                combine_text = ann.get("SHORT_TEXT", "")+"|"+ann.get("LONG_TEXT", "")+"|"+title
                if keyword in convert_traditional_to_simplified(combine_text):
                    break
            else:
                continue
            file_type = ann['FILE_TYPE'].lower()
            url = "https://www1.hkexnews.hk/" + ann['FILE_LINK'].lstrip("/")
            if os.path.exists(self.report_file_root+f"{title}.{file_type}"):
                continue
            download_file(url, f"{title}.{file_type}", self.report_file_root)
            time.sleep(1)


class HkStockInfoManager:
    def __init__(self):
        pass
        
    def update_stock_info(self):
        url_list_of_securities = "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx"
        # url_list_of_securities_c = "https://www.hkex.com.hk/chi/services/trading/securities/securitieslists/ListOfSecurities_c.xlsx"
        download_file(url_list_of_securities, 
                      "FinReport/StockInfo/ListOfSecurities.xlsx")
        # download_file(url_list_of_securities_c, "ListOfSecurities_c.xlsx")
        # 解析 Excel 文件
        df = pd.read_excel("FinReport/StockInfo/ListOfSecurities.xlsx", 
                   sheet_name="ListOfSecurities",
                   header=2)
        # df_c = pd.read_excel("ListOfSecurities_c.xlsx",
        #            sheet_name="ListOfSecurities",
        #            header=2)
        mongo_db.update_stocks_info(df.to_dict(orient='records'))
    
    def update_stock_info_zh(self):
        url_list_of_securities_c = "https://www.hkex.com.hk/chi/services/trading/securities/securitieslists/ListOfSecurities_c.xlsx"
        download_file(url_list_of_securities_c, "FinReport/StockInfo/ListOfSecurities_c.xlsx")
        df_c = pd.read_excel("FinReport/StockInfo/ListOfSecurities_c.xlsx",
                               sheet_name="ListOfSecurities",
                               header=2)
        mongo_db.update_stocks_info_zh(df_c.to_dict(orient='records'))

    def update_all_announcements(self, ann_report: str="report"):
        stock_symbols = mongo_db.stock_symbol_list()
        for symbol in stock_symbols:
            try:
                stock_info = HkStockInfo(symbol)
                if stock_info.update_announcements(ann_report):
                    time.sleep(1)  # 避免请求过快导致服务器拒绝服务
                print(f"Updated announcements for {symbol} - {stock_info.name}")
            except Exception as e:
                print(f"Error updating {symbol}: {e}")
    
    def download_all_report_files(self):
        stock_symbols = mongo_db.stock_symbol_list()
        for symbol in stock_symbols:
            try:
                stock_info = HkStockInfo(symbol)
                stock_info.download_report_files()
                print(f"Downloaded report files for {symbol} - {stock_info.name}")
            except Exception as e:
                print(f"Error updating {symbol}: {e}")