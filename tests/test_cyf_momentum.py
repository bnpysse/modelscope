"""
Unit tests for CYF66_Raw / VMA(T+55) Strategic Momentum Engine
Tests:
1. 主攻扩张态 (君正/佰维模式)
2. 动能溢出态 · 真空超导 (香农芯创真龙模式)
3. 动能溢出态 · 高摩擦对倒 (德明利模式)
4. 死叉钝化态 (江波龙模式)
5. 黄金反向钳形律与真空走廊穿透耦合
"""
import pytest
from core.signals import SignalJudge, CYFMomentumVerdict


def test_cyf_expansion_mode():
    """测试主攻扩张态: 君正/佰维模式 (0 < ΔCYF <= 15, CYF ∈ [40, 65])"""
    # 君正股份: 52.40 / 41.30 -> ΔCYF = +11.10
    verdict = SignalJudge.judge_cyf_momentum(
        cyf66_raw=52.40,
        vma55=41.30,
        turnover=4.5,
        asr=18.0,
        x70=12.0,
        y_overlap=35.0,
        main_pct=6.5,
        d_pos=40.0,
        bias_5_20=4.2,
        cys34=3.5
    )
    assert verdict.state_code == "EXPANSION"
    assert "【主攻扩张态】" in verdict.state_label
    assert verdict.delta_cyf == 11.10
    assert "主升持仓区" in verdict.tactical_command


def test_cyf_superconductor_shannon_mode():
    """测试真龙真空超导态: 香农芯创模式 (ΔCYF > 15, 低换手 < 8%, 低 ASR < 15)"""
    # 香农芯创: 58.12 / 38.64 -> ΔCYF = +19.48, 换手 7.94%, ASR 12.0
    verdict = SignalJudge.judge_cyf_momentum(
        cyf66_raw=58.12,
        vma55=38.64,
        turnover=7.94,
        asr=12.0,
        x70=8.5,
        y_overlap=25.0,
        main_pct=12.5,
        d_pos=30.0,
        bias_5_20=8.5,
        cys34=5.0
    )
    assert verdict.state_code == "SUPERCONDUCTOR"
    assert "【真龙真空超导态】" in verdict.state_label
    assert verdict.delta_cyf == 19.48
    assert verdict.is_gold_clamp is True  # CYF 58.12 ∈ [40,65], ASR 12.0 < 15
    assert verdict.is_vacuum_tunnel is True # ΔCYF > 15, X70 8.5 < 10, Y 25 <= 30
    assert "绝对锁仓装死" in verdict.tactical_command


def test_cyf_friction_churn_mode():
    """测试高摩擦对倒博弈态: 德明利模式 (ΔCYF > 15, 高换手 12.8%, 高 ASR 22.0)"""
    # 德明利: 64.50 / 46.80 -> ΔCYF = +17.70, 换手 12.8%, ASR 22.0
    verdict = SignalJudge.judge_cyf_momentum(
        cyf66_raw=64.50,
        vma55=46.80,
        turnover=12.8,
        asr=22.0,
        x70=15.0,
        y_overlap=45.0,
        main_pct=3.0,
        d_pos=65.0,
        bias_5_20=11.0,
        cys34=6.0
    )
    assert verdict.state_code == "FRICTION_CHURN"
    assert "【高摩擦对倒博弈】" in verdict.state_label
    assert verdict.delta_cyf == 17.70
    assert "高摩擦" in verdict.tactical_command


def test_cyf_passive_decay_mode():
    """测试死叉钝化态: 江波龙模式 (ΔCYF <= 0 或 CYF < 40)"""
    # 江波龙: 41.20 / 43.80 -> ΔCYF = -2.60
    verdict = SignalJudge.judge_cyf_momentum(
        cyf66_raw=41.20,
        vma55=43.80,
        turnover=5.5,
        asr=28.0,
        x70=18.0,
        y_overlap=55.0,
        main_pct=-2.0,
        d_pos=75.0,
        bias_5_20=-3.0,
        cys34=-4.0
    )
    assert verdict.state_code == "PASSIVE_DECAY"
    assert "【死叉钝化态】" in verdict.state_label
    assert verdict.delta_cyf == -2.60
    assert "动能衰竭" in verdict.tactical_command


def test_position_tier_with_cyf_momentum():
    """测试 4 级仓位状态机与 CYF 动能的协同判定"""
    # 1. 动能衰竭且护城河破位 -> 0% 清仓一票否决
    decay_verdict = SignalJudge.judge_cyf_momentum(cyf66_raw=35.0, vma55=45.0, turnover=5.0, asr=30.0)
    pos_stop = SignalJudge.judge_position_tier(
        lfs=40.0,
        hccyf=55.0,
        scissor=-15.0,
        slope_3d=-0.5,
        bias_5_20=2.0,
        cyf_momentum=decay_verdict
    )
    assert pos_stop.tier_code == "HARD_STOP"
    assert pos_stop.target_pos_pct == 0

    # 2. 真龙超导态 -> 100% 满配锁仓
    super_verdict = SignalJudge.judge_cyf_momentum(cyf66_raw=60.0, vma55=40.0, turnover=5.0, asr=10.0)
    pos_lock = SignalJudge.judge_position_tier(
        lfs=65.0,
        hccyf=45.0,
        scissor=20.0,
        slope_3d=1.5,
        bias_5_20=6.0,
        cyf_momentum=super_verdict
    )
    assert pos_lock.tier_code == "FULL_LOCK"
    assert pos_lock.target_pos_pct == 100
