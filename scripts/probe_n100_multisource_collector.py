#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · N100 边缘数据港湾
全市场多源高频数据采集与容灾入库守护引擎 (Production Collector)
"""

import os
import sys
import time
import json
import random
import logging
import argparse
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("probe_collector_run.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("TianYanCollector")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tianyan_market_multiscale.duckdb"
STOCKS_CSV = DATA_DIR / "all_a_stocks.csv"

# 优先 DuckDB
USE_DUCKDB = False
try:
    import duckdb
    USE_DUCKDB = True
    DB_PATH = DATA_DIR / "tianyan_market_multiscale.duckdb"
except ImportError:
    import sqlite3
    USE_DUCKDB = False
    DB_PATH = DATA_DIR / "tianyan_market_multiscale.db"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_headers(referer: str = "https://finance.sina.com.cn/") -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": referer
    }


class MultiScaleDBManager:
    """多尺度时空数据持久化管理器"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.use_duck = USE_DUCKDB
        self._init_tables()

    def _get_conn(self):
        if self.use_duck:
            return duckdb.connect(str(self.db_path))
        import sqlite3
        return sqlite3.connect(str(self.db_path))

    def _init_tables(self):
        with self._get_conn() as con:
            cur = con.cursor() if not self.use_duck else con
            # 1. 宏观 320 交易日 日线大底座
            cur.execute("""
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

            # 2. 波段 5 分钟高清分时线表 (1024根)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS kline_5m (
                code TEXT,
                name TEXT,
                datetime TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, datetime)
            );
            """)

            # 3. 微观尖刀 1 分钟极致分时线表 (1024根)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS kline_1m (
                code TEXT,
                name TEXT,
                datetime TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, datetime)
            );
            """)
            if hasattr(con, "commit"):
                con.commit()
        engine_name = "DuckDB 专库" if self.use_duck else "SQLite3 专库"
        logger.info(f"✓ 数据库三层多时空物理表底座就绪 ({engine_name}): {self.db_path}")

    def save_klines(self, table_name: str, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        date_col = "date" if "date" in records[0] else "datetime"
        with self._get_conn() as con:
            cur = con.cursor() if not self.use_duck else con
            sql = f"""
            INSERT OR REPLACE INTO {table_name} 
            (code, name, {date_col}, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = [
                (r["code"], r["name"], r[date_col], r["open"], r["high"], r["low"], r["close"], r["volume"])
                for r in records
            ]
            cur.executemany(sql, params)
            if hasattr(con, "commit"):
                con.commit()
        return len(records)


class MultiSourceCollector:
    def __init__(self, db_mgr: MultiScaleDBManager):
        self.db = db_mgr

    @staticmethod
    def _format_symbol(code: str) -> str:
        code_str = str(code).zfill(6)
        prefix = "sh" if code_str.startswith(("6", "9")) else "sz"
        return f"{prefix}{code_str}"

    def fetch_sina(self, code: str, name: str, scale: int, datalen: int) -> List[Dict[str, Any]]:
        symbol = self._format_symbol(code)
        url = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={symbol}&scale={scale}&ma=no&datalen={datalen}"
        headers = get_headers()
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode())
                    if not data or not isinstance(data, list):
                        return []
                    records = []
                    is_daily = (scale == 240)
                    date_key = "date" if is_daily else "datetime"
                    for item in data:
                        records.append({
                            "code": str(code).zfill(6),
                            "name": name,
                            date_key: item.get("day", ""),
                            "open": float(item.get("open", 0.0)),
                            "high": float(item.get("high", 0.0)),
                            "low": float(item.get("low", 0.0)),
                            "close": float(item.get("close", 0.0)),
                            "volume": float(item.get("volume", 0.0))
                        })
                    return records
            except Exception:
                time.sleep(0.2)
        return []


def run_collection(total_count: int = 5555):
    logger.info("==================================================")
    logger.info(f"🚀 N100 边缘数据港湾启动全量高频多源收割 (计划总数: {total_count})")
    logger.info("==================================================")

    db_mgr = MultiScaleDBManager(DB_PATH)
    collector = MultiSourceCollector(db_mgr)

    stocks = []
    if STOCKS_CSV.exists():
        with open(STOCKS_CSV, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for l in lines[1:]:
                parts = l.strip().split(",")
                if len(parts) >= 2:
                    stocks.append((parts[0].strip(), parts[1].strip()))
    if not stocks:
        stocks = [("000001", "平安银行"), ("600519", "贵州茅台")]

    target_stocks = stocks[:total_count]
    logger.info(f"✓ 成功加载 A 股股票清单: {len(target_stocks)} 只标的")

    t_start = time.time()
    total_d, total_5m, total_1m = 0, 0, 0

    for idx, (code, name) in enumerate(target_stocks, 1):
        try:
            d_d = collector.fetch_sina(code, name, scale=240, datalen=320)
            n_d = db_mgr.save_klines("kline_daily", d_d)
            total_d += n_d

            d_5m = collector.fetch_sina(code, name, scale=5, datalen=1024)
            n_5m = db_mgr.save_klines("kline_5m", d_5m)
            total_5m += n_5m

            d_1m = collector.fetch_sina(code, name, scale=1, datalen=1024)
            n_1m = db_mgr.save_klines("kline_1m", d_1m)
            total_1m += n_1m

            if idx % 20 == 0 or idx == len(target_stocks):
                elapsed = time.time() - t_start
                rate = idx / max(elapsed, 0.1)
                rem_min = (len(target_stocks) - idx) / max(rate, 0.01) / 60
                logger.info(
                    f"进度: [{idx}/{len(target_stocks)}] ({(idx/len(target_stocks)*100):.1f}%) | "
                    f"最新: {name}({code}) | 速度: {rate:.1f}只/秒 | 预计剩余: {rem_min:.1f}分钟"
                )
            time.sleep(0.12)
        except Exception as e:
            logger.warning(f"标的 {code} 处理异常: {e}")
            time.sleep(0.5)

    logger.info(f"🏆 全量收割大圆满完成！总用时: {(time.time()-t_start)/60:.1f} 分钟！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="天衍五维多源数据全量收割")
    parser.add_argument("--count", type=int, default=5555, help="收割标的数量")
    parser.add_argument("--all", action="store_true", help="全量全市场 5555 只")
    args = parser.parse_args()
    cnt = 5555 if args.all else args.count
    run_collection(cnt)
