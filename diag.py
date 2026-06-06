# -*- coding: utf-8 -*-
"""诊断4：找非东财、海外可达、含板块涨跌榜的网页(用于web兜底+DeepSeek提取)。"""
import re
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
KW = ["半导体", "通信设备", "航天", "元件", "电机", "板块", "领涨", "领跌"]


def show(tag, url, enc=None, headers=None):
    try:
        r = requests.get(url, headers=headers or {"User-Agent": UA}, timeout=20)
        if enc:
            r.encoding = enc
        t = r.text
        hits = [k for k in KW if k in t]
        # 抓几个 "名字+百分比" 样例
        pcts = re.findall(r"[一-龥]{2,8}[^\d%]{0,6}(?:-|\+)?\d+\.\d{1,2}%", t)[:4]
        print(f"[{tag}] HTTP {r.status_code} len={len(t)} kw={hits} pctSamples={pcts}")
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
    print("-" * 55)


# 1. 同花顺 行业板块页(HTML)
show("ths-thshy", "https://q.10jqka.com.cn/thshy/")
# 2. 同花顺 板块数据接口(尝试)
show("ths-api", "https://q.10jqka.com.cn/api/v1/plate/list/field/199112/order/desc/page/1/size/10/type/THS")
# 3. 财联社 电报
show("cls-tele", "https://www.cls.cn/telegraph")
# 4. 证券时报
show("stcn", "https://www.stcn.com/article/list/gs.html")
# 5. 新浪 行业(申万) 板块页
show("sina-bk", "https://vip.stock.finance.sina.com.cn/mkt/#industry_swl2", enc="gbk")
# 6. 雪球 行业板块(可能需token)
show("xq", "https://xueqiu.com/hq")
# 7. 东财行业HTML页(对照，可能同样限流)
show("em-html", "https://quote.eastmoney.com/center/boardlist.html")
