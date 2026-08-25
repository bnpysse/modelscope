#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场 5000+ A 股日线数据批量下载 + 高精五维筹码物理场微积分全量计算流水线
1. 专线批量拉取 5115 只有效 A 股完整前复权历史日线 (ZSTD Parquet)
2. 批量执行 MCD 移动成本分布积分，生成全市场 5000+ 标的五维因子库
3. 聚合生成全市场最新截面宽表 full_market_snapshot.parquet
4. DuckDB 极速战术扫描输出全市场【真空走廊】与【黄金坑】精选榜单
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

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

import numpy as np
import polars as pl
import baostock as bs
import duckdb
from tqdm import tqdm
from core.quant_chip_engine import chip_engine
from core.ai_advisor import evaluate_local_tactical_status


def get_all_a_share_symbols() -> List[dict]:
    """获取全市场 5000+ 有效 A 股列表"""
    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")

    # 使用有效交易日基准查询全市场清单
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


def step1_download_all_a_shares(stock_list: List[dict], start_date: str = "2023-01-01", max_count: int = 0) -> int:
    """阶段一：批量下载历史日线数据"""
    if max_count > 0:
        stock_list = stock_list[:max_count]

    print(f"\n================================================================================")
    print(f"📥 [阶段 1/3] 启动全市场历史日线批量采集 (标的总量: {len(stock_list)} 只, 起始: {start_date})")
    print(f"📁 原始落盘路径: {RAW_DIR}")
    print(f"================================================================================")

    fields = "date,code,open,high,low,close,volume,amount,turn,pctChg"
    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")

    success_cnt = 0
    skip_cnt = 0
    fail_cnt = 0
    t0 = time.time()

    try:
        for idx, item in enumerate(tqdm(stock_list, desc="1.日线采集进度", unit="股")):
            bs_code = item["bs_code"]
            clean_code = item["clean_code"]
            save_path = RAW_DIR / f"{clean_code}.parquet"

            if save_path.exists() and save_path.stat().st_size > 1024:
                skip_cnt += 1
                continue

            rs = bs.query_history_k_data_plus(
                bs_code,
                fields,
                start_date=start_date,
                frequency="d",
                adjustflag="2"
            )

            data = []
            while (rs.error_code == '0') & rs.next():
                data.append(rs.get_row_data())

            if not data or len(data) < 5:
                fail_cnt += 1
                continue

            df = pl.DataFrame(data, orient="row", schema=[
                ("Date", pl.Utf8), ("Code", pl.Utf8),
                ("Open", pl.Float64), ("High", pl.Float64), ("Low", pl.Float64), ("Close", pl.Float64),
                ("Volume", pl.Float64), ("Amount", pl.Float64), ("Turnover", pl.Float64), ("Pct_Chg", pl.Float64)
            ])
            df.write_parquet(save_path, compression="zstd")
            success_cnt += 1
    finally:
        bs.logout()

    elapsed = round(time.time() - t0, 1)
    print(f"✅ 日线采集完成！新增: {success_cnt} 只 | 跳过已有: {skip_cnt} 只 | 耗时: {elapsed}s\n")
    return success_cnt + skip_cnt


def step2_compute_all_factors() -> pl.DataFrame:
    """阶段二：全市场 MCD 筹码物理场微积分批量递推"""
    parquet_files = list(RAW_DIR.glob("*.parquet"))
    print(f"================================================================================")
    print(f"⚡ [阶段 2/3] 启动全市场五维筹码微积分批量计算 (待处理标的: {len(parquet_files)} 只)")
    print(f"📁 因子库存储路径: {FACTORS_DIR}")
    print(f"================================================================================")

    t0 = time.time()
    snapshot_records = []

    for p_file in tqdm(parquet_files, desc="2.筹码微积分计算", unit="股"):
        clean_code = p_file.stem
        try:
            raw_df = pl.read_parquet(p_file)
            if raw_df.is_empty() or len(raw_df) < 5:
                continue

            # 执行高精微积分计算
            factors_df = chip_engine.compute_mcd_series(raw_df)
            
            # 保存该股票全历史因子时间序列
            factor_out = FACTORS_DIR / f"{clean_code}_factors.parquet"
            factors_df.write_parquet(factor_out, compression="zstd")

            # 提取最新一日截面特征
            latest = factors_df.tail(1).to_dicts()[0]
            local_eval = evaluate_local_tactical_status(latest)

            snapshot_records.append({
                "code": clean_code,
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
        except Exception:
            continue

    elapsed = round(time.time() - t0, 2)
    summary_df = pl.DataFrame(snapshot_records)
    
    # 落盘全市场大快照
    summary_df.write_parquet(DATA_DIR / "full_market_snapshot.parquet", compression="zstd")
    print(f"\n✅ 五维微积分计算完毕！成功产出 {len(summary_df)} 只标的因子宽表，计算总耗时: {elapsed} 秒！")
    return summary_df


def step3_duckdb_tactical_screening():
    """阶段三：DuckDB 全市场战术扫描"""
    print(f"\n================================================================================")
    print("🔍 [阶段 3/3] 启动 DuckDB 全市场纯 SQL 毫秒级战术穿透扫描")
    print(f"================================================================================")

    con = duckdb.connect()
    snapshot_path = str(DATA_DIR / "full_market_snapshot.parquet")

    # 1. 扫描真空走廊 (获利盘跳升 + 筹码单峰密集)
    sql_vac = f"""
    SELECT code, close, Z_profit, Z_prime, X70, X90, LFS, HCCYF13, BIAS_5_20, order
    FROM read_parquet('{snapshot_path}')
    WHERE (Z_prime > 8.0 OR (Z_profit > 80.0 AND X90 < 15.0))
      AND LFS >= HCCYF13 * 0.8
    ORDER BY Z_profit DESC
    LIMIT 15;
    """
    vac_df = con.execute(sql_vac).pl()
    print("\n🎯 【战术榜单一：全市场物理真空走廊 + 极度单峰 Top 15】")
    print(vac_df)

    # 2. 扫描战略黄金坑 (市场极度深套超卖 CYS34 < -15%)
    sql_pit = f"""
    SELECT code, close, CYS34, Z_profit, LFS, HCCYF13, BIAS_5_20, order
    FROM read_parquet('{snapshot_path}')
    WHERE CYS34 < -15.0
    ORDER BY CYS34 ASC
    LIMIT 15;
    """
    pit_df = con.execute(sql_pit).pl()
    print("\n💎 【战术榜单二：全市场战略级黄金坑逆向超卖 Top 15】")
    print(pit_df)


if __name__ == "__main__":
    stocks = get_all_a_share_symbols()
    print(f"✅ 全市场 A 股目录拉取成功，共计 {len(stocks)} 只有效标的！")
    
    # 默认全量流水线执行 (先执行前 500 只或全量)
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    step1_download_all_a_shares(stocks, max_count=limit)
    step2_compute_all_factors()
    step3_duckdb_tactical_screening()
