# -*- coding: utf-8 -*-
"""临时诊断：从 GitHub runner 测试多个"申万/东财口径"行业板块接口的可达性。"""
import requests

H = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}
HS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}


def show(tag, url, headers=H, enc=None):
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if enc:
            r.encoding = enc
        body = r.text
        print(f"[{tag}] HTTP {r.status_code} len={len(body)} :: {body[:220]!r}")
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
    print("-" * 60)


# 1. 东方财富 push2 clist 行业板块（标准）
show("em-push2", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b")
# 2. 东方财富 带 JSONP 回调
show("em-jsonp", "https://push2.eastmoney.com/api/qt/clist/get?cb=x&pn=1&pz=5&po=1&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b")
# 3. 东方财富编号 CDN 节点
show("em-13node", "https://13.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b")
# 4. 东方财富 push2ex（涨停同host，已知可达）测一个板块接口
show("em-push2ex", "https://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=1&sort=fbt%3Aasc&date=20260605")
# 5. 腾讯行业板块
show("tx-sector", "https://proxy.finance.qq.com/cgi/cgicombineserv/group/detail/get?app=web&category=hybk")
# 6. 腾讯 web 行情接口测试
show("tx-stock", "https://qt.gtimg.cn/q=sh000001", enc="gbk")
# 7. 新浪申万节点尝试（getHQNodeData 不同 node）
show("sina-sw", "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=5&sort=changepercent&asc=0&node=sw_2", headers=HS, enc="gbk")
