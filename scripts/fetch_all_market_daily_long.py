#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · N100 边缘数据港湾
全市场 A 股超长周期全息日线库构建引擎 (覆盖 200周线 / 1950交易日 / 8年时空纵深)
"""

import os
import sys
import time
import json
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
import duckdb
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "tianyan_market_multiscale.duckdb"
STOCKS_CSV = DATA_DIR / "all_a_stocks.csv"

def get_target_stocks() -> List[Tuple[str, str]]:
    stocks = []
    if STOCKS_CSV.exists():
        with open(STOCKS_CSV, "r", encoding="utf-8") as f:
            for l in f.readlines()[1:]:
                parts = l.strip().split(",")
                if len(parts) >= 2:
                    stocks.append((parts[0].strip().zfill(6), parts[1].strip()))
    return stocks

def fetch_sina_daily_long(code: str, name: str, datalen: int = 1950) -> List[Dict[str, Any]]:
    prefix = "sh" if code.startswith(("6", "9")) else "sz"
    symbol = f"{prefix}{code}"
    url = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={datalen}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://finance.sina.com.cn/"
    }
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode())
                if not data or not isinstance(data, list):
                    return []
                records = []
                for item in data:
                    records.append({
                        "code": code,
                        "name": name,
                        "date": item.get("day", ""),
                        "open": float(item.get("open", 0.0)),
                        "high": float(item.get("high", 0.0)),
                        "low": float(item.get("low", 0.0)),
                        "close": float(item.get("close", 0.0)),
                        "volume": float(item.get("volume", 0.0))
                    })
                return records
        except Exception:
            time.sleep(0.3)
    return []

def run_pipeline(max_workers: int = 16, limit: int = None):
    stocks = get_target_stocks()
    if limit:
        stocks = stocks[:limit]
    total_stocks = len(stocks)
    print(f"🚀 N100 全天候引擎启动: 目标 {total_stocks} 只 A 股，时空深度 1,950 交易日 (8年)，并发线程: {max_workers}")

    con = duckdb.connect(str(DB_PATH))
    con.execute("""
    CREATE TABLE IF NOT EXISTS kline_daily (
        code TEXT,
        name TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (code, date)
    );
    """)

    t0 = time.time()
    batch_records = []
    total_inserted = 0
    completed_stocks = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(fetch_sina_daily_long, code, name): (code, name) for code, name in stocks}
        
        for future in as_completed(future_map):
            code, name = future_map[future]
            try:
                records = future.result()
                if records:
                    batch_records.extend(records)
                completed_stocks += 1

                if len(batch_records) >= 30000 or completed_stocks == total_stocks:
                    if batch_records:
                        df_batch = pd.DataFrame(batch_records)
                        con.execute("INSERT OR REPLACE INTO kline_daily (code, name, date, open, high, low, close, volume) SELECT code, name, date, open, high, low, close, volume FROM df_batch")
                        total_inserted += len(df_batch)
                        batch_records = []

                if completed_stocks % 200 == 0 or completed_stocks == total_stocks:
                    elapsed = time.time() - t0
                    speed = completed_stocks / max(elapsed, 0.1)
                    eta_min = (total_stocks - completed_stocks) / max(speed, 0.1) / 60.0
                    print(f"[{completed_stocks}/{total_stocks}] ({completed_stocks/total_stocks*100:.1f}%) | 速度: {speed:.1f}只/秒 | 已入库行数: {total_inserted:,} | 预计剩余: {eta_min:.1f}分钟")
            except Exception as e:
                pass

    con.close()
    print(f"🏆 全息超长日线库构建圆满完成！总计入库: {total_inserted:,} 行，总耗时: {(time.time()-t0)/60.0:.2f} 分钟！")

if __name__ == "__main__":
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_pipeline(max_workers=16, limit=limit_arg)
