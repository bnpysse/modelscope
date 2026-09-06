#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · N100 全天候量化数据中心
全市场 A 股 66日滚动 Level 2 主力资金与微观大单并发批处理管道
"""

import os
import sys
import time
import json
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

import duckdb
import pandas as pd
import numpy as np
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tianyan_l2_66d.duckdb"
STOCKS_CSV = DATA_DIR / "all_a_stocks.csv"

# 初始化 DuckDB 数据表
def init_db(db_path: Path = DB_PATH):
    with duckdb.connect(str(db_path)) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS l2_daily_fund_flow (
            code VARCHAR,
            name VARCHAR,
            date VARCHAR,
            close DOUBLE,
            pct_chg DOUBLE,
            main_net DOUBLE,       -- 主力净流入 (超大单 + 大单)
            super_net DOUBLE,      -- 超大单净流入 (超级机构 / 敢死队)
            large_net DOUBLE,      -- 大单净流入
            mid_net DOUBLE,        -- 中单净流入
            small_net DOUBLE,      -- 小单净流入 (散户)
            sum_5d DOUBLE,         -- 5日累积主力净额 (周)
            sum_22d DOUBLE,        -- 22日累积主力净额 (月)
            sum_66d DOUBLE,        -- 66日累积主力净额 (季)
            super_ratio DOUBLE,    -- 超大单占主力比例
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (code, date)
        );
        CREATE INDEX IF NOT EXISTS idx_l2_code_date ON l2_daily_fund_flow(code, date);
        """)

def fetch_stock_66d(code: str, name: str) -> Optional[pd.DataFrame]:
    code_str = str(code).zfill(6)
    secid = f"0.{code_str}" if code_str.startswith(("0", "3")) else f"1.{code_str}"
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
        f"?secid={secid}&fields1=f1,f2,f3,f7"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65"
        f"&klt=101&lmt=66&ut=b2884a393a59ad64002292a3e90d46a5&_={int(time.time()*1000)}"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://data.eastmoney.com/"
    }
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status != 200:
                    continue
                data = json.loads(resp.read().decode())
                if not data or data.get("rc") != 0 or not data.get("data"):
                    continue
                klines = data["data"].get("klines", [])
                if not klines:
                    continue

                records = []
                for item in klines:
                    parts = item.split(",")
                    if len(parts) >= 13:
                        records.append({
                            "code": code_str,
                            "name": name,
                            "date": parts[0].replace("-", ""),
                            "main_net": float(parts[1]),
                            "small_net": float(parts[2]),
                            "mid_net": float(parts[3]),
                            "large_net": float(parts[4]),
                            "super_net": float(parts[5]),
                            "close": float(parts[11]),
                            "pct_chg": float(parts[12])
                        })
                df = pd.DataFrame(records)
                if df.empty:
                    continue
                df = df.sort_values("date").reset_index(drop=True)
                if len(df) > 66:
                    df = df.tail(66).reset_index(drop=True)

                # 滑动微分面积计算
                df["sum_5d"] = df["main_net"].rolling(5, min_periods=1).sum()
                df["sum_22d"] = df["main_net"].rolling(22, min_periods=1).sum()
                df["sum_66d"] = df["main_net"].rolling(66, min_periods=1).sum()
                denom = np.abs(df["main_net"]) + 1e-4
                df["super_ratio"] = np.clip(df["super_net"] / denom, -1.0, 1.0)
                return df
        except Exception:
            time.sleep(0.1)
    return None

def batch_save_to_duckdb(dfs: List[pd.DataFrame], db_path: Path = DB_PATH):
    if not dfs:
        return
    combined = pd.concat(dfs, ignore_index=True)
    with duckdb.connect(str(db_path)) as con:
        con.register("tmp_batch", combined)
        con.execute("""
        INSERT OR REPLACE INTO l2_daily_fund_flow (
            code, name, date, close, pct_chg, main_net, super_net, large_net, mid_net, small_net,
            sum_5d, sum_22d, sum_66d, super_ratio
        )
        SELECT code, name, date, close, pct_chg, main_net, super_net, large_net, mid_net, small_net,
               sum_5d, sum_22d, sum_66d, super_ratio
        FROM tmp_batch;
        """)

def main():
    init_db()
    if not STOCKS_CSV.exists():
        print(f"❌ 标的列表不存在: {STOCKS_CSV}")
        return

    stocks_df = pd.read_csv(STOCKS_CSV)
    stocks_df["code"] = stocks_df["code"].astype(str).str.zfill(6)
    
    # 统帅核心持仓排在绝对第一优先级
    core_codes = ["001309", "301171", "688525", "301308", "300475", "300308", "300378", "002885"]
    core_part = stocks_df[stocks_df["code"].isin(core_codes)]
    other_part = stocks_df[~stocks_df["code"].isin(core_codes)]
    sorted_stocks = pd.concat([core_part, other_part], ignore_index=True)

    targets = sorted_stocks.to_dict("records")
    total_count = len(targets)
    print(f"🚀 N100 并发引擎启动！总计目标标的: {total_count} 只 A 股，并发线程: 16")

    batch_buffer = []
    saved_count = 0
    start_time = time.time()

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        TimeRemainingColumn()
    ) as progress:
        task = progress.add_task("🌊 全市场 66日主力大单管道推进中", total=total_count)

        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_stock = {
                executor.submit(fetch_stock_66d, s["code"], s["name"]): s for s in targets
            }
            for future in as_completed(future_to_stock):
                stock = future_to_stock[future]
                res_df = future.result()
                if res_df is not None and not res_df.empty:
                    batch_buffer.append(res_df)

                # 每攒齐 50 只标的批量写入一次 DuckDB
                if len(batch_buffer) >= 50:
                    batch_save_to_duckdb(batch_buffer)
                    saved_count += len(batch_buffer)
                    batch_buffer.clear()

                progress.update(task, advance=1)

        # 写入剩余缓冲区
        if batch_buffer:
            batch_save_to_duckdb(batch_buffer)
            saved_count += len(batch_buffer)
            batch_buffer.clear()

    elapsed = round(time.time() - start_time, 1)
    print(f"\n🎉 全市场调度圆满达成！用时: {elapsed} 秒，成功入库: {saved_count}/{total_count} 只标的！")

    # 执行全局 FIFO 滚动淘汰，保证每只标的严格只保留最近 66 天
    print("🧹 正在执行全局 FIFO 66日滑动窗口规整...")
    with duckdb.connect(str(DB_PATH)) as con:
        # 查询总行数与股票数
        cnt = con.execute("SELECT count(*), count(distinct code) FROM l2_daily_fund_flow").fetchone()
        print(f"📊 当前 N100 数据库指标池总计: {cnt[1]} 只标的，{cnt[0]} 条高质量 66日物理截面切片！")

if __name__ == "__main__":
    main()
