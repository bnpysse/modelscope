#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场 5000+ A 股极速流水线采集与五维微积分实时计算引擎 (稳定单会话流式架构)
1. 采用 BaoStock 单长连接低延迟批量流式拉取 5115 只 A 股
2. 边下载日线边实时微积分求解五维因子，双向落盘
3. 每 50 只输出详细进度与耗时心跳，支持中断自动秒级续跑
"""

import os
import sys
import time
from pathlib import Path
from typing import List

if os.path.exists("/mnt/workspace"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = WORKSPACE_DIR / "quant_data"
RAW_DIR = DATA_DIR / "all_a_shares_parquet"
FACTORS_DIR = DATA_DIR / "factors"
RAW_DIR.mkdir(parents=True, exist_ok=True)
FACTORS_DIR.mkdir(parents=True, exist_ok=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import polars as pl
import baostock as bs
from core.quant_chip_engine import chip_engine
from core.ai_advisor import evaluate_local_tactical_status


def get_all_a_share_universe() -> List[dict]:
    """获取全市场有效 A 股列表"""
    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")

    rs = bs.query_all_stock(day="2024-06-28")
    stock_list = []
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        bs_code = row[0]
        status = row[1]
        name = row[2] if len(row) > 2 else ""
        
        if bs_code.startswith(("sh.60", "sh.688", "sz.00", "sz.300", "sz.301")):
            stock_list.append({
                "bs_code": bs_code,
                "clean_code": bs_code.split(".")[-1],
                "name": name,
                "trade_status": status
            })

    bs.logout()
    return stock_list


def run_batch_market_ingest(start_date: str = "2023-01-01", max_count: int = 0):
    stocks = get_all_a_share_universe()
    if max_count > 0:
        stocks = stocks[:max_count]

    total_stocks = len(stocks)
    print("================================================================================")
    print(f"🚀 [全市场 5000+ A 股日线采集与微积分一体化引擎] 标的总量: {total_stocks} 只")
    print(f"📁 存储目录: {DATA_DIR}")
    print("================================================================================")

    fields = "date,code,open,high,low,close,volume,amount,turn,pctChg"
    str_schema = [
        ("Date", pl.Utf8), ("Code", pl.Utf8),
        ("Open", pl.Utf8), ("High", pl.Utf8), ("Low", pl.Utf8), ("Close", pl.Utf8),
        ("Volume", pl.Utf8), ("Amount", pl.Utf8), ("Turnover", pl.Utf8), ("Pct_Chg", pl.Utf8)
    ]

    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")

    success_cnt = 0
    skip_cnt = 0
    fail_cnt = 0
    t0 = time.time()
    t_batch = time.time()

    summary_records = []

    try:
        for idx, item in enumerate(stocks):
            bs_code = item["bs_code"]
            clean_code = item["clean_code"]
            name = item["name"]

            raw_path = RAW_DIR / f"{clean_code}.parquet"
            factor_path = FACTORS_DIR / f"{clean_code}_factors.parquet"

            # 1. 检查是否已存在完整因子
            if factor_path.exists() and factor_path.stat().st_size > 2048:
                skip_cnt += 1
                continue

            # 2. 拉取历史日线
            rs = bs.query_history_k_data_plus(
                bs_code,
                fields,
                start_date=start_date,
                frequency="d",
                adjustflag="2"  # 前复权
            )

            data = []
            while (rs.error_code == '0') & rs.next():
                data.append(rs.get_row_data())

            if not data or len(data) < 5:
                fail_cnt += 1
                continue

            # 3. 安全清洗空值与停牌字符串
            raw_df = pl.DataFrame(data, orient="row", schema=str_schema)
            df = raw_df.with_columns([
                pl.col("Open").replace("", None).cast(pl.Float64, strict=False),
                pl.col("High").replace("", None).cast(pl.Float64, strict=False),
                pl.col("Low").replace("", None).cast(pl.Float64, strict=False),
                pl.col("Close").replace("", None).cast(pl.Float64, strict=False),
                pl.col("Volume").replace("", None).cast(pl.Float64, strict=False),
                pl.col("Amount").replace("", None).cast(pl.Float64, strict=False),
                pl.col("Turnover").replace("", None).cast(pl.Float64, strict=False),
                pl.col("Pct_Chg").replace("", None).cast(pl.Float64, strict=False),
            ]).drop_nulls(subset=["Close", "Turnover"])

            if df.is_empty() or len(df) < 5:
                fail_cnt += 1
                continue

            # 4. 落盘原始日线
            df.write_parquet(raw_path, compression="zstd")

            # 5. 实时执行五维筹码物理场微积分递推
            factors_df = chip_engine.compute_mcd_series(df)
            factors_df.write_parquet(factor_path, compression="zstd")

            # 提取最新截面
            latest = factors_df.tail(1).to_dicts()[0]
            local_eval = evaluate_local_tactical_status(latest)
            summary_records.append({
                "code": clean_code,
                "name": name,
                "date": str(latest.get("Date", "")),
                "close": round(float(latest.get("Close", 0.0)), 2),
                "Z_profit": round(float(latest.get("Z_Profit", 0.0)), 2),
                "Z_prime": round(float(latest.get("Z_diff1", 0.0)), 2),
                "ASR": round(float(latest.get("ASR", 0.0)), 2),
                "X70": round(float(latest.get("X70", 0.0)), 2),
                "X90": round(float(latest.get("X90", 0.0)), 2),
                "LFS": round(float(latest.get("LFS", 0.0)), 2),
                "HCCYF13": round(float(latest.get("HCCYF13", 0.0)), 2),
                "Scissor": round(float(latest.get("Scissor", 0.0)), 2),
                "CYS34": round(float(latest.get("CYS34", 0.0)), 2),
                "BIAS_5_20": round(float(latest.get("BIAS_5_20", 0.0)), 4),
                "order": local_eval["order"],
            })

            success_cnt += 1

            # 每 50 只打印一次实时心跳并更新全市场截面快照
            if (idx + 1) % 50 == 0 or (idx + 1) == total_stocks:
                now = time.time()
                speed = 50.0 / max(0.1, (now - t_batch))
                t_batch = now
                progress_pct = round((idx + 1) / total_stocks * 100, 1)
                total_elapsed = round(now - t0, 1)
                
                print(f"📊 [实时进度] 已处理 {idx + 1}/{total_stocks} ({progress_pct}%) | 新增: {success_cnt} | 跳过: {skip_cnt} | 速度: {speed:.1f} 股/秒 | 累计耗时: {total_elapsed}s")
                
                # 增量落盘全市场最新快照
                if summary_records:
                    pl.DataFrame(summary_records).write_parquet(DATA_DIR / "full_market_snapshot.parquet", compression="zstd")

    finally:
        bs.logout()

    elapsed = round(time.time() - t0, 2)
    print("\n================================================================================")
    print(f"🎉 全市场 5000+ A 股数据采集与五维微积分全部计算完毕！总耗时: {elapsed} 秒")
    print(f"📊 成功落盘: {success_cnt} 只 | 跳过已有: {skip_cnt} 只 | 异常停牌: {fail_cnt} 只")
    print(f"📁 因子数据库已保存至: {FACTORS_DIR}")
    print("================================================================================")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run_batch_market_ingest(start_date="2023-01-01", max_count=limit)
