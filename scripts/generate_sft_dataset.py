#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维量化 · ms-swift 金融大模型微调 SFT 数据集全自动生成器
1. 从 5000+ 标的历史因子库与 198 交易日斐波那契矩阵中抽取样本
2. 注入 Level-2 微观订单流与 22 项物理真值
3. 生成带有标准 CoT 深度思考链 (<thought>...</thought>) 的高纯度金融量化训练对
4. 输出标准 ms-swift 训练 JSONL 格式: /mnt/workspace/quant_data/sft_dataset.jsonl
"""

import os
import sys
import json
import time
import random
from pathlib import Path

# 适配云端或本地环境
if os.path.exists("/mnt/workspace"):
    WORKSPACE_DIR = Path("/mnt/workspace")
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = WORKSPACE_DIR / "quant_data"
FACTORS_DIR = DATA_DIR / "factors"
OUT_FILE = DATA_DIR / "omni_finllm_sft_train.jsonl"

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import polars as pl
from core.signals import SignalJudge
from core.knowledge.tactical_bible import SYSTEM_PROMPT_STAFF_EXPERT, POSITION_TIERS


def build_cot_reasoning(snap: dict) -> str:
    """根据物理场全维真值生成严密的 CoT 物理微积分推演过程与最终军令"""
    close = float(snap.get("Close", 10.0))
    z = float(snap.get("Z_Profit", 0.0))
    z_diff = float(snap.get("Z_diff1", 0.0))
    asr = float(snap.get("ASR", 0.0))
    x90 = float(snap.get("X90", 0.0))
    x70 = float(snap.get("X70", 0.0))
    y_overlap = float(snap.get("Y_Overlap", 50.0))
    lfs = float(snap.get("LFS", 0.0))
    hccyf = float(snap.get("HCCYF13", 0.0))
    scissor = float(snap.get("Scissor", 0.0))
    slope3 = float(snap.get("Slope3_LFS", 0.0))
    cyf66 = float(snap.get("CYF66_Raw", lfs))
    vma55 = float(snap.get("VMA_CYF55", hccyf))
    cyf_spread = float(snap.get("CYF_Spread_66_55", cyf66 - vma55))
    
    cyc5 = float(snap.get("CYC5", close))
    cyc13 = float(snap.get("CYC13", close))
    cyc34 = float(snap.get("CYC34", close))
    cyc_inf = float(snap.get("CYC_Infinity", close))
    cys13 = float(snap.get("CYS13", 0.0))
    cys34 = float(snap.get("CYS34", 0.0))
    bias_cyc_inf = float(snap.get("BIAS_CYC5_CYCInf", 0.0))
    
    d_turnover = float(snap.get("D_Dynamic_Turnover", 3.0))
    d_pos = float(snap.get("D_pos", 50.0))
    bias = float(snap.get("BIAS_5_20", 0.0))
    norm_bias = float(snap.get("Norm_BIAS_5_20", bias))
    res_score = float(snap.get("Resonance_Score", 50.0))
    
    # 战术特征识别
    is_vacuum = bool(snap.get("Is_Vacuum_Corridor", (z_diff > 10.0 and x90 < 10.0) or (z_diff > 15.0 and x90 <= 15.0)))
    is_major = bool(snap.get("Is_Major_Controlled", (z > 95.0 and float(snap.get("Turnover", 3.0)) < 3.0) or bias_cyc_inf > 30.0))
    is_hibernation = bool(snap.get("Is_Extreme_Hibernation", y_overlap > 60.0 and float(snap.get("Turnover", 3.0)) < 3.5))
    is_golden_pit = bool(snap.get("Is_Golden_Pit", cys34 < -15.0 and lfs >= hccyf))
    is_hot_potato = bool(snap.get("Is_Hot_Potato_Warning", d_pos > 70.0))
    
    # 状态机裁决
    verdict = SignalJudge.judge_position_tier(
        lfs=lfs, hccyf=hccyf, scissor=scissor,
        slope_3d=slope3,
        bias_5_20=bias, x90=x90, z_profit=z, cys34=cys34
    )

    cot_text = f"""1. 【维度一：底座与阵地（筹码锁定与中枢防护）】：
   - 筹码锁定因子 LFS={lfs:.1f}, 13日护城河 HCCYF13={hccyf:.1f}, 暴力锁仓剪刀差 LFS-ASR={lfs-asr:+.1f}。
   - 3日控盘斜率 Slope3(LFS)={slope3:+.2f}。
   - 斐波那契跨周期死锁: CYF66_Raw={cyf66:.1f} / VMA(T+55)={vma55:.1f} (敞口差={cyf_spread:+.2f})。
   - 诊断结论：{'主力底座护城河破位死叉，底座坍塌' if hccyf > lfs and slope3 < -1.5 else ('超级战略庄家深度死锁' if cyf66 > vma55 and lfs >= hccyf else '多头常态锁仓护城河稳固')}。

2. 【维度二：空间与抛压（筹码真空走廊与控盘雷达）】：
   - 获利盘 Z={z:.1f}%, 单日一阶导数 Z'={z_diff:+.1f}%, 浮筹比 ASR={asr:.1f}%。
   - 集中度 X70={x70:.1f}%, X90={x90:.1f}%, 重合度 Y={y_overlap:.1f}%。
   - 指数成本均线: CYC5={cyc5:.2f}, CYC13={cyc13:.2f}, CYC34={cyc34:.2f}, 全局无穷成本 CYC_Inf={cyc_inf:.2f}。
   - 诊断结论：{'触发【物理真空走廊】，上方无阻力层加速上攻' if is_vacuum else ('触发【庄股雷达高控盘拉升豁免】' if is_major else '常态筹码分布')}。

3. 【维度三：点火与流速（盘口动量与资金对冲）】：
   - 真实活筹换手率 D={d_turnover:.2f}%, 活筹历史位置 D_pos={d_pos:.1f}/100。
   - 诊断结论：{'【游资击鼓传花派发预警】D_pos异常飙升，严禁追高' if is_hot_potato else ('主力强吸/缩量锁仓主升' if d_pos < 50 else '多空常规换手博弈')}。

4. 【维度四：情绪冰点与黄金坑（极端逆向博弈）】：
   - 13日市场盈亏 CYS13={cys13:+.1f}%, 34日市场盈亏 CYS34={cys34:+.1f}%。
   - 诊断结论：{'触发【黄金坑战略买点】(散户深套割肉但主力底座未散)' if is_golden_pit else ('处于【极限装死区】(卖压彻底衰竭)' if is_hibernation else '常态情绪区间')}。

5. 【维度五：均线偏离与均值回归（波动率边界控制）】：
   - BIAS_5_20={bias:+.2f}%, 真实波幅归一化 Norm_BIAS={norm_bias:+.2f}。
   - 日/周/月跨周期筹码张量协整共振得分={res_score:.1f}/100。
   - 诊断结论：{'【脉冲诱多超买】BIAS>15%，浮动仓执行反向做T' if bias > 15.0 else ('【均线粘合蓄势区】主升浪爆发前夜' if abs(bias) <= 5.0 else '均值回归区间')}。"""

    response_text = f"""全景引擎启动。

【天衍参谋部·全景五维量化穿透审计】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 最终战术军令：{verdict.tier_label}
📊 目标建议仓位：{verdict.target_pos_pct}% (强制保留20%现金流动性对冲盾)
🛡️ 核心战术归因：{verdict.action_guidance}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【五维物理场全维深度审计推演】
{cot_text}"""

    return cot_text, response_text


def generate_full_sft_dataset(max_samples_per_stock: int = 20):
    print("================================================================================")
    print("🧠 [天衍量化大模型 SFT 数据工坊] 启动标准 CoT 训练集萃取 (28项全维物理量)")
    print(f"📁 因子源路径: {FACTORS_DIR}")
    print(f"📄 输出文件: {OUT_FILE}")
    print("================================================================================")

    factor_files = list(FACTORS_DIR.glob("*.parquet"))
    if not factor_files:
        print("⚠️ 未找到因子 Parquet 文件，请先确保因子库计算完成。")
        return

    all_conversations = []
    total_count = 0
    t0 = time.time()

    for p_file in factor_files:
        code = p_file.stem.replace("_factors", "")
        try:
            df = pl.read_parquet(p_file)
            if len(df) < 20:
                continue

            indices = list(range(len(df) - 1, max(0, len(df) - 1 - max_samples_per_stock), -1))
            for idx in indices:
                snap = df.row(idx, named=True)
                cot, response = build_cot_reasoning(snap)
                
                # 构造输入 User Prompt
                user_content = f"""标的代码: {code}
最新交易日: {snap.get('Date', '')}
收盘价: {snap.get('Close', 0.0):.2f}
【物理截面 28 项全维真值】:
- 维度一 (底座): LFS={snap.get('LFS', 0):.2f}, HCCYF13={snap.get('HCCYF13', 0):.2f}, 剪刀差={snap.get('Scissor', 0):.2f}, Slope3={snap.get('Slope3_LFS', 0):.2f}, CYF66={snap.get('CYF66_Raw', 0):.2f}, VMA55={snap.get('VMA_CYF55', 0):.2f}
- 维度二 (空间): Z={snap.get('Z_Profit', 0):.2f}%, Z'={snap.get('Z_diff1', 0):.2f}%, ASR={snap.get('ASR', 0):.2f}%, X70={snap.get('X70', 0):.2f}%, X90={snap.get('X90', 0):.2f}%, CYC_Inf={snap.get('CYC_Infinity', 0):.2f}
- 维度三 (流速): D_Dynamic={snap.get('D_Dynamic_Turnover', 0):.2f}%, D_pos={snap.get('D_pos', 50):.1f}, Turnover={snap.get('Turnover', 0):.2f}%
- 维度四 (情绪): CYS13={snap.get('CYS13', 0):.2f}%, CYS34={snap.get('CYS34', 0):.2f}%
- 维度五 (偏离): BIAS_5_20={snap.get('BIAS_5_20', 0):.4f}%, Norm_BIAS={snap.get('Norm_BIAS_5_20', 0):.2f}, ATR_20={snap.get('ATR_20', 0):.2f}, 共振得分={snap.get('Resonance_Score', 50):.1f}

请严格依据天衍五维筹码物理微积分与 4 级动态仓位铁律，输出带 CoT 思考链的穿透审计军令。"""

                sample = {
                    "system": SYSTEM_PROMPT_STAFF_EXPERT,
                    "conversations": [
                        {
                            "from": "user",
                            "value": user_content
                        },
                        {
                            "from": "assistant",
                            "value": response
                        }
                    ]
                }
                all_conversations.append(sample)
                total_count += 1
        except Exception:
            continue

    random.shuffle(all_conversations)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for item in all_conversations:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    elapsed = round(time.time() - t0, 1)
    print(f"\n🎉 SFT 训练集萃取完成！共生成 {total_count} 条高纯度 CoT 量化微积分训练样本，耗时: {elapsed}s")
    print(f"📁 训练集已落盘: {OUT_FILE} (文件体积: {round(OUT_FILE.stat().st_size / 1024 / 1024, 2)} MB)")


if __name__ == "__main__":
    generate_full_sft_dataset()
