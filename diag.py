# -*- coding: utf-8 -*-
"""诊断3：找一个独立于东财push2、海外可达、含申万行业涨跌幅榜的源。"""
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def show(tag, url, headers=None):
    try:
        r = requests.get(url, headers=headers or {"User-Agent": UA}, timeout=20)
        print(f"[{tag}] HTTP {r.status_code} len={len(r.text)} :: {r.text[:200]!r}")
    except Exception as e:
        print(f"[{tag}] ERROR {e}")
    print("-" * 55)


# 1. 东财 push2 + 完整浏览器头 + Cookie（测请求头/Cookie理论）
emh = {
    "User-Agent": UA,
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://quote.eastmoney.com/center/boardlist.html",
    "Cookie": "qgqp_b_id=abc123def456; st_pvi=00000000000000",
}
show("em-fullhdr", "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b", emh)
# 2. 东财备用 CDN 节点
show("em-1node", "https://1.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b", emh)
show("em-7node", "https://7.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fid=f3&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b", emh)
# 3. 腾讯：候选板块路由
show("tx-r1", "https://proxy.finance.qq.com/cgi/cgicombineserv/group/list/get?app=web&category=hybk")
show("tx-r2", "https://proxy.finance.qq.com/cgi/cgicombineserv/sector/list/get?app=web&type=hangye")
show("tx-r3", "https://web.ifzq.gtimg.cn/appstock/app/mktHs/rank?p=1&l=20&t=hangye&o=0&ff=1")
show("tx-r4", "https://proxy.finance.qq.com/cgi/cgicombineserv/group/detail/get?app=web&category=hybk&start=0&size=10&sortField=zdf&direct=0")
# 4. 网易：行业板块
show("ne-bk", "https://quotes.money.163.com/hs/service/diyrank.php?host=quotes.money.163.com&page=0&query=PLATE_IDS:1000001000&fields=NAME,PERCENT&sort=PERCENT&order=desc&count=10&type=query")
