# -*- coding: utf-8 -*-
"""
A股每日复盘 - 云端版（GitHub Actions）
流程：取行情数据(新浪/东方财富) -> DeepSeek 写分析 -> 生成HTML -> Gmail SMTP 发送
所有密钥从环境变量(GitHub Secrets)读取。
"""
import os
import re
import json
import smtplib
import datetime as dt
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

import requests

BJ = dt.timezone(dt.timedelta(hours=8))  # 北京时间


def beijing_now():
    return dt.datetime.now(BJ)


# ----------------------------------------------------------------------------
# 1. 行情数据采集
# ----------------------------------------------------------------------------
def fetch_indices():
    """指数：上证/深证成指/创业板指/科创50。主源新浪，备源东方财富。
    返回 (indices_list, data_date_str)。"""
    codes = ["sh000001", "sz399001", "sz399006", "sh000688"]
    url = "https://hq.sinajs.cn/list=" + ",".join(codes)
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
    indices, data_date = [], None
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = "gbk"
        for line in r.text.split("\n"):
            if '="' not in line:
                continue
            q = line.split('="', 1)[1].rstrip('";\r')
            f = q.split(",")
            if len(f) < 10:
                continue
            prev, cur = float(f[2]), float(f[3])
            pct = round((cur - prev) / prev * 100, 2) if prev else 0.0
            indices.append({
                "name": f[0],
                "close": round(cur, 2),
                "change": round(cur - prev, 2),
                "pct": pct,
                "amount_yi": round(float(f[9]) / 1e8, 2) if f[9] else None,
            })
            m = re.search(r"\d{4}-\d{2}-\d{2}", q)
            if m and not data_date:
                data_date = m.group(0)
    except Exception as e:
        print("sina indices failed:", e)

    if not indices:  # 备源：东方财富
        try:
            eu = ("https://push2.eastmoney.com/api/qt/ulist.np/get?"
                  "secids=1.000001,0.399001,0.399006,1.000688&fields=f2,f3,f4,f6,f12,f14"
                  "&ut=fa5fd1943c7b386f172d6893dbfba10b")
            d = requests.get(eu, headers={"User-Agent": "Mozilla/5.0",
                                          "Referer": "https://quote.eastmoney.com/"}, timeout=20).json()
            for x in d["data"]["diff"]:
                indices.append({
                    "name": x["f14"], "close": round(x["f2"] / 100, 2),
                    "change": round(x["f4"] / 100, 2), "pct": round(x["f3"] / 100, 2),
                    "amount_yi": round(x["f6"] / 1e8, 2),
                })
        except Exception as e:
            print("eastmoney indices failed:", e)
    return indices, data_date


def fetch_sectors():
    """行业板块涨幅/跌幅榜（东方财富）。"""
    base = ("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=6&np=1&fid=f3"
            "&fs=m:90+t:2&fields=f3,f14&ut=fa5fd1943c7b386f172d6893dbfba10b&po=")
    h = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}
    up, down = [], []
    for po, bucket in (("1", up), ("0", down)):
        try:
            d = requests.get(base + po, headers=h, timeout=20).json()
            for x in d["data"]["diff"]:
                bucket.append({"name": x["f14"], "pct": round(x["f3"] / 100, 2)})
        except Exception as e:
            print("sectors po=%s failed:" % po, e)
    return up, down


def fetch_limitup(ymd):
    """涨停池家数（东方财富 push2ex）。"""
    try:
        u = ("https://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989"
             "&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt%3Aasc&date=" + ymd)
        d = requests.get(u, headers={"User-Agent": "Mozilla/5.0",
                                     "Referer": "https://quote.eastmoney.com/"}, timeout=20).json()
        data = d.get("data") or {}
        cnt = data.get("total")
        names = [p.get("n") for p in (data.get("pool") or [])][:8]
        if cnt is None and data.get("pool"):
            cnt = len(data["pool"])
        return {"count": cnt, "sampleNames": names}
    except Exception as e:
        print("limitup failed:", e)
        return None


def fetch_news():
    """best-effort 抓取财经快讯标题（东方财富7x24）。失败返回[]。"""
    try:
        u = ("https://np-weblist.eastmoney.com/comm/web/getFastNewsList?"
             "client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize=12&req_trace=1")
        d = requests.get(u, headers={"User-Agent": "Mozilla/5.0",
                                     "Referer": "https://kuaixun.eastmoney.com/"}, timeout=20).json()
        items = d.get("data", {}).get("fastNewsList", []) or []
        titles = []
        for it in items:
            t = (it.get("title") or it.get("summary") or "").strip()
            if t:
                titles.append(t[:80])
        return titles[:10]
    except Exception as e:
        print("news failed:", e)
        return []


# ----------------------------------------------------------------------------
# 2. DeepSeek 分析
# ----------------------------------------------------------------------------
def deepseek_analyze(date_str, indices, up, down, limitup, news):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return None
    data_txt = {
        "日期": date_str,
        "指数": indices,
        "领涨板块": up,
        "领跌板块": down,
        "涨停": limitup,
        "财经快讯标题": news,
    }
    sys = ("你是资深A股市场分析师。基于提供的当日真实行情数据，写一份客观、专业的收盘复盘。"
           "只依据给定数据与标题，不要编造不存在的数字。返回严格的JSON。")
    user = (
        "以下是今天A股的真实数据(JSON)：\n" + json.dumps(data_txt, ensure_ascii=False) +
        "\n\n请输出JSON，字段如下，全部用中文：\n"
        "{\n"
        '  "index_comment": "对四大指数与成交额的解读，3-4句",\n'
        '  "sector_comment": "对领涨领跌板块与涨停情况的解读及市场主线判断，3-4句",\n'
        '  "news_summary": "结合财经快讯标题(若为空则说明无实时快讯，仅据盘面)梳理影响市场的消息面，3-5条，用分号或换行分隔",\n'
        '  "strategy": "次日关注方向与风险提示，2-4句，不得出现具体买卖个股建议，结尾不需要免责声明"\n'
        "}"
    )
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": sys},
                      {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=0.4,
            timeout=90,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print("deepseek failed:", e)
        return None


# ----------------------------------------------------------------------------
# 3. HTML 生成
# ----------------------------------------------------------------------------
def color(v):
    return "#c0392b" if (v or 0) > 0 else ("#27ae60" if (v or 0) < 0 else "#6b7280")


def build_html(date_str, weekday_cn, indices, up, down, limitup, analysis):
    rows = ""
    for x in indices:
        c = color(x["pct"])
        amt = ("%.1f亿" % x["amount_yi"]) if x.get("amount_yi") else "—"
        rows += (
            f'<tr><td style="padding:9px 10px;border-bottom:1px solid #f0f0f0;">{x["name"]}</td>'
            f'<td style="padding:9px 10px;border-bottom:1px solid #f0f0f0;text-align:right;">{x["close"]}</td>'
            f'<td style="padding:9px 10px;border-bottom:1px solid #f0f0f0;text-align:right;color:{c};">{x["change"]:+}</td>'
            f'<td style="padding:9px 10px;border-bottom:1px solid #f0f0f0;text-align:right;color:{c};font-weight:600;">{x["pct"]:+}%</td>'
            f'<td style="padding:9px 10px;border-bottom:1px solid #f0f0f0;text-align:right;color:#6b7280;">{amt}</td></tr>'
        )

    def sector_line(lst, clr):
        if not lst:
            return '<span style="color:#9ca3af;">数据暂缺</span>'
        return "、".join(f'{s["name"]} <span style="color:{clr};">{s["pct"]:+}%</span>' for s in lst[:5])

    lu = "数据暂缺"
    if limitup and limitup.get("count") is not None:
        lu = f'{limitup["count"]} 家'
        if limitup.get("sampleNames"):
            lu += "（部分：" + "、".join(limitup["sampleNames"][:6]) + "）"

    a = analysis or {}
    idx_c = a.get("index_comment", "（AI分析未生成，以上为行情数据。）")
    sec_c = a.get("sector_comment", "")
    news_c = a.get("news_summary", "")
    strat = a.get("strategy", "")
    news_html = news_c.replace("\n", "<br>") if news_c else "（暂无）"

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>A股每日复盘 · {date_str}</title></head>
<body style="margin:0;padding:0;background:#f4f5f7;font-family:'Microsoft YaHei',-apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:#1f2329;">
<div style="max-width:680px;margin:0 auto;padding:20px;">
  <div style="background:#1f2937;border-radius:10px 10px 0 0;padding:22px 24px;">
    <div style="color:#fff;font-size:22px;font-weight:700;">A股每日复盘 · {date_str}（{weekday_cn}）</div>
    <div style="color:#9ca3af;font-size:13px;margin-top:6px;">收盘后行情梳理 · GitHub Actions 自动生成 · 分析由 DeepSeek 提供</div>
  </div>

  <div style="background:#fff;padding:20px 24px;">
    <div style="font-size:17px;font-weight:700;border-left:4px solid #2563eb;padding-left:10px;margin-bottom:14px;">一、大盘指数复盘</div>
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead><tr style="background:#f3f4f6;color:#374151;">
        <th style="text-align:left;padding:9px 10px;border-bottom:1px solid #e5e7eb;">指数</th>
        <th style="text-align:right;padding:9px 10px;border-bottom:1px solid #e5e7eb;">收盘</th>
        <th style="text-align:right;padding:9px 10px;border-bottom:1px solid #e5e7eb;">涨跌点</th>
        <th style="text-align:right;padding:9px 10px;border-bottom:1px solid #e5e7eb;">涨跌幅</th>
        <th style="text-align:right;padding:9px 10px;border-bottom:1px solid #e5e7eb;">成交额</th>
      </tr></thead><tbody>{rows}</tbody></table>
    <div style="font-size:13px;color:#374151;margin-top:12px;line-height:1.8;">{idx_c}</div>
    <div style="font-size:13px;color:#6b7280;margin-top:8px;">涨停家数：{lu}　·　北向资金：自2024年8月起不再实时披露</div>
  </div>

  <div style="background:#fff;padding:20px 24px;border-top:1px solid #f0f0f0;">
    <div style="font-size:17px;font-weight:700;border-left:4px solid #2563eb;padding-left:10px;margin-bottom:14px;">二、板块与热点</div>
    <div style="font-size:14px;line-height:1.9;color:#374151;">
      <b style="color:#c0392b;">领涨板块：</b>{sector_line(up, "#c0392b")}<br>
      <b style="color:#27ae60;">领跌板块：</b>{sector_line(down, "#27ae60")}<br>
      <div style="margin-top:8px;">{sec_c}</div>
    </div>
  </div>

  <div style="background:#fff;padding:20px 24px;border-top:1px solid #f0f0f0;">
    <div style="font-size:17px;font-weight:700;border-left:4px solid #2563eb;padding-left:10px;margin-bottom:14px;">三、消息面与政策</div>
    <div style="font-size:14px;line-height:1.9;color:#374151;">{news_html}</div>
  </div>

  <div style="background:#fff;padding:20px 24px;border-top:1px solid #f0f0f0;">
    <div style="font-size:17px;font-weight:700;border-left:4px solid #2563eb;padding-left:10px;margin-bottom:14px;">四、次日策略提示</div>
    <div style="font-size:14px;line-height:1.9;color:#374151;">{strat}</div>
    <div style="margin-top:14px;padding:12px 14px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;font-size:12px;color:#6b7280;line-height:1.7;">
      以上为行情信息梳理，<b>不构成任何投资建议</b>。数据来源：指数=新浪财经，板块/涨停=东方财富；分析由 DeepSeek 生成，可能存在错漏，请以交易所正式数据为准。
    </div>
  </div>
  <div style="text-align:center;color:#9ca3af;font-size:12px;padding:16px;">A股Agent · 云端自动推送 · {date_str}</div>
</div></body></html>"""


# ----------------------------------------------------------------------------
# 4. 发送邮件
# ----------------------------------------------------------------------------
def send_email(subject, html):
    user = os.environ["GMAIL_USER"]
    pwd = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
    to = os.environ.get("MAIL_TO", user)
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header("A股Agent", "utf-8")), user))
    msg["To"] = to
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls()
        s.login(user, pwd)
        s.sendmail(user, [x.strip() for x in to.split(",")], msg.as_string())
    print("email sent to", to)


# ----------------------------------------------------------------------------
def main():
    now = beijing_now()
    dash = now.strftime("%Y-%m-%d")
    ymd = now.strftime("%Y%m%d")
    weekday_cn = "一二三四五六日"[now.weekday()]
    weekday_cn = "周" + weekday_cn

    force = os.environ.get("FORCE_SEND", "").lower() in ("1", "true", "yes")

    indices, data_date = fetch_indices()

    # 交易日判断：若指数数据日期与今天不一致（或无数据），视为休市/异常 -> 不发送
    # FORCE_SEND=1（手动测试）时跳过此判断，强制用最近收盘数据发送
    if not indices:
        print("no index data; abort.")
        return
    if data_date and data_date != dash and not force:
        print(f"market closed today (data date {data_date} != {dash}); skip sending.")
        return
    if data_date and data_date != dash and force:
        print(f"FORCE_SEND on: sending with latest close data dated {data_date}.")
        dash = data_date  # 报告标题用真实数据日期
        try:
            d = dt.datetime.strptime(data_date, "%Y-%m-%d")
            weekday_cn = "周" + "一二三四五六日"[d.weekday()]
            ymd = d.strftime("%Y%m%d")
        except Exception:
            pass

    up, down = fetch_sectors()
    limitup = fetch_limitup(ymd)
    news = fetch_news()
    analysis = deepseek_analyze(dash, indices, up, down, limitup, news)

    html = build_html(dash, weekday_cn, indices, up, down, limitup, analysis)
    send_email(f"A股每日复盘 {dash}", html)


if __name__ == "__main__":
    main()
