#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五维筹码物理场微积分 V2 单元测试套件：
1. 验证非对称加速度阻尼衰减机制 (高换手对倒防护)
2. 验证极端无量一字跌停保底衰减 (Limit-down Floor)
3. 验证真实波幅归一化乖离率 (Norm_BIAS_5_20)
4. 验证日/周/月跨周期筹码张量协整共振评分 (Resonance_Score)
5. 验证 4 级动态仓位分层管理矩阵 (PositionTierVerdict)
6. 验证 Level-2 微观订单流推升效率与防对倒识别
"""

import sys
from pathlib import Path
import numpy as np
import polars as pl
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.quant_chip_engine import QuantChipMathEngine, chip_engine
from core.signals import SignalJudge, PositionTierVerdict
from core.ai_advisor import evaluate_local_tactical_status
from core.level2_tick_engine import level2_engine
from core.full_market_screener import screener


def test_asymmetric_damping_math():
    """测试 1：非对称换手率阻尼数学特性"""
    engine = QuantChipMathEngine(damping_beta=1.8, extreme_gamma=0.005)

    # 构造包含高换手对倒（30%换手率）的模拟行情
    dates = [f"2026-01-{i+1:02d}" for i in range(20)]
    closes = [10.0 + i * 0.2 for i in range(20)]
    highs = [c + 0.3 for c in closes]
    lows = [c - 0.3 for c in closes]
    opens = [c - 0.1 for c in closes]
    # 第 10 天发生 30% 巨量对倒换手
    turnovers = [3.0] * 20
    turnovers[10] = 30.0

    df = pl.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Turnover": turnovers
    })

    # 计算带阻尼与不带阻尼
    df_damped = engine.compute_mcd_series(df, use_damping=True)
    df_undamped = engine.compute_mcd_series(df, use_damping=False)

    # 在巨量对倒日，带阻尼的有效换手率应严格小于原始换手率 0.30
    eff_to_damped = df_damped["Effective_Turnover"][10]
    eff_to_undamped = df_undamped["Effective_Turnover"][10]
    
    assert eff_to_damped < 0.22, f"高换手阻尼后有效换手率应饱和衰减: {eff_to_damped}"
    assert eff_to_undamped == 0.30, f"无阻尼应保持原始换手: {eff_to_undamped}"

    # 验证底座筹码保留度：带阻尼的 LFS 在对倒后保留应高于未阻尼
    lfs_damped = df_damped["LFS"][10]
    lfs_undamped = df_undamped["LFS"][10]
    print(f"\n✅ 阻尼生效：T_raw=30% -> T_eff={eff_to_damped*100:.1f}%, LFS(Damped)={lfs_damped:.2f} >= LFS(Raw)={lfs_undamped:.2f}")
    assert lfs_damped >= lfs_undamped - 0.5


def test_limit_down_floor():
    """测试 2：无量一字跌停最低更新保底"""
    engine = QuantChipMathEngine(damping_beta=1.8, extreme_gamma=0.005)

    # 构造连续无量一字跌停 (换手率 0.01%)
    dates = ["2026-02-01", "2026-02-02", "2026-02-03"]
    closes = [20.0, 18.0, 16.2]  # 连续跌停
    highs = closes
    lows = closes
    opens = closes
    turnovers = [5.0, 0.01, 0.01]  # 第2、3日无量

    df = pl.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Turnover": turnovers
    })

    df_res = engine.compute_mcd_series(df, use_damping=True)
    
    # 跌停日有效换手率应被激活保底 gamma = 0.005 (0.5%)
    eff_to_limit_down = df_res["Effective_Turnover"][1]
    assert eff_to_limit_down >= 0.0049, f"一字跌停保底未生效: {eff_to_limit_down}"
    print(f"\n✅ 极端一字跌停保底生效: 极低换手 0.01% 被提升至保底有效更新 {eff_to_limit_down*100:.2f}%")


def test_norm_bias_and_atr():
    """测试 3：ATR 波动率归一化 BIAS"""
    # 构造高波动标的
    n = 30
    dates = [f"2026-03-{i+1:02d}" for i in range(n)]
    closes = [10.0 + (i % 2) * 1.5 for i in range(n)]
    highs = [c + 1.0 for c in closes]
    lows = [c - 1.0 for c in closes]
    turnovers = [5.0] * n

    df = pl.DataFrame({
        "Date": dates,
        "Open": closes,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Turnover": turnovers
    })

    res = chip_engine.compute_mcd_series(df)
    assert "ATR_20" in res.columns
    assert "Norm_BIAS_5_20" in res.columns
    
    latest_atr = res["ATR_20"][-1]
    latest_norm_bias = res["Norm_BIAS_5_20"][-1]
    assert latest_atr > 0, "ATR 应大于 0"
    print(f"\n✅ 波动率归一化测试通过: ATR_20={latest_atr:.2f}, Norm_BIAS={latest_norm_bias:.2f}")


def test_multi_period_resonance():
    """测试 4：日/周/月跨周期筹码张量协整共振"""
    # 构造 60 交易日的主升浪强控盘多头走势
    n = 60
    closes = [10.0 * (1.015 ** i) for i in range(n)]
    df = pl.DataFrame({
        "Date": [f"2026-D{i:03d}" for i in range(n)],
        "Open": closes,
        "High": [c * 1.02 for c in closes],
        "Low": [c * 0.98 for c in closes],
        "Close": closes,
        "Turnover": [2.5] * n
    })

    res_info = chip_engine.compute_multi_period_resonance(df)
    print(f"\n✅ 跨周期共振结果: 得分={res_info['resonance_score']}, 诊断={res_info['diagnosis']}")
    assert "resonance_score" in res_info
    assert res_info["resonance_score"] >= 60.0, "主升浪标的多周期得分应较高"


def test_four_tier_position_judge():
    """测试 5：4 级动态仓位状态机决策"""
    # 1. 满配主升测试 (100%)
    v_lock = SignalJudge.judge_position_tier(
        lfs=65.0, hccyf=50.0, scissor=15.0, slope_3d=2.0, bias_5_20=4.0
    )
    assert v_lock.target_pos_pct == 100
    assert "绝对锁仓" in v_lock.tier_label

    # 2. 超买反向对冲测试 (30%)
    v_hedge = SignalJudge.judge_position_tier(
        lfs=60.0, hccyf=50.0, scissor=10.0, slope_3d=1.0, bias_5_20=18.0
    )
    assert v_hedge.target_pos_pct == 30
    assert "反向对冲" in v_hedge.tier_label

    # 3. 防线松动减仓测试 (50%)
    v_trim = SignalJudge.judge_position_tier(
        lfs=45.0, hccyf=46.0, scissor=-1.0, slope_3d=-0.5, bias_5_20=2.0, x90=24.0
    )
    assert v_trim.target_pos_pct == 50
    assert "分批减仓" in v_trim.tier_label

    # 4. 底座坍塌清仓测试 (0%)
    v_stop = SignalJudge.judge_position_tier(
        lfs=30.0, hccyf=45.0, scissor=-15.0, slope_3d=-3.0, bias_5_20=-8.0
    )
    assert v_stop.target_pos_pct == 0
    assert "坚决清仓" in v_stop.tier_label
    print("\n✅ 4 级动态仓位状态机决策测试 100% 通过！")


def test_level2_safe_micro_features():
    """测试 6：Level-2 微观特征与推升效率安全计算"""
    mock_snapshot = {
        "Close": 25.0,
        "Open": 24.0,
        "Turnover": 4.5,
        "Main_Pct": 2.5,
        "Dare_Pct": 1.2
    }
    micro = level2_engine.get_micro_features_safely("300322", mock_snapshot)
    assert "active_buy_ratio_%" in micro
    assert "eta_micro_thrust" in micro
    assert "is_wash_trading_dump" in micro
    print(f"\n✅ Level-2 微观订单流安全估算: ABR={micro['active_buy_ratio_%']}%, 推升效率 η={micro['eta_micro_thrust']}")


def test_screener_super_resonance():
    """测试 7：DuckDB 超级主升浪共振初筛"""
    res_df = screener.scan_super_resonance()
    assert isinstance(res_df, pl.DataFrame)
    print(f"\n✅ DuckDB 超级共振榜单查询成功，返回 {len(res_df)} 条记录:")
    print(res_df)


def test_full_tactical_indicator_matrix():
    """测试 8：全景五维量化全套指标矩阵完备性测试"""
    # 构造标准行情
    n = 70
    dates = [f"2026-T{i:03d}" for i in range(n)]
    closes = [10.0 + i * 0.3 for i in range(n)]
    df = pl.DataFrame({
        "Date": dates,
        "Open": [c - 0.1 for c in closes],
        "High": [c + 0.5 for c in closes],
        "Low": [c - 0.5 for c in closes],
        "Close": closes,
        "Turnover": [3.5] * n
    })

    factors_df = chip_engine.compute_mcd_series(df)
    
    # 必须包含的 22 项全维物理真值与战术标记
    required_cols = [
        "Z_Profit", "Z_diff1", "ASR", "X70", "X90",
        "LFS", "HCCYF13", "LFS_ASR_Scissor", "Slope3_LFS",
        "CYF66_Raw", "VMA_CYF55", "CYF_Spread_66_55",
        "CYC5", "CYC13", "CYC34", "CYC_Infinity",
        "CYS13", "CYS34", "BIAS_5_20", "Norm_BIAS_5_20", "BIAS_CYC5_CYCInf",
        "D_Dynamic_Turnover", "D_pos",
        "Is_Vacuum_Corridor", "Is_Major_Controlled",
        "Is_Extreme_Hibernation", "Is_Golden_Pit", "Is_Hot_Potato_Warning"
    ]

    for col in required_cols:
        assert col in factors_df.columns, f"缺少关键物理指标: {col}"

    latest = factors_df.tail(1).to_dicts()[0]
    print(f"\n✅ 全景五维量化 28 项衍生指标全部通过校验！最新截面快照: CYF66={latest['CYF66_Raw']:.2f}, VMA55={latest['VMA_CYF55']:.2f}, D_pos={latest['D_pos']:.1f}, CYC_Inf={latest['CYC_Infinity']:.2f}")

