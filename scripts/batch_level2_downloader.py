#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场 A 股 Level-2 逐笔订单流高频数据批量采集与微观结构特征萃取引擎
1. 循环遍历沪深京 5115+ 标的单日逐笔成交明细 (带主动买/卖/中性盘属性)
2. 通过 Level2TickEngine 实时提炼高频主动买盘占比 (ABR)、推升效率 (eta_micro)、主力大单净额
3. 压缩持久化存储至 /mnt/workspace/quant_data/level2_ticks/ 与 level2_features.parquet
"""

import os
import sys
import time
from pathlib import Path
from typing import List

# 避开本地代理对国内行情 API 的拦截
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

if os.path.exists("/mnt/workspace"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = WORKSPACE_DIR / "quant_data"
L2_DIR = DATA_DIR / "level2_ticks"
L2_DIR.mkdir(parents=True, exist_ok=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import polars as pl
import baostock as bs
from tqdm import tqdm
from core.level2_tick_engine import level2_engine


def get_all_stock_codes() -> List[str]:
    """获取全市场股票代码列表"""
    # 优先从已有的 all_a_shares_parquet 目录中快速获取
    parquet_dir = DATA_DIR / "all_a_shares_parquet"
    if parquet_dir.exists():
        files = list(parquet_dir.glob("*.parquet"))
        if files:
            return sorted([f.stem for f in files])
    
    # 备选通过 BaoStock 查询
    lg = bs.login()
    stock_list = []
    try:
        today_str = time.strftime("%Y-%m-%d")
        rs = bs.query_all_stock(day=today_str)
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            code = row[0].split(".")[-1]
            if len(code) == 6:
                stock_list.append(code)
    finally:
        bs.logout()
    return stock_list


def run_batch_level2_ingest(batch_size: int = 200):
    print("================================================================================")
    print("🌊 [Level-2 全市场逐笔订单流引擎] 批量采集与微观结构萃取启动")
    print(f"📁 存储持久化路径: {L2_DIR}")
    print("================================================================================")

    stocks = get_all_stock_codes()
    print(f"📊 待处理标的总量: {len(stocks)} 只")

    feature_records = []
    success = 0
    skip = 0
    fail = 0
    t0 = time.time()

    for idx, code in enumerate(tqdm(stocks, desc="Level-2 逐笔订单流采集", unit="股")):
        save_file = L2_DIR / f"{code}_level2.parquet"
        
        # 断点续传：若已存在则直接读取特征
        if save_file.exists() and save_file.stat().st_size > 1024:
            skip += 1
            continue

        try:
            # 拉取单只标的单日全量逐笔明细 (带主动买卖属性)
            df_tick = level2_engine.fetch_stock_tick_series(code)
            if df_tick is None or df_tick.is_empty():
                fail += 1
                continue

            # 落盘逐笔明细 Parquet
            df_tick.write_parquet(save_file, compression="zstd")

            # 萃取 Level-2 微观特征
            features = level2_engine.compute_level2_micro_features(df_tick)
            features["code"] = code
            features["date"] = time.strftime("%Y-%m-%d")
            feature_records.append(features)
            success += 1

            if (idx + 1) % 50 == 0:
                print(f"   [Level-2 进度] {idx+1}/{len(stocks)} | 成功: {success} | 耗时: {round(time.time()-t0, 1)}s")

            # 避免触发远程高频频控，微休眠
            time.sleep(0.05)

        except Exception:
            fail += 1
            continue

    # 保存特征汇总表
    if feature_records:
        feat_df = pl.DataFrame(feature_records)
        feat_df.write_parquet(DATA_DIR / "level2_features.parquet", compression="zstd")

    elapsed = round(time.time() - t0, 1)
    print("\n================================================================================")
    print(f"🎉 Level-2 逐笔订单流采集完毕！耗时: {elapsed} 秒")
    print(f"📊 成功: {success} | 跳过: {skip} | 失败/停牌: {fail}")
    print("================================================================================")


if __name__ == "__main__":
    run_batch_level2_ingest()
