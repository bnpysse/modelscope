"""
天眼全息智导系统 V7.0 (ModelScope Edition) — 参谋部 AI 穿透审计引擎 (AI Tactical Advisor)

结合统帅量化战术知识库 (tactical_bible)、斐波那契战略纵深矩阵与 ModelScope 官方免费大模型 (MiniMax M1 / Qwen 3 235B / Qwen 3 30B)，
对当前标的执行穿透式量化推演与绝对军令下发。
"""
import os
import json
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st

from core.signals import SignalJudge
from core.knowledge.tactical_bible import (
    INDICATOR_DICTIONARY,
    COMMANDS,
    POSITION_TIERS,
    SYSTEM_PROMPT_STAFF_EXPERT,
)
from core.providers.modelscope_client import modelscope_client


def evaluate_local_tactical_status(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    纯本地高速量化规则状态机推演 (零网络依赖，毫秒级响应)
    已升级为 4 级动态仓位分层管理矩阵
    """
    asr = float(d.get("ASR", 20.0) or 20.0)
    x70 = float(d.get("X70", 15.0) or 15.0)
    x90 = float(d.get("X90", 25.0) or 25.0)
    y_ovp = float(d.get("Y_Overlap", 50.0) or 50.0)
    to = float(d.get("Turnover", 5.0) or 5.0)
    z_profit = float(d.get("Z_Profit", d.get("Z", 30.0)) or 30.0)
    z_diff1 = float(d.get("Z_diff1", 0.0) or 0.0)
    hccyf = float(d.get("HCCYF13", 40.0) or 40.0)
    lfs = float(d.get("LFS", 40.0) or 40.0)
    scissor = float(d.get("Scissor", hccyf - lfs) or (hccyf - lfs))
    slope_3d = float(d.get("Slope_3d", d.get("Slope3_LFS", 0.0)) or 0.0)
    bias_5_20 = float(d.get("BIAS_5_20", 0.0) or 0.0)
    norm_bias = float(d.get("Norm_BIAS_5_20", 0.0) or 0.0)
    cys34 = float(d.get("CYS34", 0.0) or 0.0)
    d_pos = float(d.get("D_Pos", 50.0) or 50.0)
    res_score = float(d.get("Resonance_Score", 50.0) or 50.0)
    
    delta_p = float(d.get("Delta_Sum_1d", 1.5) or 1.5)
    eta = round(abs(delta_p) / max(to, 0.1), 2)
    is_wash_dump = bool(d.get("is_wash_trading_dump", False))

    # 1. 核心战术形态判定
    is_pincer = (hccyf >= 40 and asr < 15 and x70 < 10)
    is_vacuum = (z_diff1 > 10 and x90 < 10) or (x70 < 10 and y_ovp <= 35)
    is_strong_lock = (lfs >= hccyf) and (slope_3d > 1.5)
    is_moat_dead_cross = (hccyf > lfs) and (slope_3d < -2.0)
    is_golden_pit = (cys34 < -15.0) and (lfs >= hccyf)
    is_pump_dump_warning = (d_pos > 70) and (to > 12.0)
    is_super_resonance = res_score >= 80.0

    verdict_tags = []
    if is_super_resonance:
        verdict_tags.append("👑 三周期超级主升共振")
    if is_strong_lock:
        verdict_tags.append("★ 护城河多头金叉·强锁仓")
    if is_pincer:
        verdict_tags.append("★ 黄金反向钳形")
    if is_vacuum:
        verdict_tags.append("◆ 哑铃型真空主升")
    if is_golden_pit:
        verdict_tags.append("■ 战略级黄金坑买点")
    if is_pump_dump_warning or is_wash_dump:
        verdict_tags.append("✖ 游资倒手/对倒出货预警")
    if not verdict_tags:
        verdict_tags.append("● 常规量化博弈态")

    # 2. 4 级动态仓位决策
    pos_verdict = SignalJudge.judge_position_tier(
        lfs=lfs,
        hccyf=hccyf,
        scissor=scissor,
        slope_3d=slope_3d,
        bias_5_20=bias_5_20,
        x90=x90,
        z_profit=z_profit,
        cys34=cys34,
        is_wash_trading_dump=is_wash_dump
    )

    return {
        "status_title": " · ".join(verdict_tags),
        "order": pos_verdict.tier_label,
        "order_desc": pos_verdict.action_guidance,
        "rationale": pos_verdict.rationale,
        "target_position_pct": pos_verdict.target_pos_pct,
        "position_tier_code": pos_verdict.tier_code,
        "badge_color": pos_verdict.color,
        "eta": eta,
        "asr": asr,
        "x70": x70,
        "x90": x90,
        "y_ovp": y_ovp,
        "hccyf": hccyf,
        "lfs": lfs,
        "scissor": scissor,
        "slope_3d": slope_3d,
        "bias_5_20": bias_5_20,
        "norm_bias": norm_bias,
        "cys34": cys34,
        "resonance_score": res_score,
    }


def format_panoramic_prompt(stock_code: str, stock_name: str, snapshot: Dict[str, Any], fib_matrix: List[Dict[str, Any]]) -> str:
    """
    格式化生成符合 198 交易日战略纵深的全景提示词
    """
    fib_lines = [
        "| 斐波那契周期 | 起始日期 | 起始价 (元) | 最新价 (元) | 周期涨跌幅 (%) | 日均换手率 (%) | 平均 LFS | 平均 ASR (%) | 平均 获利比例 Z (%) | 平均 CYS34 (%) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    for row in fib_matrix:
        fib_lines.append(
            f"| **{row['Period']}** | {row['Start_Date']} | {row['Price_Start']} | {row['Price_End']} | "
            f"{row['Price_Change_%']:+.2f}% | {row['Avg_Turnover_%']:.2f}% | {row['Avg_LFS']:.2f} | "
            f"{row['Avg_ASR']:.2f}% | {row['Avg_Z_%']:.2f}% | {row['Avg_CYS34']:.2f}% |"
        )
    fib_table_md = "\n".join(fib_lines)

    date_str = snapshot.get("Date_Full", snapshot.get("Date", "最新交易日"))
    
    prompt = f"""全景引擎启动。
请对标的：【{stock_name} ({stock_code})】截至 {date_str} 的全景宏观战略演化及物理真值截面执行穿透式数学审计。

# 一、 斐波那契战略纵深矩阵（历史时序解构）
{fib_table_md}

# 二、 最新物理真值截面快照与 V2 进阶特征
- 收盘价 (Close): {snapshot.get('Close')} 元 (开: {snapshot.get('Open')}, 高: {snapshot.get('High')}, 低: {snapshot.get('Low')})
- 跨周期共振得分 (Resonance): {snapshot.get('Resonance_Score', 50)} / 100 ({snapshot.get('Resonance_Diagnosis', '常规')})
- Turnover (换手率): {snapshot.get('Turnover')}% | Main% (主力): {snapshot.get('Main_Pct')}% | Dare% (游资): {snapshot.get('Dare_Pct')}%
- X70 (70%筹码宽度): {snapshot.get('X70')}% | X90: {snapshot.get('X90')}% | Y (重合度): {snapshot.get('Y_Overlap')}%
- Z (获利比例): {snapshot.get('Z_Profit', snapshot.get('Z'))}% | D_pos (活筹位置): {snapshot.get('D_Pos')} | Flow_5d: {snapshot.get('Flow_5d')}
- ASR (活动筹码): {snapshot.get('ASR')}% | CYS34 (市场盈亏): {snapshot.get('CYS34')}%
- LFS (锁定因子): {snapshot.get('LFS')} | HCCYF13 (护城河): {snapshot.get('HCCYF13')}
- Slope3_LFS (3日斜率): {snapshot.get('Slope3_LFS', snapshot.get('Slope_3d'))} | BIAS_5_20: {snapshot.get('BIAS_5_20'):.4f}%
- ATR_20 (真实波幅): {snapshot.get('ATR_20', 0)} | Norm_BIAS (波动率标准化乖离率): {snapshot.get('Norm_BIAS_5_20', 0)}
- CYF66_Raw / VMA(T+55): {snapshot.get('CYF66_Raw', 50):.2f} / {snapshot.get('CYF66_VMA55', 50):.2f}

请严格按照参谋部规范输出全景深度研报：
1. 【一、 198 交易日斐波那契战略纵深矩阵研判】（总结全周期演化）
2. 【二、 最新截面五维量化底座真值研判】（逐一穿透底座、空间、流速、情绪、偏离五大维度）
3. 【三、 统帅兵力部署与参谋部 4 级动态仓位执行裁决】（必须明确下发以下 4 级动态仓位军令之一，并给出具体仓位建议与执行理由）：
   • 【满配主升·绝对锁仓】 (建议仓位: 80%~100%)
   • 【防线预警·分批减仓】 (建议仓位: 50%)
   • 【反向对冲·动态降本】 (建议仓位: 30%)
   • 【底座坍塌·坚决清仓】 (建议仓位: 0%)
"""
    return prompt


@st.cache_data(show_spinner=False, ttl=1800)
def query_ai_staff_report(
    stock_code: str,
    stock_name: str,
    snapshot_json: str,
    fib_matrix_json: str = "[]",
    selected_model: str = "MiniMax/MiniMax-M1-80k"
) -> Dict[str, Any]:
    """
    调用 ModelScope 免费大模型生成参谋部专属全景穿透审计研报 (返回包含 content, thinking, model, duration)
    """
    snapshot = json.loads(snapshot_json)
    fib_matrix = json.loads(fib_matrix_json)
    local_eval = evaluate_local_tactical_status(snapshot)

    user_prompt = format_panoramic_prompt(stock_code, stock_name, snapshot, fib_matrix)

    # 优先调用 ModelScope 官方免费大模型 (MiniMax M1 / Qwen3 235B / 30B 级联)
    try:
        res = modelscope_client.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_STAFF_EXPERT},
                {"role": "user", "content": user_prompt}
            ],
            model=selected_model,
            temperature=0.1,
            max_tokens=3500
        )
        return {
            "status": "success",
            "content": res.get("content", "").strip(),
            "thinking": res.get("thinking", ""),
            "model_used": res.get("model", selected_model),
            "duration_seconds": res.get("duration_seconds", 0.0),
            "quota_status": res.get("quota_status", {})
        }
    except Exception as e:
        st.warning(f"⚠️ ModelScope API 调用提示 ({e})，已自动降级为本地量化状态机。")

    # 纯本地参谋部兜底报告
    date_str = snapshot.get("Date_Full", snapshot.get("Date", "最新日"))
    fallback_content = f"""全景引擎启动。
基于最新物理真值快照，本地量化状态机针对标的 【{stock_name} ({stock_code})】 截至 {date_str} 输出 4 级动态仓位确定性穿透裁决：

# 一、 五维量化底座真值穿透
1. **维度一（底座与阵地）**：LFS={local_eval['lfs']:.2f} 对比 HCCYF13={local_eval['hccyf']:.2f}，3日控盘斜率 Slope3={local_eval['slope_3d']:.2f}，跨周期共振得分 Resonance={local_eval['resonance_score']:.1f}/100。
2. **维度二（空间与抛压）**：X70={local_eval['x70']:.2f}%，X90={local_eval['x90']:.2f}%，筹码锁定密集，真空走廊畅通。
3. **维度三（点火与流速）**：量能推升效率 η={local_eval['eta']}，换手率处于主力强吸沉淀区。
4. **维度四（情绪冰点）**：CYS34={local_eval['cys34']:.2f}%，底部筹码稳固。
5. **维度五（均线偏离）**：BIAS_5_20={local_eval['bias_5_20']:.2f}% (Norm_BIAS={local_eval['norm_bias']:.2f})，均线充分收敛。

# 二、 参谋部 4 级动态仓位执行裁决
● 状态定性：{local_eval['status_title']}
● 仓位目标：【建议仓位 {local_eval['target_position_pct']}%】
● 决策理由：{local_eval['rationale']}

**参谋部战术执行指令**：
{local_eval['order']}（{local_eval['order_desc']}）"""

    return {
        "status": "fallback",
        "content": fallback_content,
        "thinking": "",
        "model_used": "纯本地确定性状态机 (Local Fallback)",
        "duration_seconds": 0.01,
        "quota_status": modelscope_client.get_quota_status()
    }
