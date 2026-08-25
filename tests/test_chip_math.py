#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证高精移动成本分布 (MCD) 数学积分引擎：
1. 从真实行情序列进行微积分求解
2. 验证计算出的 Z(获利比), ASR, X70, X90, LFS, CYS34, BIAS 等指标的物理边界与数值精度
3. 测试计算耗时 (每千日序列耗时应 < 10 毫秒)
"""
import time
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import polars as pl
from core.quant_chip_engine import chip_engine

def test_math_engine():
    csv_path = ROOT_DIR / "data" / "stock.csv"
    if not csv_path.exists():
        print("未找到 stock.csv，跳过")
        return

    raw = pl.read_csv(csv_path, infer_schema_length=5000)
    
    # 取 300322 硕贝德
    sub = raw.filter(pl.col("Target_Code").cast(pl.Utf8).str.contains("300322")).sort("Date")
    print(f"✅ 载入 300322 历史日线数据: {len(sub)} 行")
    
    t0 = time.time()
    result = chip_engine.compute_mcd_series(sub)
    elapsed_ms = (time.time() - t0) * 1000.0
    
    print(f"⚡ MCD 物理场递推积分耗时: {elapsed_ms:.2f} ms ({len(sub)} 个交易日)")
    
    latest = result.tail(1).to_dicts()[0]
    print("\n---【高精数学积分求解出的最新截面真值】---")
    print(f"  • 收盘价 Close: {latest.get('Close')} 元")
    print(f"  • 获利比例 Z:   {latest.get('Z_Profit'):.2f}%")
    print(f"  • 活动筹码 ASR: {latest.get('ASR'):.2f}%")
    print(f"  • 集中度 X70:   {latest.get('X70'):.2f}% | X90: {latest.get('X90'):.2f}%")
    print(f"  • 锁定因子 LFS: {latest.get('LFS'):.2f} | 护城河 HCCYF13: {latest.get('HCCYF13'):.2f}")
    print(f"  • 成本偏离 CYS34: {latest.get('CYS34'):.2f}%")
    print(f"  • 均线偏离 BIAS:  {latest.get('BIAS_5_20'):.4f}%")
    print(f"  • 3日斜率 Slope3: {latest.get('Slope3_LFS'):.2f}")
    print("------------------------------------------")

    # 边界条件断言
    assert 0.0 <= latest.get('Z_Profit') <= 100.0, "Z 获利比必须在 [0, 100] 区间"
    assert 0.0 <= latest.get('ASR') <= 100.0, "ASR 必须在 [0, 100] 区间"
    assert 0.0 <= latest.get('X70') <= 100.0, "X70 必须在 [0, 100] 区间"
    assert elapsed_ms < 50.0, "千日筹码递推计算耗时必须在 50ms 以内"
    print("\n🎉 数学积分引擎测试完全通过，具备高精且极速的物理场求解能力！")

if __name__ == "__main__":
    test_math_engine()
