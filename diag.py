# -*- coding: utf-8 -*-
"""诊断6：找带文章URL、海外可达的财经新闻源，用于消息面分条+超链接。"""
import json
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"


def dump(tag, url, headers=None):
    try:
        r = requests.get(url, headers=headers or {"User-Agent": UA}, timeout=20)
        print(f"[{tag}] HTTP {r.status_code} len={len(r.text)}")
        try:
            j = r.json()
            print(f"  top keys: {list(j.keys())[:10]}")
            # 尝试定位列表
            def find_list(o, depth=0):
                if depth > 4:
                    return None
                if isinstance(o, list) and o and isinstance(o[0], dict):
                    return o
                if isinstance(o, dict):
                    for v in o.values():
                        r = find_list(v, depth + 1)
                        if r:
                            return r
                return None
            lst = find_list(j)
            if lst:
                print(f"  item keys: {list(lst[0].keys())}")
                print(f"  sample: {json.dumps(lst[0], ensure_ascii=False)[:300]}")
        except Exception as e:
            print("  not json / parse err:", e, "::", r.text[:120])
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
    print("-" * 55)


# 1. 东方财富 7x24 快讯（当前在用）
dump("em-fast", "https://np-weblist.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize=8&req_trace=1")
# 2. 东方财富 要闻/财经导读
dump("em-news", "https://np-listapi.eastmoney.com/comm/web/getNewsList?client=web&biz=web_news&column=350&order=1&needInteractData=0&pageindex=1&pagesize=8&req_trace=2&fields=code,title,url,showTime")
# 3. 财联社 电报
dump("cls", "https://www.cls.cn/nodeapi/updateTelegraphList?app=CailianpressWeb&os=web&rn=8")
# 4. 新浪财经 要闻 feed
dump("sina", "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=1686&num=8&page=1")
