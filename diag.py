# -*- coding: utf-8 -*-
"""诊断7：验证东财快讯 code -> 文章URL 模式是否可访问。"""
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
H = {"User-Agent": UA}

r = requests.get("https://np-weblist.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&pageSize=5&req_trace=1", headers=H, timeout=20)
items = r.json()["data"]["fastNewsList"]
for it in items[:4]:
    code = it["code"]
    title = it["title"]
    for pat in [f"https://finance.eastmoney.com/a/{code}.html"]:
        try:
            rr = requests.get(pat, headers=H, timeout=20)
            ok = title[:6] in rr.text
            print(f"code={code} HTTP {rr.status_code} len={len(rr.text)} titleInPage={ok} url={pat}")
        except Exception as e:
            print(f"code={code} ERR {e}")
    print("  title:", title)
