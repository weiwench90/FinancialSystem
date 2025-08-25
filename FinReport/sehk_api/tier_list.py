#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import datetime

headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        )
}

def tierone():
    url = "https://www1.hkexnews.hk/ncms/script/eds/tierone_c.json"
    payload = {
        "_": int(datetime.datetime.now().timestamp() * 1000)
    }
    response = requests.get(url, params=payload, headers=headers)
    ret = response.json()
    return ret

def tiertwo():
    url = "https://www1.hkexnews.hk/ncms/script/eds/tiertwo_c.json"
    payload = {
        "_": int(datetime.datetime.now().timestamp() * 1000)
    }
    response = requests.get(url, params=payload, headers=headers)
    ret = response.json()
    return ret

def tiertwo_group():
    url = "https://www1.hkexnews.hk/ncms/script/eds/tiertwogrp_c.json"
    payload = {
        "_": int(datetime.datetime.now().timestamp() * 1000)
    }
    response = requests.get(url, params=payload, headers=headers)
    ret = response.json()
    return ret