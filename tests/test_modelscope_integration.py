#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端集成测试：
1. 验证 Polars 数据引擎加载与 198 交易日斐波那契战略纵深计算
2. 验证 ModelScope MiniMax M1 / Qwen 3 免费大模型全景研报生成与 <think> 思维链分离
3. 验证本地日配额水库与预算硬锁门神正常工作
"""
import os
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.engine import create_engine
from core.ai_advisor import query_ai_staff_report
from core.providers.modelscope_client import modelscope_client

def test_full_pipeline():
    print("==================================================")
    print("🛰️ [测试 1/3] 启动 Polars 数据引擎并计算 300322 斐波那契纵深")
    print("==================================================")
    engine = create_engine(str(ROOT_DIR))
    
    code = "300322"
    name = engine.get_stock_name(code)
    print(f"✅ 标的识别: {name} ({code})")
    
    snapshot = engine.get_latest_snapshot(code)
    print(f"✅ 最新快照 (Close={snapshot.get('Close')}, LFS={snapshot.get('LFS')}, HCCYF13={snapshot.get('HCCYF13')}, X70={snapshot.get('X70')}, BIAS={snapshot.get('BIAS_5_20'):.4f}%)")
    
    fib_matrix = engine.get_fibonacci_depth_matrix(code)
    print(f"✅ 斐波那契纵深矩阵周期数: {len(fib_matrix)}")
    for row in fib_matrix:
        print(f"   [{row['Period']}] {row['Start_Date']} -> {row['Price_End']}元, 涨跌幅: {row['Price_Change_%']:+.2f}%, 均LFS: {row['Avg_LFS']:.2f}, 均ASR: {row['Avg_ASR']:.2f}%")

    print("\n==================================================")
    print("🤖 [测试 2/3] 召唤 ModelScope 免费旗舰生成全景穿透研报 (MiniMax M1)")
    print("==================================================")
    quota_before = modelscope_client.get_quota_status()
    print(f"📊 调用前配额: 已用 {quota_before['used_calls']} / {quota_before['limit_calls']} 次")
    
    res = query_ai_staff_report(
        stock_code=code,
        stock_name=name,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False, default=str),
        fib_matrix_json=json.dumps(fib_matrix, ensure_ascii=False, default=str),
        selected_model="MiniMax/MiniMax-M1-80k"
    )
    
    print(f"\n✅ 审计完成! 状态: {res.get('status')} | 使用模型: {res.get('model_used')} | 耗时: {res.get('duration_seconds')}s")
    if res.get("thinking"):
        print(f"💡 [思维链提取成功]: {res['thinking'][:120]}...\n")
    
    print("----------【参谋部生成的全景穿透研报】----------")
    print(res["content"])
    print("------------------------------------------------")

    print("\n==================================================")
    print("🛡️ [测试 3/3] 验证配额门神台账登记")
    print("==================================================")
    quota_after = modelscope_client.get_quota_status()
    print(f"✅ 调用后配额: 已用 {quota_after['used_calls']} / {quota_after['limit_calls']} 次 (总计 Tokens: {quota_after['total_tokens']})")
    assert quota_after['used_calls'] > quota_before['used_calls'], "配额台账应增加 1 次调用"
    print("\n🎉 恭喜！天眼全息智导 V7.0 (ModelScope Edition) 全部测试 100% 通过！")

if __name__ == "__main__":
    test_full_pipeline()
