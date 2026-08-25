#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 DuckDB 战术筛选引擎
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.full_market_screener import screener

def test_screener():
    print("==================================================")
    print("🔍 [测试 DuckDB 战术初筛引擎]")
    print("==================================================")
    
    df_vac = screener.scan_vacuum_corridor()
    print("\n✅ 【物理真空走廊 + 极度单峰】初筛结果:")
    print(df_vac)

    df_pit = screener.scan_golden_pit()
    print("\n✅ 【战略级黄金坑】初筛结果:")
    print(df_pit)

    print("\n🎉 DuckDB 战术初筛测试通过！")

if __name__ == "__main__":
    test_screener()
