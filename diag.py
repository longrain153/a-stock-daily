# -*- coding: utf-8 -*-
"""诊断7b：稳健验证东财快讯 code -> 文章URL。"""
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
H = {"User-Agent": UA, "Referer": "https://kuaixun.eastmoney.com/"}

url = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize=6&req_trace=1"
r = requests.get(url, headers=H, timeout=20)
print("fastnews HTTP", r.status_code, "len", len(r.text))
j = r.json()
data = j.get("data")
print("data type:", type(data).__name__, "keys:", list(data.keys()) if isinstance(data, dict) else data)
items = (data or {}).get("fastNewsList") or []
print("items:", len(items))
for it in items[:4]:
    code = it.get("code")
    title = (it.get("title") or "")[:8]
    cand = [
        f"https://finance.eastmoney.com/a/{code}.html",
        f"https://kuaixun.eastmoney.com/{code}.html",
    ]
    for u in cand:
        try:
            rr = requests.get(u, headers=H, timeout=20, allow_redirects=True)
            inpage = title in rr.text
            print(f"  {u} -> HTTP {rr.status_code} len={len(rr.text)} titleInPage={inpage}")
        except Exception as e:
            print(f"  {u} -> ERR {e}")
    print("  TITLE:", it.get("title"))
