#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证实证后验三角交叉验证与 ModelScope 大模型智能仲裁机制
1. 从 stock.csv 提取真实历史交易数据与未来 5 日走势
2. 统计【指南针赢】vs【自研数学微积分赢】的真实胜率分布
3. 选取典型背离案例调用 ModelScope 旗舰大模型进行归因与校准裁决
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import polars as pl
from core.quant_chip_engine import chip_engine
from core.empirical_arbitrator import arbitrator


def run_empirical_test():
    csv_path = ROOT_DIR / "data" / "stock.csv"
    full_df = pl.read_csv(csv_path, infer_schema_length=5000)

    print("================================================================================")
    print("🔬 [实证后验三角交叉检验] 正在扫描全历史数据中指南针 vs 自研微积分的信号背离点...")
    print("================================================================================")

    targets = ["300322", "300475", "300223", "001309", "300655", "688525"]
    all_divergence_events = []

    compass_wins = 0
    math_wins = 0
    both_equal = 0

    for code in targets:
        sub = full_df.filter(
            pl.col("Target_Code").cast(pl.Utf8).str.replace(r"\.0$", "").str.zfill(6) == code
        ).sort("Date")

        if len(sub) < 30:
            continue

        # 运行自研微积分
        math_df = chip_engine.compute_mcd_series(sub)

        # 合并两组数据
        merged = sub.with_columns([
            math_df["LFS"].alias("LFS_Math"),
            math_df["HCCYF13"].alias("HCCYF13_Math"),
            math_df["Z_Profit"].alias("Z_Math")
        ])

        events = arbitrator.detect_divergence_events(merged, code)
        all_divergence_events.extend(events)

        for ev in events:
            if ev["empirical_winner"] == "COMPASS_WIN":
                compass_wins += 1
            elif ev["empirical_winner"] == "MATH_WIN":
                math_wins += 1
            else:
                both_equal += 1

    total_events = len(all_divergence_events)
    print(f"\n📊 【实证后验统计结果】（共检测到 {total_events} 次关键背离检验日）：")
    print(f"  • 自研微积分预测胜出 (MATH_WIN):    {math_wins} 次 (占比: {round(math_wins/max(1, total_events)*100, 1)}%)")
    print(f"  • 指南针商业软件胜出 (COMPASS_WIN): {compass_wins} 次 (占比: {round(compass_wins/max(1, total_events)*100, 1)}%)")
    print(f"  • 双方平局或走平 (BOTH_EQUAL):      {both_equal} 次 (占比: {round(both_equal/max(1, total_events)*100, 1)}%)")

    # 选取一个最具代表性的【自研数学胜出 / 指南针失真误判】案例提交 ModelScope 进行智能仲裁
    case_candidates = [e for e in all_divergence_events if e["empirical_winner"] == "MATH_WIN"]
    if not case_candidates:
        case_candidates = all_divergence_events

    selected_case = case_candidates[0]
    print(f"\n🔍 选取典型背离案例：标的 {selected_case['code']} 在 {selected_case['date']} 的变盘节点")
    print(json.dumps(selected_case, ensure_ascii=False, indent=2))

    print("\n🤖 正在召唤 ModelScope 旗舰大模型执行智能归因与校准裁决...")
    report = arbitrator.arbitrate_with_modelscope(selected_case)
    
    print("\n================【ModelScope 智能仲裁法庭裁决】================")
    print(report)
    print("================================================================")


if __name__ == "__main__":
    run_empirical_test()
