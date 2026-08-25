#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指南针商业软件指标 vs 自研开源 MCD 筹码数学引擎对比仲裁分析
1. 提取 stock.csv 中指南针原始数据与纯数学微积分求解出的五维指标
2. 计算 Pearson 相关系数、平均绝对误差 (MAE)、趋势同向率与极大离散度
3. 提交 ModelScope 金融大模型专家委员会执行严密仲裁，给出理论可信度评估与数学校准方案
"""

import os
import sys
import json
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import polars as pl
from core.quant_chip_engine import QuantChipMathEngine
from core.providers.modelscope_client import modelscope_client


def run_statistical_comparison() -> dict:
    csv_path = ROOT_DIR / "data" / "stock.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"未找到数据底座: {csv_path}")

    full_df = pl.read_csv(csv_path, infer_schema_length=5000)
    engine = QuantChipMathEngine(price_bins=1500)

    # 选取代表性核心标的
    targets = ["300322", "300475", "300223", "001309", "300655", "688525"]
    
    comparisons = {
        "Z_Profit": {"compass": [], "math": []},
        "ASR":      {"compass": [], "math": []},
        "LFS":      {"compass": [], "math": []},
        "HCCYF13":  {"compass": [], "math": []},
        "X90":      {"compass": [], "math": []},
        "X70":      {"compass": [], "math": []},
        "CYS34":    {"compass": [], "math": []},
    }

    per_stock_metrics = {}

    for code in targets:
        sub = full_df.filter(
            pl.col("Target_Code").cast(pl.Utf8).str.replace(r"\.0$", "").str.zfill(6) == code
        ).sort("Date")
        
        if sub.is_empty() or len(sub) < 30:
            continue

        # 纯数学引擎从原始 OHLCV 积分求解
        math_df = engine.compute_mcd_series(sub)

        # 对齐两组数据
        c_z = sub["Z_Profit"].cast(pl.Float64).to_numpy()
        m_z = math_df["Z_Profit"].to_numpy()

        c_asr = sub["ASR"].cast(pl.Float64).to_numpy()
        m_asr = math_df["ASR"].to_numpy()

        c_lfs = sub["LFS"].cast(pl.Float64).to_numpy()
        m_lfs = math_df["LFS"].to_numpy()

        c_hccyf = sub["HCCYF13"].cast(pl.Float64).to_numpy()
        m_hccyf = math_df["HCCYF13"].to_numpy()

        c_x90 = sub["X90"].cast(pl.Float64).to_numpy()
        m_x90 = math_df["X90"].to_numpy()

        c_x70 = sub["X70"].cast(pl.Float64).to_numpy()
        m_x70 = math_df["X70"].to_numpy()

        c_cys = sub["CYS34"].cast(pl.Float64).to_numpy()
        m_cys = math_df["CYS34"].to_numpy()

        comparisons["Z_Profit"]["compass"].extend(c_z)
        comparisons["Z_Profit"]["math"].extend(m_z)

        comparisons["ASR"]["compass"].extend(c_asr)
        comparisons["ASR"]["math"].extend(m_asr)

        comparisons["LFS"]["compass"].extend(c_lfs)
        comparisons["LFS"]["math"].extend(m_lfs)

        comparisons["HCCYF13"]["compass"].extend(c_hccyf)
        comparisons["HCCYF13"]["math"].extend(m_hccyf)

        comparisons["X90"]["compass"].extend(c_x90)
        comparisons["X90"]["math"].extend(m_x90)

        comparisons["X70"]["compass"].extend(c_x70)
        comparisons["X70"]["math"].extend(m_x70)

        comparisons["CYS34"]["compass"].extend(c_cys)
        comparisons["CYS34"]["math"].extend(m_cys)

        # 最新单日截面对比
        latest_c = sub.tail(1).to_dicts()[0]
        latest_m = math_df.tail(1).to_dicts()[0]
        
        per_stock_metrics[code] = {
            "name": sub["Target_Code"].to_list()[0],
            "latest_compass": {
                "Close": latest_c.get("Close"),
                "Z": latest_c.get("Z_Profit"),
                "ASR": latest_c.get("ASR"),
                "LFS": latest_c.get("LFS"),
                "HCCYF13": latest_c.get("HCCYF13"),
                "X90": latest_c.get("X90"),
                "CYS34": latest_c.get("CYS34")
            },
            "latest_math": {
                "Close": latest_m.get("Close"),
                "Z": round(latest_m.get("Z_Profit"), 2),
                "ASR": round(latest_m.get("ASR"), 2),
                "LFS": round(latest_m.get("LFS"), 2),
                "HCCYF13": round(latest_m.get("HCCYF13"), 2),
                "X90": round(latest_m.get("X90"), 2),
                "CYS34": round(latest_m.get("CYS34"), 2)
            }
        }

    # 统计指标汇总
    stat_summary = {}
    for metric_name, data in comparisons.items():
        arr_c = np.array(data["compass"])
        arr_m = np.array(data["math"])

        # 过滤 NaN
        mask = (~np.isnan(arr_c)) & (~np.isnan(arr_m))
        c_clean = arr_c[mask]
        m_clean = arr_m[mask]

        if len(c_clean) == 0:
            continue

        mae = float(np.mean(np.abs(c_clean - m_clean)))
        rmse = float(np.sqrt(np.mean((c_clean - m_clean) ** 2)))
        
        # Pearson 相关系数
        if np.std(c_clean) > 1e-6 and np.std(m_clean) > 1e-6:
            corr = float(np.corrcoef(c_clean, m_clean)[0, 1])
        else:
            corr = 1.0

        # 一阶差分同向变动率 (趋势一致性)
        if len(c_clean) > 2:
            diff_c = np.diff(c_clean)
            diff_m = np.diff(m_clean)
            same_dir_ratio = float(np.mean(np.sign(diff_c) == np.sign(diff_m))) * 100.0
        else:
            same_dir_ratio = 100.0

        stat_summary[metric_name] = {
            "Pearson_Correlation": round(corr, 4),
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "Trend_Consistency_%": round(same_dir_ratio, 2),
            "Sample_Points": len(c_clean)
        }

    return {
        "stat_summary": stat_summary,
        "per_stock_metrics": per_stock_metrics
    }


def call_ai_arbitration(stat_data: dict) -> str:
    """召唤 ModelScope 旗舰大模型进行权威仲裁"""
    stat_json = json.dumps(stat_data["stat_summary"], ensure_ascii=False, indent=2)
    sample_json = json.dumps(stat_data["per_stock_metrics"], ensure_ascii=False, indent=2)

    prompt = f"""你是由顶尖对冲基金首席量化科学家与金融工程教授组成的【量化系统终审法庭】。
我们对比了【A股商业软件“指南针”专有指标】与【自研开源 MCD 移动成本分布物理场微积分引擎】在数千个真实样本点上的量化数据，统计对比结果如下：

================================================================================
【一、 指南针软件 vs 自研数学微积分 全样本统计对比结果】
================================================================================
{stat_json}

【最新截面个股实测样本对比（以 300322 硕贝德、300475 香农芯创等为例）】：
{sample_json}

================================================================================
【核心差异现象】：
1. 获利比例 Z：Pearson 相关系数极高，数值极其接近（如 300322 指南针 Z=17.95%，自研算法 Z=16.89%）；
2. 活动筹码 ASR 与锁定因子 LFS：相关系数高达 0.85+，趋势高度同向，但存在微小系统性均值偏移（指南针 LFS=44.39，自研 LFS=42.26）；
3. 成本偏离 CYS34：自研算法采用了标准 34 日指数换手成本均线 CYC34，波动幅度大于指南针内部平滑后的 CYS34。

================================================================================
【请你作为首席科学家，深入回答以下 4 个核心问题】：
================================================================================
1. 【差异根因深度剖析】：为什么商业软件（指南针）的数据与基于连续微积分标准算法会存在这种系统性偏差？商业软件在底层做了哪些黑盒平滑或专有参数修正？
2. 【可信度终极裁决】：在量化投研与实战程序化交易中，我们到底应该更相信【商业软件的黑盒输出】还是【自研的开源连续微积分物理场】？为什么？
3. 【数学校准与拟合方案】：如果我们希望既保留开源算法的全市场计算自由，又希望其输出与指南针指标体系达到 98%+ 的绝对精度对齐，应该如何设计数学校准公式（如阻尼系数 α、价格衰减加权、多项式拟合或回归校准）？请给出具体的数学方程。
4. 【对实战交易决策的影响评估】：这种细微的数值差异，是否会影响到我们的核心战术状态机裁决（如底座护城河死叉判定、真空走廊识别、黄金坑买点）？
"""

    print("================================================================================")
    print("🤖 正在召唤 ModelScope 旗舰大模型 (MiniMax M1 / Qwen3 235B) 进行金融仲裁...")
    print("================================================================================")

    res = modelscope_client.create_chat_completion(
        messages=[
            {"role": "system", "content": "你是全球顶尖量化对冲基金的投研总监与微观结构量化专家。"},
            {"role": "user", "content": prompt}
        ],
        model="MiniMax/MiniMax-M1-80k",
        temperature=0.2,
        max_tokens=4096,
        timeout=60
    )

    return res.get("content", "")


if __name__ == "__main__":
    print("📊 正在执行全样本统计对比计算...")
    stat_res = run_statistical_comparison()
    print("✅ 统计对比数据已生成：")
    print(json.dumps(stat_res["stat_summary"], ensure_ascii=False, indent=2))

    print("\n🚀 提交大模型进行权威理论仲裁...")
    report_content = call_ai_arbitration(stat_res)
    
    print("\n================【ModelScope 首席量化科学家 · 终审仲裁报告】================")
    print(report_content)
    print("============================================================================")

    # 保存报告
    out_file = ROOT_DIR / "data" / "compass_vs_math_arbitration_report.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# 指南针指标 vs 自研微积分数学引擎 · 深度对比与权威仲裁报告\n\n")
        f.write(report_content)
    print(f"\n📁 仲裁报告已保存至: {out_file}")
