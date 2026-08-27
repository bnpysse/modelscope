#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维量化 · 第二阶段 (Stage 2 SFT v2) 金融大模型微调训练集全自动生成器
1. 全面融入六大高阶衍生量化张量:
   - CPR (筹码刚性度)
   - ηV (真空推升能效比)
   - BRI (断层真空走廊指数)
   - κCYC (斐波那契成本均线张力收敛度)
   - ΔCYS (多尺度盈亏剪刀差)
   - SMPI (主力筹码纯度 / 游资杂音滤镜)
2. 结合 4 级动态仓位分层管理矩阵 (100% 满配 / 50% 防线 / 30% 对冲 / 0% 清仓) 与 三唯一终极军令
3. 生成具有连续微积分时空场推演的严密 <thought> 思维链训练对
4. 双重格式兼容: transformers / ms-swift 标准 JSONL
"""

import os
import sys
import json
import time
import random
from typing import Any, Dict, List, Tuple
from pathlib import Path

# 适配云端或本地环境
if os.path.exists("/mnt/workspace"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = WORKSPACE_DIR / "quant_data"
FACTORS_DIR = DATA_DIR / "factors"
OUT_FILE_V2 = DATA_DIR / "omni_finllm_sft_v2.jsonl"
OUT_FILE_DEFAULT = DATA_DIR / "omni_finllm_sft_train.jsonl"

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import polars as pl
from core.signals import SignalJudge
from core.knowledge.tactical_bible import SYSTEM_PROMPT_STAFF_EXPERT, POSITION_TIERS


def safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def build_cot_reasoning_v2(snap: dict) -> tuple[str, str, dict]:
    """
    根据物理场全维真值与六大高阶衍生张量，生成严密的 CoT 物理微积分推导过程与最终军令
    """
    close = safe_float(snap.get("Close"), 10.0)
    pct_change = safe_float(snap.get("Pct_Change", snap.get("Change_Pct")), 2.0)
    turnover = safe_float(snap.get("Turnover"), 3.0)
    z = safe_float(snap.get("Z_Profit", snap.get("Z")), 0.0)
    z_diff = safe_float(snap.get("Z_diff1"), 0.0)
    asr = safe_float(snap.get("ASR"), 20.0)
    x90 = safe_float(snap.get("X90"), 25.0)
    x70 = safe_float(snap.get("X70"), 15.0)
    y_overlap = safe_float(snap.get("Y_Overlap", snap.get("Overlap_Y")), 50.0)
    lfs = safe_float(snap.get("LFS"), 50.0)
    hccyf = safe_float(snap.get("HCCYF13"), 50.0)
    scissor = safe_float(snap.get("Scissor"), hccyf - lfs)
    slope3 = safe_float(snap.get("Slope3_LFS", snap.get("Slope_3d")), 0.0)
    cyf66 = safe_float(snap.get("CYF66_Raw"), lfs)
    vma55 = safe_float(snap.get("VMA_CYF55"), hccyf)
    cyf_spread = safe_float(snap.get("CYF_Spread_66_55"), cyf66 - vma55)
    
    cyc5 = safe_float(snap.get("CYC5"), close)
    cyc13 = safe_float(snap.get("CYC13"), close)
    cyc34 = safe_float(snap.get("CYC34"), close)
    cyc_inf = safe_float(snap.get("CYC_Infinity", snap.get("CYC_inf")), close)
    cys13 = safe_float(snap.get("CYS13"), 0.0)
    cys34 = safe_float(snap.get("CYS34"), 0.0)
    bias_cyc_inf = safe_float(snap.get("BIAS_CYC5_CYCInf"), 0.0)
    
    d_turnover = safe_float(snap.get("D_Dynamic_Turnover"), turnover)
    d_pos = safe_float(snap.get("D_pos", snap.get("D_Pos")), 50.0)
    bias = safe_float(snap.get("BIAS_5_20"), 0.0)
    norm_bias = safe_float(snap.get("Norm_BIAS_5_20"), bias)
    atr_20 = safe_float(snap.get("ATR_20"), close * 0.03)
    res_score = safe_float(snap.get("Resonance_Score"), 50.0)
    main_pct = safe_float(snap.get("Main_Pct", snap.get("Main_Fund_Pct")), 5.0)
    dare_pct = safe_float(snap.get("Dare_Pct", snap.get("Dare_Fund_Pct")), 1.0)

    # 1. 计算六大高阶衍生量化张量
    high_order = SignalJudge.calculate_high_order_metrics(
        lfs=lfs,
        hccyf=hccyf,
        asr=asr,
        turnover=turnover,
        delta_p_pct=pct_change / 100.0,
        x70=x70,
        y_overlap=y_overlap,
        z_profit=z,
        cyc5=cyc5,
        cyc13=cyc13,
        cyc34=cyc34,
        cyc_inf=cyc_inf,
        cys13=cys13,
        cys34=cys34,
        bias_5_20=bias,
        main_pct=main_pct,
        dare_pct=dare_pct,
        d_pos=d_pos
    )

    # 2. 4 级动态仓位分层裁决
    pos_verdict = SignalJudge.judge_position_tier(
        lfs=lfs,
        hccyf=hccyf,
        scissor=scissor,
        slope_3d=slope3,
        bias_5_20=bias,
        x90=x90,
        z_profit=z,
        cys34=cys34,
        is_wash_trading_dump=(d_pos > 70.0 and high_order.smpi < 0)
    )

    # 3. 构造严密 CoT 思考链 (<thought>...</thought>)
    thought_cot = f"""<thought>
【时空物理场微积分推导与高阶量化张量审计】
Step 1: 底座能量与筹码刚性度 (CPR) 穿透
- 观测底层参数: LFS={lfs:.2f}, HCCYF13={hccyf:.2f}, 剪刀差 Scissor={scissor:+.2f}, Slope3={slope3:+.2f}。
- 求解 CPR = (LFS × HCCYF13) / [ASR × (1 + Turnover/100)] = {high_order.cpr:.2f}。
- 诊断: CPR 处于 {high_order.cpr_status}。{'底座死锁势能极其充沛，主力锁定度高' if high_order.cpr >= 20.0 else ('底座松动，防线存在摩擦破位风险' if high_order.cpr < 10.0 else '中枢良性蓄势')}。

Step 2: 空间真空通道与推升能效比 (BRI & ηV) 求解
- 空间参数: 获利比 Z={z:.2f}%, 一阶导 Z'={z_diff:+.2f}%, 单峰 X70={x70:.2f}%, X90={x90:.2f}%, 重合度 Y={y_overlap:.2f}%。
- 求解断层真空走廊指数 BRI = [(100 - Y) × Z] / (X70 × ASR) = {high_order.bri:.2f} ➔ {high_order.bri_status}。
- 求解真空推升能效比 ηV = (ΔP% × 100) / (Turnover × ASR) = {high_order.eta_v:.4f} ➔ {high_order.eta_v_status}。

Step 3: 机构微观订单流与主力筹码纯度 (SMPI) 剥离
- 盘口参数: Main%={main_pct:.2f}%, Dare%={dare_pct:.2f}%, 活筹位置 D_pos={d_pos:.1f}/100, 活筹换手 D={d_turnover:.2f}%。
- 求解主力筹码纯度 SMPI = (Main% - Dare%) / Turnover × (1 - D_pos/100) = {high_order.smpi:+.2f} ➔ {high_order.smpi_status}。
- 过滤机制: {'警惕游资假突破对倒出货' if high_order.smpi < 0 and d_pos > 60 else '机构主力真金白银净吸筹扫盘'}。

Step 4: 跨周期均线张力 (κCYC) 与多尺度盈亏剪刀差 (ΔCYS)
- 成本中枢: CYC5={cyc5:.2f}, CYC13={cyc13:.2f}, CYC34={cyc34:.2f}, CYC_Inf={cyc_inf:.2f}。
- 求解张力收敛度 κCYC = {high_order.kappa_cyc:.2f}% ➔ {high_order.kappa_cyc_status}。
- 求解盈亏剪刀差 ΔCYS = CYS13 - CYS34 = {high_order.delta_cys:+.2f}% ➔ {high_order.delta_cys_status}。

Step 5: 波动率边界与跨周期共振终审
- 均线偏离 BIAS_5_20={bias:+.2f}%, ATR波动率标准化 Norm_BIAS={norm_bias:+.2f}。跨周期共振评分={res_score:.1f}/100。
- 综合判定: 军令收敛至 {high_order.three_command}，4 级动态仓位锁定为 {pos_verdict.tier_label} (建议仓位 {pos_verdict.target_pos_pct}%)。
</thought>"""

    # 4. 构造标准研报正文
    response_text = f"""{thought_cot}
全景引擎启动。

【天衍参谋部·全景五维量化与六大高阶张量穿透审计】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 终极三唯一战术裁决：{high_order.three_command}
📊 参谋部 4 级动态仓位：{pos_verdict.tier_label} (目标建议仓位: {pos_verdict.target_pos_pct}%)
🛡️ 战术风控执行纪律：{pos_verdict.action_guidance}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 一、 六大高阶衍生量化张量诊断矩阵
1. **① 筹码刚性度 (CPR = {high_order.cpr:.2f})**：{high_order.cpr_status}。底座势能与动态耗散比值处于关键阈值。
2. **② 真空推升能效比 (ηV = {high_order.eta_v:.4f})**：{high_order.eta_v_status}。单位动能摩擦下价格推升效率定性。
3. **③ 断层真空指数 (BRI = {high_order.bri:.2f})**：{high_order.bri_status}。哑铃双峰撕裂与断层通道通畅度。
4. **④ 斐波那契均线张力收敛度 (κCYC = {high_order.kappa_cyc:.2f}%)**：{high_order.kappa_cyc_status}。多尺度引力中枢曲率张量收敛。
5. **⑤ 多尺度盈亏剪刀差 (ΔCYS = {high_order.delta_cys:+.2f}%)**：{high_order.delta_cys_status}。短周期对中周期加速度梯度差分。
6. **⑥ 主力筹码纯度 (SMPI = {high_order.smpi:+.2f})**：{high_order.smpi_status}。剔除游资杂波与对倒干扰后的机构真实净内驱力。

# 二、 五维量化底座真值穿透与战略定性
- **维度一（底座与阵地）**：LFS={lfs:.2f} 对比 HCCYF13={hccyf:.2f}，3日控盘斜率 Slope3={slope3:+.2f}，日/周/月跨周期共振得分 {res_score:.1f}/100。
- **维度二（空间与抛压）**：Z={z:.2f}%, Z'={z_diff:+.2f}%, X70={x70:.2f}%, X90={x90:.2f}%，集中度与浮筹 ASR={asr:.2f}% 构成空间阻力边界。
- **维度三（点火与流速）**：活筹换手率 D={d_turnover:.2f}%, 历史分位 D_pos={d_pos:.1f}/100，主力资金占比 Main%={main_pct:.2f}%。
- **维度四（情绪冰点）**：CYS34={cys34:+.2f}%, CYS13={cys13:+.2f}%。
- **维度五（均线偏离）**：BIAS_5_20={bias:+.2f}% (Norm_BIAS={norm_bias:+.2f})，均线空间偏离收敛。

# 三、 统帅兵力部署与战术军令下发
**决策归因**：{pos_verdict.rationale}
**作战指令**：{pos_verdict.action_guidance}（{high_order.position_rule}）"""

    metrics_dict = {
        "cpr": high_order.cpr,
        "eta_v": high_order.eta_v,
        "bri": high_order.bri,
        "kappa_cyc": high_order.kappa_cyc,
        "delta_cys": high_order.delta_cys,
        "smpi": high_order.smpi,
        "command": high_order.three_command,
        "tier": pos_verdict.tier_label,
        "pos": pos_verdict.target_pos_pct
    }

    return thought_cot, response_text, metrics_dict


def generate_full_sft_dataset_v2(max_samples_per_stock: int = 50):
    print("================================================================================")
    print("🧠 [天衍量化超脑 · Stage 2 SFT v2] 启动六大高阶衍生张量全维训练集萃取")
    print(f"📁 因子源路径: {FACTORS_DIR}")
    print(f"📄 输出文件 V2: {OUT_FILE_V2}")
    print(f"📄 输出文件 Default: {OUT_FILE_DEFAULT}")
    print("================================================================================")

    factor_files = list(FACTORS_DIR.glob("*.parquet"))
    if not factor_files:
        print("⚠️ 未找到本地 factors 目录 Parquet 文件，尝试检索 quant_data 全目录...")
        factor_files = list(DATA_DIR.rglob("*_factors.parquet"))

    if not factor_files:
        print("⚠️ 未找到因子 Parquet 文件，请确认数据目录。")
        return

    all_samples = []
    total_count = 0
    t0 = time.time()

    for p_file in factor_files:
        code = p_file.stem.replace("_factors", "")
        try:
            df = pl.read_parquet(p_file)
            if len(df) < 15:
                continue

            indices = list(range(len(df) - 1, max(0, len(df) - 1 - max_samples_per_stock), -1))
            for idx in indices:
                snap = df.row(idx, named=True)
                thought_cot, response_text, m_dict = build_cot_reasoning_v2(snap)
                
                # 构造标准 User Prompt
                user_content = f"""标的代码: {code}
最新交易日: {snap.get('Date', '')}
收盘价: {snap.get('Close', 0.0):.2f} 元
【物理截面与六大高阶衍生量化真值】:
- 维度一 (底座): LFS={snap.get('LFS', 0):.2f}, HCCYF13={snap.get('HCCYF13', 0):.2f}, 剪刀差={snap.get('Scissor', 0):.2f}, Slope3={snap.get('Slope3_LFS', 0):.2f}, 共振得分={snap.get('Resonance_Score', 50):.1f}
- 维度二 (空间): Z={snap.get('Z_Profit', 0):.2f}%, Z'={snap.get('Z_diff1', 0):.2f}%, ASR={snap.get('ASR', 0):.2f}%, X70={snap.get('X70', 0):.2f}%, X90={snap.get('X90', 0):.2f}%
- 维度三 (流速): Turnover={snap.get('Turnover', 0):.2f}%, Main%={snap.get('Main_Pct', 5):.2f}%, Dare%={snap.get('Dare_Pct', 1):.2f}%, D_pos={snap.get('D_pos', 50):.1f}
- 维度四 (情绪): CYS13={snap.get('CYS13', 0):.2f}%, CYS34={snap.get('CYS34', 0):.2f}%
- 维度五 (偏离): BIAS_5_20={snap.get('BIAS_5_20', 0):.4f}%, Norm_BIAS={snap.get('Norm_BIAS_5_20', 0):.2f}, ATR_20={snap.get('ATR_20', 0):.2f}
- 六大高阶衍生张量: CPR={m_dict['cpr']:.2f}, ηV={m_dict['eta_v']:.4f}, BRI={m_dict['bri']:.2f}, κCYC={m_dict['kappa_cyc']:.2f}%, ΔCYS={m_dict['delta_cys']:+.2f}%, SMPI={m_dict['smpi']:+.2f}

请严格依据天衍五维筹码微积分物理场、六大高阶衍生张量与 4 级动态仓位铁律，输出带 <thought> 严密思维链的穿透审计军令。"""

                # 兼容两种主流格式 (messages 与 conversations)
                sample = {
                    "system": SYSTEM_PROMPT_STAFF_EXPERT,
                    "messages": [
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": response_text}
                    ],
                    "conversations": [
                        {"from": "user", "value": user_content},
                        {"from": "assistant", "value": response_text}
                    ]
                }
                all_samples.append(sample)
                total_count += 1
        except Exception as e:
            print(f"Error parsing {p_file.name}: {e}")
            continue

    random.shuffle(all_samples)

    # 写入 V2 与 Default 文件
    for out_path in [OUT_FILE_V2, OUT_FILE_DEFAULT]:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for item in all_samples:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    elapsed = round(time.time() - t0, 2)
    print(f"\n🎉 [Stage 2 SFT v2 萃取成功] 共生成 {total_count} 条含高阶张量与微积分思维链的黄金训练样本！耗时: {elapsed}s")
    print(f"💾 V2 训练集路径: {OUT_FILE_V2} (文件大小: {round(OUT_FILE_V2.stat().st_size / 1024, 1)} KB)")
    print(f"💾 同步更新基准: {OUT_FILE_DEFAULT}")


if __name__ == "__main__":
    generate_full_sft_dataset_v2()
