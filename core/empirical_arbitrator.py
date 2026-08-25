#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实证后验三角交叉验证与 ModelScope 金融大模型智能仲裁引擎 (Empirical Triangulation & AI Arbitrator)
1. 构建【指南针黑盒数据 A】vs【自研微积分物理场 B】vs【未来真实市场走势 Benchmark C】的三角验证模型
2. 自动检测指标背离点（Divergence Points），计算各自对未来 T+1~T+5 真实走势的预测准确率 (Hit Rate)
3. 召唤 ModelScope 旗舰大模型执行病因归因诊断与自适应数学校准裁决
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import polars as pl
from core.quant_chip_engine import chip_engine
from core.providers.modelscope_client import modelscope_client


class EmpiricalArbitrationEngine:
    """实证后验与大模型智能仲裁引擎"""

    def __init__(self, forward_window: int = 5):
        self.forward_window = forward_window

    def detect_divergence_events(self, df_with_both: pl.DataFrame, code: str) -> List[Dict[str, Any]]:
        """
        在时间序列中寻找指南针指标与自研微积分指标出现显著背离的关键交易日
        """
        closes = df_with_both["Close"].to_numpy()
        dates = df_with_both["Date"].to_numpy()
        
        # 指南针指标
        c_lfs = df_with_both["LFS"].to_numpy()
        c_hccyf = df_with_both["HCCYF13"].to_numpy()
        c_z = df_with_both["Z_Profit"].to_numpy()

        # 自研数学指标
        m_lfs = df_with_both["LFS_Math"].to_numpy()
        m_hccyf = df_with_both["HCCYF13_Math"].to_numpy()
        m_z = df_with_both["Z_Math"].to_numpy()

        n_days = len(closes)
        events = []

        for t in range(15, n_days - self.forward_window):
            # 指南针信号判定 (金叉 vs 死叉)
            c_signal = "BULL_LOCK" if c_lfs[t] >= c_hccyf[t] else "BEAR_BREAK"
            # 自研数学信号判定
            m_signal = "BULL_LOCK" if m_lfs[t] >= m_hccyf[t] else "BEAR_BREAK"

            # 计算后续 T+1 ~ T+5 真实市场走势
            future_return_5d = (closes[t + self.forward_window] - closes[t]) / closes[t] * 100.0
            real_outcome = "UP" if future_return_5d > 1.0 else ("DOWN" if future_return_5d < -1.0 else "FLAT")

            # 核心背离触发：两者信号相反，或者获利盘判定差异 > 15%
            is_signal_divergence = (c_signal != m_signal)
            is_z_divergence = abs(c_z[t] - m_z[t]) > 15.0

            if is_signal_divergence or is_z_divergence:
                # 判定哪一方得到了未来真实走势的实证支持
                compass_won = (c_signal == "BULL_LOCK" and real_outcome == "UP") or (c_signal == "BEAR_BREAK" and real_outcome == "DOWN")
                math_won = (m_signal == "BULL_LOCK" and real_outcome == "UP") or (m_signal == "BEAR_BREAK" and real_outcome == "DOWN")

                verdict_status = "COMPASS_WIN" if (compass_won and not math_won) else (
                    "MATH_WIN" if (math_won and not compass_won) else "BOTH_EQUAL"
                )

                events.append({
                    "code": code,
                    "date": str(dates[t]),
                    "close": round(float(closes[t]), 2),
                    "compass": {
                        "LFS": round(float(c_lfs[t]), 2),
                        "HCCYF13": round(float(c_hccyf[t]), 2),
                        "Z": round(float(c_z[t]), 2),
                        "signal": c_signal
                    },
                    "math": {
                        "LFS": round(float(m_lfs[t]), 2),
                        "HCCYF13": round(float(m_hccyf[t]), 2),
                        "Z": round(float(m_z[t]), 2),
                        "signal": m_signal
                    },
                    "realized_future_5d": {
                        "price_after_5d": round(float(closes[t + self.forward_window]), 2),
                        "return_5d_pct": round(float(future_return_5d), 2),
                        "real_outcome": real_outcome
                    },
                    "empirical_winner": verdict_status
                })

        return events

    def arbitrate_with_modelscope(self, event: Dict[str, Any]) -> str:
        """调用 ModelScope 旗舰大模型对具体背离案例进行深度归因与自适应校准裁决"""
        prompt = f"""你是由顶尖对冲基金首席量化架构师组成的【实证后验智能仲裁法庭】。
在标的【{event['code']}】于 {event['date']} 的交易截面上，【商业软件指南针】与【自研微积分物理场】发生了严重战术信号背离，随后市场经历了真实的 5 日检验。数据如下：

================================================================================
【一、 背离截面对比】
================================================================================
- 当日收盘价: {event['close']} 元
- 【指南针系统判定】: LFS={event['compass']['LFS']}, HCCYF13={event['compass']['HCCYF13']}, Z={event['compass']['Z']}%, 战术信号: {event['compass']['signal']}
- 【自研微积分判定】: LFS={event['math']['LFS']}, HCCYF13={event['math']['HCCYF13']}, Z={event['math']['Z']}%, 战术信号: {event['math']['signal']}

================================================================================
【二、 未来 5 交易日真实市场检验结果 (Ground Truth)】
================================================================================
- 5日后收盘价: {event['realized_future_5d']['price_after_5d']} 元 (真实收益率: {event['realized_future_5d']['return_5d_pct']:+.2f}%)
- 真实市场方向: {event['realized_future_5d']['real_outcome']}
- 实证胜出方: 【{event['empirical_winner']}】

================================================================================
【请你执行以下 4 步量化归因与校准裁决】：
================================================================================
1. 【胜负归因剖析】：为什么实证胜出方预测对了？失败方究竟是由于“黑盒平滑滞后”还是“微积分未能捕捉主力底仓粘性”导致的误判？
2. 【指南针失真场景判定】：如果指南针在此处失败，是否表明商业软件在面对突发变盘时存在固有缺陷？
3. 【自适应数学校准建议】：我们应该如何动态修正数学引擎（如调整衰减参数 α、增大护城河窗口、引入主力对倒过滤项）？
4. 【实盘风控裁决军令】：在两套系统再次发生类似背离时，系统应当采取哪种风控策略？
"""

        res = modelscope_client.create_chat_completion(
            messages=[
                {"role": "system", "content": "你是资深金融工程教授与量化系统主审官。"},
                {"role": "user", "content": prompt}
            ],
            model="MiniMax/MiniMax-M1-80k",
            temperature=0.2,
            max_tokens=3000,
            timeout=45
        )
        return res.get("content", "")


arbitrator = EmpiricalArbitrationEngine()
