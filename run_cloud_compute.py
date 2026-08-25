#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelScope 云端高吞吐数学计算主脚本 (专为 PAI-DSW 免费实例设计)
1. 自动适配 /mnt/workspace 持久化存储，机器自动休眠后重启进度不丢
2. 支持输入任意 A 股代码在线拉取历史行情或读取本地底座
3. 执行高精 MCD 筹码物理场时间步进积分，产出一手高精五维量化因子库
4. 生成 DuckDB 极速分析宽表与当日战术扫描军令快照
"""

import os
import sys
import time
import json
from pathlib import Path

# 避开本地代理对国内行情 API 的拦截
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# 自动适配云端 /mnt/workspace 或本地目录
if os.path.exists("/mnt/workspace"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent

DATA_DIR = WORKSPACE_DIR / "quant_data"
PARQUET_DIR = DATA_DIR / "daily_parquet"
FACTORS_DIR = DATA_DIR / "factors"
PARQUET_DIR.mkdir(parents=True, exist_ok=True)
FACTORS_DIR.mkdir(parents=True, exist_ok=True)

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import polars as pl
from core.quant_chip_engine import chip_engine
from core.ai_advisor import evaluate_local_tactical_status

def get_all_target_pool() -> list[dict]:
    """动态获取全部监控标的池 (结合核心资产与 stock.csv 底座)"""
    pool = [
        {"code": "300475", "name": "香农芯创", "sector": "HBM存储分销+先进封测"},
        {"code": "300223", "name": "北京君正", "sector": "车规工控DRAM自研存算"},
        {"code": "300322", "name": "硕贝德",   "sector": "天线射频·死锁资产"},
        {"code": "001309", "name": "德明利",   "sector": "企业级存储主控模组"},
        {"code": "300655", "name": "晶瑞电材", "sector": "半导体光刻胶与湿电子化学品"},
        {"code": "688525", "name": "佰维存储", "sector": "嵌入式存储与封测龙头"},
    ]
    seen = {item["code"] for item in pool}
    
    local_csv = ROOT_DIR / "data" / "stock.csv"
    if local_csv.exists():
        try:
            df = pl.read_csv(local_csv, infer_schema_length=2000)
            code_col = "Target_Code" if "Target_Code" in df.columns else "Code"
            name_col = "Target_Name" if "Target_Name" in df.columns else "Name"
            
            rows = df.select([code_col, name_col]).unique().to_dicts()
            for r in rows:
                c = str(r[code_col]).replace(".0", "").zfill(6)
                n = str(r.get(name_col, c))
                if c not in seen:
                    pool.append({"code": c, "name": n, "sector": "核心观察标的"})
                    seen.add(c)
        except Exception:
            pass
    return pool


def fetch_or_load_stock_history(code: str, force_refresh: bool = False) -> pl.DataFrame:
    """获取标的历史日线序列 (优先读本地 Parquet 缓存，无则从本地底座/在线获取)"""
    clean_code = str(code).replace(".0", "").zfill(6)
    parquet_path = PARQUET_DIR / f"{clean_code}.parquet"

    if parquet_path.exists() and not force_refresh:
        return pl.read_parquet(parquet_path)

    # 1. 优先从本地 stock.csv / stock_clean.csv 中高效抽取
    for candidate_name in ["stock.csv", "stock_clean.csv"]:
        local_csv = ROOT_DIR / "data" / candidate_name
        if local_csv.exists():
            try:
                full_df = pl.read_csv(local_csv, infer_schema_length=5000)
                code_col = "Target_Code" if "Target_Code" in full_df.columns else "Code"
                sub = full_df.filter(
                    pl.col(code_col).cast(pl.Utf8).str.replace(r"\.0$", "").str.zfill(6) == clean_code
                ).sort("Date")
                if not sub.is_empty():
                    sub.write_parquet(parquet_path, compression="zstd")
                    return sub
            except Exception:
                pass

    # 2. 本地无则通过 AkShare 在线获取
    print(f"🌐 [数据源在线拉取] 正在获取标的 {clean_code} 的全量前复权历史日线...")
    try:
        import akshare as ak
        raw_df = ak.stock_zh_a_hist(symbol=clean_code, period="daily", start_date="20240101", adjust="qfq")
        if not raw_df.empty:
            pdf = pl.from_pandas(raw_df.rename(columns={
                "日期": "Date", "开盘": "Open", "最高": "High", "最低": "Low",
                "收盘": "Close", "换手率": "Turnover", "成交量": "Volume", "涨跌幅": "Pct_Chg"
            }))
            pdf.write_parquet(parquet_path, compression="zstd")
            return pdf
    except Exception as e:
        print(f"⚠️ 在线获取失败 ({e})")

    raise RuntimeError(f"无法获取标的 {clean_code} 的历史数据。")


def run_full_market_math_pipeline():
    print("================================================================================")
    print("🚀 [天眼全息智导 V7.0] ModelScope 云端五维筹码物理场数学计算引擎启动")
    print(f"📁 工作持久化目录: {WORKSPACE_DIR}")
    print("================================================================================")

    summary_records = []
    t_start = time.time()

    targets = get_all_target_pool()
    print(f"📊 监控标的池总量: {len(targets)} 只标的")
    for item in targets:
        code = item["code"]
        name = item["name"]
        sector = item["sector"]

        t0 = time.time()
        # 1. 提取一手原始日线
        df_raw = fetch_or_load_stock_history(code)
        
        # 2. 执行高精 MCD 筹码物理场微积分递推
        df_factors = chip_engine.compute_mcd_series(df_raw)
        
        # 3. 将衍生全量因子落盘至 /mnt/workspace/quant_data/factors/
        clean_code = str(code).zfill(6)
        factor_file = FACTORS_DIR / f"{clean_code}_factors.parquet"
        df_factors.write_parquet(factor_file, compression="zstd")

        # 4. 提取最新截面真值
        latest = df_factors.tail(1).to_dicts()[0]
        local_eval = evaluate_local_tactical_status(latest)
        
        calc_ms = (time.time() - t0) * 1000.0

        summary_records.append({
            "code": clean_code,
            "name": name,
            "sector": sector,
            "close": float(latest.get("Close", 0.0)),
            "Z_profit": round(float(latest.get("Z_Profit", 0.0)), 2),
            "ASR": round(float(latest.get("ASR", 0.0)), 2),
            "X70": round(float(latest.get("X70", 0.0)), 2),
            "X90": round(float(latest.get("X90", 0.0)), 2),
            "LFS": round(float(latest.get("LFS", 0.0)), 2),
            "HCCYF13": round(float(latest.get("HCCYF13", 0.0)), 2),
            "Scissor": round(float(latest.get("Scissor", 0.0)), 2),
            "CYS34": round(float(latest.get("CYS34", 0.0)), 2),
            "BIAS_5_20": round(float(latest.get("BIAS_5_20", 0.0)), 4),
            "order": local_eval["order"],
            "status_title": local_eval["status_title"],
            "calc_time_ms": round(calc_ms, 2)
        })

    total_time = round(time.time() - t_start, 2)

    # 5. 汇总为全市场快照宽表并持久化
    summary_df = pl.DataFrame(summary_records)
    summary_df.write_parquet(DATA_DIR / "latest_factor_snapshot.parquet")
    
    with open(DATA_DIR / "latest_factor_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(summary_records, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 全量计算完毕！总耗时: {total_time}s，生成因子宽表如下：\n")
    print(summary_df.select([
        "code", "name", "close", "Z_profit", "ASR", "X70", "LFS", "Scissor", "BIAS_5_20", "order"
    ]))

    print("\n================================================================================")
    print("🛡️ [断点续算状态] 所有计算数据已持久化至 /mnt/workspace/quant_data/，即使机器休眠重启亦无损！")
    print("================================================================================")


if __name__ == "__main__":
    run_full_market_math_pipeline()
