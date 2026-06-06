# -*- coding: utf-8 -*-
"""诊断5：同花顺行业板块 ajax 数据接口（带涨跌幅的表格）。"""
import re
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
H = {"User-Agent": UA, "Referer": "https://q.10jqka.com.cn/thshy/"}


def show(tag, url, enc="gbk"):
    try:
        r = requests.get(url, headers=H, timeout=20)
        r.encoding = enc
        t = r.text
        # 提取 板块名 + 百分比 对
        pairs = re.findall(r'<a[^>]*>([一-龥A-Za-z0-9]{2,10})</a>.{0,200?}?(-?\d+\.\d{2})%', t)
        names = re.findall(r'/code/\d+/[^>]*>([一-龥]{2,10})<', t)
        pcts = re.findall(r'(-?\d+\.\d{2})%', t)
        print(f"[{tag}] HTTP {r.status_code} len={len(t)} names={names[:8]} pcts={pcts[:8]}")
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
    print("-" * 55)


# 涨幅榜（field 199112 = 涨跌幅, order desc）
show("ths-up", "https://q.10jqka.com.cn/thshy/index/field/199112/order/desc/page/1/ajax/1/")
# 跌幅榜（order asc）
show("ths-down", "https://q.10jqka.com.cn/thshy/index/field/199112/order/asc/page/1/ajax/1/")
