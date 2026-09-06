#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · N100 边缘数据港湾
全量 A 股 5分钟线 66 交易日 (3个月纵深) 历史增量回填引擎 (BaoStock 专线)
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import duckdb
import baostock as bs

BASE_DIR = Path("/root/tianyan_l2_etl")
if not BASE_DIR.exists():
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tianyan_market_multiscale.duckdb"
STOCKS_CSV = DATA_DIR / "all_a_stocks.csv"
PROGRESS_FILE = DATA_DIR / "backfill_5m_progress.json"
LOG_FILE = BASE_DIR / "backfill_5m.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("TianYanBackfill5M")


def load_stocks() -> List[Dict[str, str]]:
    stocks = []
    if STOCKS_CSV.exists():
        with open(STOCKS_CSV, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for l in lines[1:]:
                parts = l.strip().split(",")
                if len(parts) >= 2:
                    c = parts[0].strip().zfill(6)
                    n = parts[1].strip()
                    bs_code = f"sh.{c}" if c.startswith(("6", "9")) else f"sz.{c}"
                    stocks.append({"code": c, "name": n, "bs_code": bs_code})
    return stocks


def load_completed_codes() -> set:
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("completed", []))
        except Exception:
            pass
    return set()


def save_completed_codes(completed: set):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({"completed": list(completed), "count": len(completed), "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
    except Exception:
        pass


def run_backfill(start_date: str = "2026-06-01", end_date: str = "2026-07-24", batch_size: int = 50):
    all_stocks = load_stocks()
    completed = load_completed_codes()
    pending = [s for s in all_stocks if s["code"] not in completed]

    logger.info("==================================================")
    logger.info(f"🚀 启动 5分钟线 66日历史回填 (总标的: {len(all_stocks)}, 待补全: {len(pending)})")
    logger.info(f"📅 回填时空区间: {start_date} ~ {end_date}")
    logger.info("==================================================")

    if not pending:
        logger.info("✅ 所有标的 5 分钟线历史已回填完毕！")
        return

    lg = bs.login()
    if lg.error_code != '0':
        logger.error(f"❌ BaoStock 登录失败: {lg.error_msg}")
        return

    con = duckdb.connect(str(DB_PATH))
    batch_records = []
    t_start = time.time()
    total_saved = 0

    try:
        for idx, item in enumerate(pending, 1):
            code = item["code"]
            name = item["name"]
            bs_code = item["bs_code"]

            try:
                rs = bs.query_history_k_data_plus(
                    bs_code,
                    "date,time,code,open,high,low,close,volume",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="5",
                    adjustflag="3"
                )
                if rs.error_code == '0' and rs.data:
                    for row in rs.data:
                        raw_time = row[1]
                        if len(raw_time) >= 14:
                            fmt_dt = f"{raw_time[:4]}-{raw_time[4:6]}-{raw_time[6:8]} {raw_time[8:10]}:{raw_time[10:12]}:{raw_time[12:14]}"
                        else:
                            fmt_dt = f"{row[0]} 15:00:00"
                        batch_records.append((
                            code,
                            name,
                            fmt_dt,
                            float(row[3] or 0.0),
                            float(row[4] or 0.0),
                            float(row[5] or 0.0),
                            float(row[6] or 0.0),
                            float(row[7] or 0.0)
                        ))
                completed.add(code)
            except Exception as e:
                logger.warning(f"⚠️ 拉取 {code} 异常: {e}")

            if len(batch_records) >= 1000 or idx == len(pending):
                if batch_records:
                    con.executemany("""
                    INSERT OR REPLACE INTO kline_5m 
                    (code, name, datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch_records)
                    total_saved += len(batch_records)
                    batch_records = []
                save_completed_codes(completed)

                elapsed = time.time() - t_start
                rate = idx / max(elapsed, 0.1)
                rem_min = (len(pending) - idx) / max(rate, 0.01) / 60
                logger.info(
                    f"进度: [{idx}/{len(pending)}] ({(idx/len(pending)*100):.1f}%) | "
                    f"最新: {name}({code}) | 已入库: {total_saved} 条 | 速度: {rate:.1f}标的/秒 | 预计剩余: {rem_min:.1f}分"
                )

            time.sleep(0.05)

    finally:
        if batch_records:
            con.executemany("""
            INSERT OR REPLACE INTO kline_5m 
            (code, name, datetime, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch_records)
            save_completed_codes(completed)
        con.close()
        bs.logout()
        logger.info(f"🏆 回填作业完成！总新增入库: {total_saved} 条 5分钟记录！")


if __name__ == "__main__":
    run_backfill()
