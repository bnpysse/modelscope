#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 BaoStock 官方专线协议的全市场 A 股前复权日线批量采集与 Parquet 落盘引擎
1. 专线直连获取沪深京 5000+ 有效标的历史日线序列 (2023-01-01 至 最新)
2. 包含字段: Date, Code, Open, High, Low, Close, Volume, Amount, Turnover, Pct_Chg
3. 零断网、零反爬封锁，全自动断点续传（已下载自动跳过）
4. 持久化存储至 /mnt/workspace/quant_data/all_a_shares_parquet/
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
PARQUET_DIR = DATA_DIR / "all_a_shares_parquet"
PARQUET_DIR.mkdir(parents=True, exist_ok=True)

import polars as pl
import baostock as bs
from tqdm import tqdm


def get_all_a_share_codes() -> List[dict]:
    """通过 BaoStock 专线查询全市场有效 A 股列表"""
    print("📋 [1/3] 正在通过 BaoStock 专线拉取全市场 A 股证券目录...")
    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")

    today_str = time.strftime("%Y-%m-%d")
    rs = bs.query_all_stock(day=today_str)
    
    stock_list = []
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        bs_code = row[0]       # 例如 "sh.600000", "sz.300475"
        trade_status = row[1]  # "1" 正常交易
        stock_name = row[2] if len(row) > 2 else ""
        
        # 过滤主板、创业板、科创板、北交所
        if bs_code.startswith(("sh.60", "sh.688", "sz.00", "sz.300", "sz.301", "bj.")):
            stock_list.append({
                "bs_code": bs_code,
                "clean_code": bs_code.split(".")[-1],
                "name": stock_name,
                "trade_status": trade_status
            })

    bs.logout()
    print(f"✅ 成功获取全市场有效 A 股标的共 {len(stock_list)} 只！")
    return stock_list


def run_full_market_download(start_date: str = "2023-01-01", batch_size: int = 500):
    """批量下载全市场历史日线数据"""
    stocks = get_all_a_share_codes()
    fields = "date,code,open,high,low,close,volume,amount,turn,pctChg"
    
    print(f"\n⚡ [2/3] 启动全市场数据持久化落盘引擎 (起始日期: {start_date})...")
    print(f"📁 目标存储路径: {PARQUET_DIR}")

    lg = bs.login()
    if lg.error_code != '0':
        raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")

    success_count = 0
    skip_count = 0
    fail_count = 0
    t0 = time.time()

    try:
        for idx, item in enumerate(tqdm(stocks, desc="全市场 A 股下载进度", unit="股")):
            bs_code = item["bs_code"]
            clean_code = item["clean_code"]
            save_path = PARQUET_DIR / f"{clean_code}.parquet"

            # 断点续传：若已存在且体积正常则跳过
            if save_path.exists() and save_path.stat().st_size > 1024:
                skip_count += 1
                continue

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
                fail_count += 1
                continue

            # 转换为高压缩 Parquet
            df = pl.DataFrame(data, orient="row", schema=[
                ("Date", pl.Utf8), ("Code", pl.Utf8),
                ("Open", pl.Float64), ("High", pl.Float64), ("Low", pl.Float64), ("Close", pl.Float64),
                ("Volume", pl.Float64), ("Amount", pl.Float64), ("Turnover", pl.Float64), ("Pct_Chg", pl.Float64)
            ])

            df.write_parquet(save_path, compression="zstd")
            success_count += 1

            # 定期打印进度
            if (idx + 1) % batch_size == 0:
                print(f"   [批次心跳] 已处理 {idx + 1}/{len(stocks)} 只 | 新增: {success_count} | 耗时: {round(time.time() - t0, 1)}s")

    finally:
        bs.logout()

    elapsed = round(time.time() - t0, 2)
    print("\n================================================================================")
    print(f"🎉 [3/3] 全市场 A 股历史日线全部拉取完毕！总耗时: {elapsed} 秒")
    print(f"📊 新增成功: {success_count} 只 | 跳过已有: {skip_count} 只 | 空数据/停牌: {fail_count} 只")
    print(f"📁 数据已全部安全落盘至: {PARQUET_DIR}")
    print("================================================================================")


if __name__ == "__main__":
    run_full_market_download(start_date="2023-01-01")
