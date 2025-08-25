#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from openai import OpenAI
import json
from utils.extract import extract_json
from config import api_key, base_url

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)


def split_markdown_by_h1(md_text: str):
    fragments = []
    current_fragment = []

    for line in md_text.splitlines():
        if line.startswith("## "):  # 一级标题
            if current_fragment:
                fragments.append("\n".join(current_fragment).strip())
                current_fragment = []
        current_fragment.append(line)
    if current_fragment:
        fragments.append("\n".join(current_fragment).strip())

    return fragments


def extract_financial_statements(pdf_content: str):
    contents = split_markdown_by_h1(pdf_content)

    prompt = (
        "从user给出的财报中，先找到3大报表所在页码，返回格式:\n"
        "{\n"
        "  \"income_statement\": 1,\n"
        "  \"balance_sheet\": 2,\n"
        "  \"cash_flow_statement\": 3\n"
        "}\n"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": "\n".join(contents[:15])
            }
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    pages = extract_json(response.choices[0].message.content)

    income_statement_page_range = (pages["income_statement"]-5, pages["income_statement"]+5)
    balance_sheet_page = (pages["balance_sheet"]-5, pages["balance_sheet"]+5)
    cash_flow_statement_page = (pages["cash_flow_statement"]-5, pages["cash_flow_statement"]+5)

    total_pages = list(range(*income_statement_page_range)) + list(range(*balance_sheet_page)) + list(range(*cash_flow_statement_page))
    total_pages = list(set(total_pages))  # 去重
    total_pages.sort()
    statement_content = "\n".join(contents[i-1] for i in total_pages)
    return statement_content


def parse_statement_to_json(statement_content: str):
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role": "system",
                "content": (
                    "从user给出的财报内容中，提取出完整的三大报表内容，输出json格式，返回格式:\n"
                    "{\n"
                    "  \"income_statement\": {\n"
                    "    \"revenue\": \"1000,000\",\n"
                    "    \"expenses\": \"500,000\",\n"
                    "    \"expenses-sale&marketing\": \"300,000\"\n"
                    "    \"expenses-R&D\": \"200,000\"\n"
                    "  },\n"
                    "  \"balance_sheet\": { ... },\n"
                    "  \"cash_flow_statement\": { ... }\,n"
                    "  \"notes\": {\n"
                    "    \"expenses-R&D\": 14,\n"
                    "    \"expenses-sale&marketing\": 15\n"
                    "  }\n"
                    "}\n"
                    "规则:\n"
                    "1. 所有数字都去掉千分位逗号，保留小数点\n"
                    "2. 字段名称用 '-' 表示子项目，可以是多级的\n"
                    "3. 完整列出财报中所有的字段，哪怕是空值，名字也必须相同（如果提供了英文名，优先采用英文）\n"
                    "4. notes中列出所有有注释的字段和对应的注释编号\n"
                )
            },
            {
                "role": "user",
                "content": statement_content
            }
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    

    return extract_json(response.choices[0].message.content)