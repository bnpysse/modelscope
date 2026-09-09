#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · 全市场超短情绪雷达与舆情前哨 (Sentiment & Catalyst Radar)
集成 Layer 8 打板连板情绪池、财联社实时电报与交易所重点监控/异动池
"""

import time
import json
import hashlib
import requests
import datetime
from typing import Dict, Any, List, Optional

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
ZTB_UT = "7eea3edcaed734bea9cbfc24409ed989"


def _fmt_zt_time(t: Any) -> str:
    s = str(t).zfill(6)
    return f"{s[0:2]}:{s[2:4]}:{s[4:6]}" if len(s) == 6 else str(t)


def fetch_limit_up_pool(date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取指定交易日（默认今日）的涨停板标的池"""
    if not date_str:
        date_str = datetime.date.today().strftime("%Y%m%d")
    else:
        date_str = date_str.replace("-", "")

    url = "https://push2ex.eastmoney.com/getTopicZTPool"
    params = {
        "ut": ZTB_UT,
        "dpt": "wz.ztzt",
        "Pageindex": 0,
        "pagesize": 200,
        "sort": "fbt:asc",
        "date": date_str
    }
    headers = {"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=6)
        data = r.json()
        pool = (data.get("data") or {}).get("pool") or []
        out = []
        for p in pool:
            out.append({
                "code": str(p.get("c", "")).zfill(6),
                "name": p.get("n", ""),
                "price": round(float(p.get("p", 0.0)) / 1000.0, 2),
                "pct": round(float(p.get("zdp", 0.0)), 2),
                "amount": p.get("amount", 0),
                "turnover": round(float(p.get("hs", 0.0)), 2),
                "limit_days": p.get("lbc", 1),
                "first_seal": _fmt_zt_time(p.get("fbt", "")),
                "last_seal": _fmt_zt_time(p.get("lbt", "")),
                "seal_fund": p.get("fund", 0),
                "break_times": p.get("zbc", 0),
                "industry": p.get("hybk", ""),
                "zt_stat": p.get("days", "")
            })
        return out
    except Exception:
        return []


def fetch_limit_down_pool(date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取跌停池"""
    if not date_str:
        date_str = datetime.date.today().strftime("%Y%m%d")
    else:
        date_str = date_str.replace("-", "")

    url = "https://push2ex.eastmoney.com/getTopicDTPool"
    params = {
        "ut": ZTB_UT,
        "dpt": "wz.ztzt",
        "Pageindex": 0,
        "pagesize": 100,
        "sort": "fund:asc",
        "date": date_str
    }
    headers = {"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=6)
        data = r.json()
        pool = (data.get("data") or {}).get("pool") or []
        out = []
        for p in pool:
            out.append({
                "code": str(p.get("c", "")).zfill(6),
                "name": p.get("n", ""),
                "price": round(float(p.get("p", 0.0)) / 1000.0, 2),
                "pct": round(float(p.get("zdp", 0.0)), 2),
                "amount": p.get("amount", 0),
                "limit_days": p.get("lbc", 1),
                "industry": p.get("hybk", "")
            })
        return out
    except Exception:
        return []


def fetch_broken_board_pool(date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取炸板池"""
    if not date_str:
        date_str = datetime.date.today().strftime("%Y%m%d")
    else:
        date_str = date_str.replace("-", "")

    url = "https://push2ex.eastmoney.com/getTopicZBPool"
    params = {
        "ut": ZTB_UT,
        "dpt": "wz.ztzt",
        "Pageindex": 0,
        "pagesize": 100,
        "sort": "fbt:asc",
        "date": date_str
    }
    headers = {"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=6)
        data = r.json()
        pool = (data.get("data") or {}).get("pool") or []
        out = []
        for p in pool:
            out.append({
                "code": str(p.get("c", "")).zfill(6),
                "name": p.get("n", ""),
                "price": round(float(p.get("p", 0.0)) / 1000.0, 2),
                "pct": round(float(p.get("zdp", 0.0)), 2),
                "break_times": p.get("zbc", 0),
                "industry": p.get("hybk", "")
            })
        return out
    except Exception:
        return []


def calculate_sentiment_summary(date_str: Optional[str] = None) -> Dict[str, Any]:
    """打板情绪温度计：连板梯队 + 炸板率 + 涨停/跌停对比"""
    zt = fetch_limit_up_pool(date_str)
    zb = fetch_broken_board_pool(date_str)
    dt = fetch_limit_down_pool(date_str)

    # 梯队分布
    ladder = {}
    for s in zt:
        lbc = s["limit_days"]
        ladder[lbc] = ladder.get(lbc, 0) + 1

    total_attempt = len(zt) + len(zb)
    break_rate = round(len(zb) / total_attempt * 100.0, 1) if total_attempt > 0 else 0.0
    max_height = max((s["limit_days"] for s in zt), default=0)

    # 热门行业统计
    ind_count = {}
    for s in zt:
        ind = s.get("industry") or "其他"
        ind_count[ind] = ind_count.get(ind, 0) + 1
    top_industries = sorted(ind_count.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "date": date_str or datetime.date.today().strftime("%Y-%m-%d"),
        "zt_count": len(zt),
        "zb_count": len(zb),
        "dt_count": len(dt),
        "break_rate": break_rate,
        "max_height": max_height,
        "ladder": dict(sorted(ladder.items())),
        "top_industries": top_industries,
        "zt_samples": zt[:15],
        "zb_samples": zb[:10]
    }


def fetch_cls_telegraph(page_size: int = 25) -> List[Dict[str, str]]:
    """财联社实时电报（零 Key，纯本地 md5(sha1) 签名）"""
    params = {
        "appName": "CailianpressWeb", "os": "web", "sv": "7.7.5",
        "last_time": "", "refresh_type": "1", "rn": str(page_size)
    }
    qs = "&".join(f"{k}={params[k]}" for k in sorted(params))
    sign = hashlib.md5(hashlib.sha1(qs.encode()).hexdigest().encode()).hexdigest()
    url = f"https://www.cls.cn/v1/roll/get_roll_list?{qs}&sign={sign}"
    headers = {"User-Agent": UA, "Referer": "https://www.cls.cn/"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        d = r.json()
        items = (d.get("data") or {}).get("roll_data") or []
        rows = []
        for it in items:
            ts = it.get("ctime")
            t_str = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else ""
            title = it.get("title") or it.get("brief") or ""
            content = it.get("content") or it.get("brief") or ""
            rows.append({
                "time": t_str,
                "title": title.strip(),
                "content": content.strip()
            })
        return rows
    except Exception:
        return []


def fetch_stock_monitors() -> List[Dict[str, Any]]:
    """获取交易所重点监控与风险警示标的"""
    url = "https://mobappconfig.securities.eastmoney.com/emcfg/stock_monitor.json"
    headers = {"User-Agent": UA, "Referer": "https://vipmoney.eastmoney.com/"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        rows = r.json() or []
        today = datetime.date.today().strftime("%Y-%m-%d")
        out = []
        for x in rows:
            start = x.get("VALIDATESTARTDATE", "")
            end = x.get("VALIDATEENDDATE", "")
            # 只保留当前生效的
            if start <= today <= end:
                out.append({
                    "code": str(x.get("STKCODE", "")).zfill(6),
                    "name": x.get("STKNAME", ""),
                    "start": start,
                    "end": end
                })
        return out
    except Exception:
        return []


def fetch_intraday_minute_chart(code: str) -> Dict[str, Any]:
    """
    拉取个股当日毫秒级分时全量走势 (腾讯行情接口)
    返回:
    {
        "code": "000523",
        "name": "红棉股份",
        "prev_close": 3.96,
        "latest_price": 4.36,
        "pct_chg": 10.10,
        "high": 4.36,
        "low": 4.36,
        "volume": 123456,
        "amount": 5432100.0,
        "times": ["09:30", "09:31", ...],
        "prices": [4.36, 4.36, ...],
        "volumes": [1000, 2000, ...],
        "vwap": [4.36, 4.36, ...]
    }
    """
    code_clean = str(code).zfill(6)
    prefix = "sh" if code_clean.startswith(("6", "9")) else "sz"
    symbol = f"{prefix}{code_clean}"
    url = f"https://web.ifzq.gtimg.cn/appstock/app/minute/query?code={symbol}"
    
    headers = {"User-Agent": UA, "Referer": "https://finance.qq.com/"}
    try:
        r = requests.get(url, headers=headers, timeout=6)
        data = r.json()
        raw_stock = data.get("data", {}).get(symbol, {})
        minute_rows = raw_stock.get("data", {}).get("data") or []
        qt = raw_stock.get("qt", {}).get(symbol, [])
        
        name = qt[1] if len(qt) > 1 else f"标的{code_clean}"
        latest_p = float(qt[3]) if len(qt) > 3 and qt[3] else 0.0
        prev_c = float(qt[4]) if len(qt) > 4 and qt[4] else latest_p
        high_p = float(qt[33]) if len(qt) > 33 and qt[33] else latest_p
        low_p = float(qt[34]) if len(qt) > 34 and qt[34] else latest_p
        total_vol = float(qt[36]) if len(qt) > 36 and qt[36] else 0.0
        total_amt = float(qt[37]) if len(qt) > 37 and qt[37] else 0.0
        pct_chg = round((latest_p - prev_c) / prev_c * 100.0, 2) if prev_c > 0 else 0.0

        times = []
        prices = []
        volumes = []
        amounts = []
        vwap = []

        cum_amt = 0.0
        cum_vol = 0.0
        for item in minute_rows:
            # 格式: '0930 4.36 100893 43989348.00' (时间, 现价, 累计/当分量, 累计/当分金额)
            parts = item.split(" ")
            if len(parts) >= 2:
                t_raw = parts[0]
                t_fmt = f"{t_raw[:2]}:{t_raw[2:]}"
                p = float(parts[1])
                v = float(parts[2]) if len(parts) > 2 else 0.0
                a = float(parts[3]) if len(parts) > 3 else 0.0
                
                times.append(t_fmt)
                prices.append(p)
                volumes.append(v)
                amounts.append(a)
                
                # 均线计算
                if a > cum_amt and v > cum_vol:
                    cum_amt = a
                    cum_vol = v
                    vwap.append(round(cum_amt / (cum_vol * 100.0), 2) if cum_vol > 0 else p)
                else:
                    vwap.append(vwap[-1] if vwap else p)

        return {
            "code": code_clean,
            "name": name,
            "prev_close": prev_c,
            "latest_price": latest_p,
            "pct_chg": pct_chg,
            "high": high_p,
            "low": low_p,
            "volume": total_vol,
            "amount": total_amt,
            "times": times,
            "prices": prices,
            "volumes": volumes,
            "vwap": vwap
        }
    except Exception as e:
        return {"code": code_clean, "name": f"标的{code_clean}", "error": str(e)}

