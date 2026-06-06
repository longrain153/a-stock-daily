# -*- coding: utf-8 -*-
"""诊断2：隔离东财板块接口失败原因 + 测试涨停池自带行业字段。"""
import json
import requests

H = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}


def show(tag, url):
    try:
        r = requests.get(url, headers=H, timeout=20)
        print(f"[{tag}] HTTP {r.status_code} len={len(r.text)} :: {r.text[:200]!r}")
        return r
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
    finally:
        print("-" * 50)


# A. 诊断1里成功过的精确 URL（pz=5, po在中部）
show("A_diagstyle", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b")
# B. 主程序式 URL（pz=12, po在末尾）
show("B_mainstyle", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=12&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b&po=1")
# C. 再请求一次 A 式（看连续两次是否被限流）
show("C_diagstyle2", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b")
# D. 涨停池完整字段（看是否含行业 hybk）
r = show("D_ztpool", "https://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=3&sort=fbt%3Aasc&date=20260605")
try:
    pool = r.json()["data"]["pool"]
    print("ZTPOOL keys:", list(pool[0].keys()))
    for p in pool:
        print("  ", p.get("n"), "| hybk=", p.get("hybk"))
except Exception as e:
    print("ztpool parse err", e)
