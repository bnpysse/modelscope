#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维 · N100 私人量化节点
66日滚动 Level 2 主力资金与微观大单特征管道 (FIFO 滚动队列)
专库专用: tianyan_l2_66d.duckdb
"""

import os
import sys
import time
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional

import duckdb
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tianyan_l2_66d.duckdb"


class Rolling66dL2Pipeline:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with duckdb.connect(str(self.db_path)) as con:
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
            """)

    def fetch_66d_fund_flow(self, code: str, name: str = "") -> Optional[pd.DataFrame]:
        """带官方客户端鉴权的近 66 个交易日主力分单历史序列拉取"""
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
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status != 200:
                        continue
                    data = json.loads(resp.read().decode())
                    if not data or data.get("rc") != 0 or not data.get("data"):
                        continue
                    
                    raw_name = data["data"].get("name", name) or f"标的{code_str}"
                    klines = data["data"].get("klines", [])
                    if not klines:
                        continue

                    records = []
                    for item in klines:
                        parts = item.split(",")
                        if len(parts) >= 13:
                            records.append({
                                "code": code_str,
                                "name": raw_name,
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
                    df = df.sort_values("date").reset_index(drop=True)

                    if len(df) > 66:
                        df = df.tail(66).reset_index(drop=True)

                    # 偏微分滑动面积计算 (5日/22日/66日滑动求和)
                    df["sum_5d"] = df["main_net"].rolling(5, min_periods=1).sum()
                    df["sum_22d"] = df["main_net"].rolling(22, min_periods=1).sum()
                    df["sum_66d"] = df["main_net"].rolling(66, min_periods=1).sum()
                    
                    denom = np.abs(df["main_net"]) + 1e-4
                    df["super_ratio"] = np.clip(df["super_net"] / denom, -1.0, 1.0)

                    return df
            except Exception:
                time.sleep(0.3)
        return None

    def ingest_stock(self, code: str, name: str = "") -> bool:
        """更新并入库单只标的"""
        df = self.fetch_66d_fund_flow(code, name)
        if df is None or df.empty:
            return False

        with duckdb.connect(str(self.db_path)) as con:
            con.register("df_view", df)
            con.execute("""
            INSERT OR REPLACE INTO l2_daily_fund_flow (
                code, name, date, close, pct_chg, main_net, super_net, large_net, mid_net, small_net,
                sum_5d, sum_22d, sum_66d, super_ratio
            )
            SELECT code, name, date, close, pct_chg, main_net, super_net, large_net, mid_net, small_net,
                   sum_5d, sum_22d, sum_66d, super_ratio
            FROM df_view;
            """)

            # FIFO 滚动淘汰：仅保留最新 66 个交易日，清理过期旧切片
            con.execute("""
            DELETE FROM l2_daily_fund_flow
            WHERE code = ?
              AND date NOT IN (
                  SELECT date FROM l2_daily_fund_flow
                  WHERE code = ?
                  ORDER BY date DESC
                  LIMIT 66
              );
            """, [code, code])

        return True

    def run_batch(self, stock_list: List[Dict[str, str]]) -> Dict[str, int]:
        """批量调度处理"""
        success = 0
        failed = 0
        print(f"🚀 开始为 {len(stock_list)} 只标的调度 66 日 Level 2 主力资金流与微观大单管道...")
        for s in stock_list:
            c = s.get("code")
            n = s.get("name", "")
            ok = self.ingest_stock(c, n)
            if ok:
                success += 1
            else:
                failed += 1
            time.sleep(0.05)
        print(f"✅ 调度完成！成功: {success} 只，失败: {failed} 只。已安全锁定于 DuckDB。")
        return {"success": success, "failed": failed}


if __name__ == "__main__":
    targets = [
        {"code": "001309", "name": "德明利"},
        {"code": "301171", "name": "易天股份"},
        {"code": "688525", "name": "佰维存储"},
        {"code": "301308", "name": "江波龙"},
        {"code": "300475", "name": "香农芯创"},
        {"code": "300308", "name": "中际旭创"},
        {"code": "300378", "name": "鼎捷数智"},
        {"code": "002885", "name": "京泉华"},
    ]
    pipe = Rolling66dL2Pipeline()
    pipe.run_batch(targets)

    with duckdb.connect(str(pipe.db_path)) as con:
        res = con.execute("""
        SELECT code, name, count(*) as days_count, 
               min(date) as min_date, max(date) as max_date,
               round(sum(main_net)/1e8, 2) as total_main_net_yi,
               round(sum(super_net)/1e8, 2) as total_super_net_yi
        FROM l2_daily_fund_flow
        GROUP BY code, name
        ORDER BY code;
        """).fetchall()
        print("\n📊 N100 数据库 66 日滚动特征池入库明细 (包含超大单):")
        for r in res:
            print(f"  ● {r[1]} ({r[0]}): 跨度 {r[3]} ~ {r[4]} ({r[2]}天), 主力净买: {r[5]}亿, 超大单净买: {r[6]}亿")
