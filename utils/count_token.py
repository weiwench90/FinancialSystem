#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tiktoken

def count_tokens(text: str, model: str = "gpt-4o-mini"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def count_tokens_messages(messages, model="gpt-4o-mini"):
    enc = tiktoken.encoding_for_model(model)
    # 简单粗暴：把 role + content 全拼起来编码
    total = 0
    for m in messages:
        total += len(enc.encode(m["role"]))
        # content 可能是字符串或列表（多段），自己展开
        if isinstance(m["content"], str):
            total += len(enc.encode(m["content"]))
        else:
            # OpenAI 的新格式可能是 [{"type":"text","text":"..."}, ...]
            for part in m["content"]:
                total += len(enc.encode(part.get("text","")))
    return total
