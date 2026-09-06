# -*- coding: utf-8 -*-
"""
天衍五维 · 终极物理量子与连续场拓扑图表组件
(Quantum Physics & Topological Continuum Visualizer)

专为 DuckDB 偏微分物理推导模式打造：
集成 14 核心物理真值指标 + 4 激进物理拓扑指标，共 18 项指标统一呈现：
- 维度一【引力做功】：价格 K线 + CYC 成本均线引力场 (CYC5/13/34/inf) + Wasserstein-1D 筹码推土做功 W_cost
- 维度二【势阱真空】：获利盘 Z' + 活动筹码 ASR + 断层真空 BRI + 福克-普朗克势阱逃逸率 P_escape
- 维度三【筹码刚性】：筹码锁定 LFS + 集中度 X70 + 护城河剪刀差 Scissor + 刚性度 CPR
- 维度四【盈亏张力】：短中盈亏 CYS13/CYS34 + 盈亏剪刀差 ΔCYS + 均线偏离 BIAS_5_20 + 斐波收敛 κCYC
- 维度五【量子相干】：库普曼相干模态纯度 λ_dmd + TDA 拓扑射流比 β_1 + 筹码纯度 SMPI + CYF66 战略动能/资金流

特性：
- 5 层子图共享 X 轴 (shared_xaxes)
- 纯暗黑战术高对比度主题
- 跨子图无缝垂直准星线联动 + 右侧物理全息 HUD 极速毫秒级悬停看板
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components

from core.advanced_physics_pde import advanced_pde

# ══════════════════════════════════════════════
# 颜色常量与战术主题
# ══════════════════════════════════════════════
BG_COLOR = "#0B0F19"
PANEL_COLOR = "#131B2E"
GRID_COLOR = "rgba(255, 255, 255, 0.05)"
TEXT_COLOR = "#E2E8F0"
MUTE_COLOR = "#64748B"

P_COLORS = {
    "price": "#F8FAFC",
    "cyc5": "#38BDF8",      # 天蓝
    "cyc13": "#F59E0B",     # 金黄
    "cyc34": "#A855F7",     # 亮紫
    "cyc_inf": "#94A3B8",   # 灰色虚线
    "w_cost": "#10B981",    # 翡翠绿 (做功能量)
    "z_profit": "#FBBF24",  # 琥珀金
    "asr": "#06B6D4",       # 活跃青
    "p_escape": "#10B981",  # 逃逸相变绿
    "bri": "#C084FC",       # 真空紫
    "lfs": "#3B82F6",       # 锁仓深蓝
    "x70": "#F59E0B",       # 集中度橙
    "cpr": "#F43F5E",       # 刚性玫瑰红
    "scissor_pos": "rgba(16, 185, 129, 0.25)",
    "scissor_neg": "rgba(239, 68, 68, 0.25)",
    "cys13": "#38BDF8",
    "cys34": "#818CF8",
    "delta_cys_pos": "#10B981",
    "delta_cys_neg": "#EF4444",
    "kappa_cyc": "#84CC16", # 荧光青柠绿
    "dmd": "#A855F7",       # 库普曼相干紫
    "tda": "#22D3EE",       # 拓扑射流蓝
    "smpi": "#EAB308",      # 纯度黄
    "cyf66": "#EC4899",     # 动能粉红
    "vma55": "#64748B",     # 基准灰
}


def compute_quantum_physics_series(df_input: Any) -> pd.DataFrame:
    """
    向量化快速补齐 18 项物理指标的全时序数据，耗时 < 30ms。
    支持输入 Polars DataFrame 或 Pandas DataFrame。
    """
    if hasattr(df_input, "to_pandas"):
        df = df_input.to_pandas()
    else:
        df = df_input.copy()

    n = len(df)
    if n == 0:
        return df

    # 1. 基础行情提取
    close = df["Close"].to_numpy(dtype=float) if "Close" in df.columns else np.full(n, 10.0)
    to = df["Turnover"].to_numpy(dtype=float) if "Turnover" in df.columns else np.full(n, 3.0)
    to = np.where(to > 100.0, 10.0, to)

    # 日期标签
    if "Date_Full" in df.columns:
        dates_full = [str(d) for d in df["Date_Full"]]
    elif "Date" in df.columns:
        dates_full = [str(d) for d in df["Date"]]
    else:
        dates_full = [f"T-{i}" for i in range(n)]

    if "Date_Disp" in df.columns:
        dates_disp = [str(d) for d in df["Date_Disp"]]
    else:
        dates_disp = [d[-5:] if len(d) >= 5 else d for d in dates_full]

    # 2. 筹码与均线提取或补齐
    asr = df["ASR"].to_numpy(dtype=float) if "ASR" in df.columns else np.full(n, 25.0)
    z_profit = df["Z_Profit"].to_numpy(dtype=float) if "Z_Profit" in df.columns else np.full(n, 30.0)
    x70 = df["X70"].to_numpy(dtype=float) if "X70" in df.columns else np.full(n, 15.0)
    
    if "Y_Overlap" in df.columns:
        y_ovp = df["Y_Overlap"].to_numpy(dtype=float)
    elif "Overlap_Y" in df.columns:
        y_ovp = df["Overlap_Y"].to_numpy(dtype=float)
    else:
        y_ovp = np.full(n, 20.0)

    lfs = df["LFS"].to_numpy(dtype=float) if "LFS" in df.columns else np.clip(100.0 - asr * 0.85, 5.0, 95.0)
    hccyf = df["HCCYF13"].to_numpy(dtype=float) if "HCCYF13" in df.columns else pd.Series(lfs).rolling(13, min_periods=1).mean().to_numpy()

    # CYC 均线群
    if "CYC5" in df.columns:
        cyc5 = df["CYC5"].to_numpy(dtype=float)
    else:
        cyc5 = pd.Series(close).ewm(span=5).mean().to_numpy()

    if "CYC13" in df.columns:
        cyc13 = df["CYC13"].to_numpy(dtype=float)
    else:
        cyc13 = pd.Series(close).ewm(span=13).mean().to_numpy()

    if "CYC34" in df.columns:
        cyc34 = df["CYC34"].to_numpy(dtype=float)
    else:
        cyc34 = pd.Series(close).ewm(span=34).mean().to_numpy()

    if "CYC_Infinity" in df.columns:
        cyc_inf = df["CYC_Infinity"].to_numpy(dtype=float)
    elif "CYC_inf" in df.columns:
        cyc_inf = df["CYC_inf"].to_numpy(dtype=float)
    else:
        cyc_inf = pd.Series(close).expanding(min_periods=1).mean().to_numpy()

    # CYS 与 BIAS
    cys13 = (close - cyc13) / np.maximum(cyc13, 1e-4) * 100.0
    cys34 = (close - cyc34) / np.maximum(cyc34, 1e-4) * 100.0
    delta_cys = cys13 - cys34

    ma5 = pd.Series(close).rolling(5, min_periods=1).mean().to_numpy()
    ma20 = pd.Series(close).rolling(20, min_periods=1).mean().to_numpy()
    bias_5_20 = (ma5 - ma20) / np.maximum(ma20, 1e-4) * 100.0

    # 3. 高阶物理张量向量化计算
    cpr = (lfs * hccyf) / (np.maximum(asr, 1.0) * (1.0 + to / 100.0))
    pct_change = np.zeros(n)
    pct_change[1:] = (close[1:] - close[:-1]) / np.maximum(close[:-1], 1e-4) * 100.0
    eta_v = (pct_change * 100.0) / (np.maximum(to, 0.1) * np.maximum(asr, 1.0))
    bri = ((100.0 - y_ovp) * z_profit) / (np.maximum(x70, 0.5) * np.maximum(asr, 1.0))
    
    cyc_max = np.maximum(np.maximum(cyc5, cyc13), cyc34)
    cyc_min = np.minimum(np.minimum(cyc5, cyc13), cyc34)
    kappa_cyc = (cyc_max - cyc_min) / np.maximum(cyc_inf, 1e-4) * 100.0
    scissor = lfs - asr

    # 资金面
    main_pct = df["Main_Pct"].to_numpy(dtype=float) if "Main_Pct" in df.columns else (to * 0.4)
    dare_pct = df["Dare_Pct"].to_numpy(dtype=float) if "Dare_Pct" in df.columns else (to * 0.1)
    
    if "D_Pos" in df.columns:
        d_pos = df["D_Pos"].to_numpy(dtype=float)
    elif "D_pos" in df.columns:
        d_pos = df["D_pos"].to_numpy(dtype=float)
    else:
        d_pos = np.full(n, 35.0)

    smpi = (main_pct - dare_pct) / np.maximum(to, 0.1) * (1.0 - d_pos / 100.0)

    # 4. 四大激进前沿拓扑指标滑动解算 (Wasserstein W_cost, Kramers P_escape, Koopman DMD, TDA Beta_1)
    w_costs = np.zeros(n)
    p_escapes = np.zeros(n)
    dmd_scores = np.zeros(n)
    tda_ratios = np.zeros(n)

    l2_net = (main_pct - dare_pct) * 10.0

    for t in range(n):
        sub_close = close[max(0, t - 30): t + 1]
        sub_to = to[max(0, t - 30): t + 1]
        sub_l2 = l2_net[max(0, t - 30): t + 1]

        # Kramers 逃逸率
        high_barrier = float(np.max(sub_close))
        p_escapes[t] = advanced_pde.calc_kramers_escape_prob(sub_close, sub_to, high_barrier)

        # Koopman DMD 模态纯度
        dmd_scores[t], _ = advanced_pde.calc_koopman_dmd_mode(sub_close, sub_l2)

        # TDA 拓扑主轴比
        tda_ratios[t], _ = advanced_pde.calc_tda_topological_channel(sub_close, sub_to)

        # Wasserstein 做功
        if t < 2:
            w_costs[t] = 0.0
        else:
            p_grid = np.linspace(min(sub_close) * 0.9, max(sub_close) * 1.1, 25)
            m0 = np.mean(sub_close[:-1])
            s0 = np.std(sub_close[:-1]) + 1e-3
            m1 = sub_close[-1]
            s1 = np.std(sub_close[-3:]) + 1e-3
            c0 = np.exp(-0.5 * ((p_grid - m0) / s0) ** 2)
            c1 = np.exp(-0.5 * ((p_grid - m1) / s1) ** 2)
            w_costs[t] = advanced_pde.calc_wasserstein_work(p_grid, c0, c1)

    # CYF 动能
    cyf66_raw = pd.Series(lfs).rolling(66, min_periods=1).mean().to_numpy()
    vma55 = pd.Series(cyf66_raw).rolling(55, min_periods=1).mean().to_numpy()

    # 封装完整结果
    res_df = df.copy()
    res_df["Date_Disp"] = dates_disp
    res_df["Date_Full"] = dates_full
    res_df["Close"] = np.round(close, 2)
    res_df["CYC5"] = np.round(cyc5, 2)
    res_df["CYC13"] = np.round(cyc13, 2)
    res_df["CYC34"] = np.round(cyc34, 2)
    res_df["CYC_inf"] = np.round(cyc_inf, 2)
    res_df["W_cost"] = np.round(w_costs, 3)
    res_df["Z_Profit"] = np.round(z_profit, 1)
    res_df["ASR"] = np.round(asr, 1)
    res_df["P_escape"] = np.round(p_escapes, 1)
    res_df["BRI"] = np.round(bri, 1)
    res_df["LFS"] = np.round(lfs, 1)
    res_df["X70"] = np.round(x70, 1)
    res_df["Scissor"] = np.round(scissor, 1)
    res_df["CPR"] = np.round(cpr, 1)
    res_df["CYS13"] = np.round(cys13, 2)
    res_df["CYS34"] = np.round(cys34, 2)
    res_df["Delta_CYS"] = np.round(delta_cys, 2)
    res_df["BIAS_5_20"] = np.round(bias_5_20, 2)
    res_df["Kappa_CYC"] = np.round(kappa_cyc, 2)
    res_df["Eta_V"] = np.round(eta_v, 4)
    res_df["DMD_Score"] = np.round(dmd_scores, 1)
    res_df["TDA_Ratio"] = np.round(tda_ratios, 2)
    res_df["SMPI"] = np.round(smpi, 2)
    res_df["CYF66_Raw"] = np.round(cyf66_raw, 1)
    res_df["VMA55"] = np.round(vma55, 1)
    res_df["Delta_CYF"] = np.round(cyf66_raw - vma55, 1)
    res_df["Main_Pct"] = np.round(main_pct, 2)
    res_df["Dare_Pct"] = np.round(dare_pct, 2)
    res_df["D_Pos"] = np.round(d_pos, 1)
    res_df["Turnover"] = np.round(to, 2)

    return res_df


def build_quantum_physics_figure(df_input: Any, stock_name: str) -> go.Figure:
    """
    构建 5 层多维物理拓扑连续场 Figure。
    """
    df = compute_quantum_physics_series(df_input)
    n = len(df)
    x = list(range(n))
    dates_disp = df["Date_Disp"].tolist()
    dates_full = df["Date_Full"].tolist()

    WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    hover_labels = []
    for i, d in enumerate(dates_full):
        try:
            dt = datetime.strptime(str(d), "%Y-%m-%d")
            wd = WEEKDAYS[dt.weekday()]
        except Exception:
            wd = ""
        hover_labels.append(f"#{i} | {d} ({wd})")

    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.032,
        row_heights=[0.24, 0.20, 0.19, 0.19, 0.18],
        specs=[
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
            [{"secondary_y": True}],
        ],
        subplot_titles=[
            "① 空间引力与推土做功 (左: CYC均线·收盘价 | 右: W_cost 做功能量)",
            "② 势阱相变与断层真空 (左: Z'获利·ASR活筹·P_esc逃逸率 | 右: BRI 断层真空)",
            "③ 筹码刚性与护城剪刀差 (左: LFS锁仓·X70集中·Scissor剪刀差 | 右: CPR 刚性度)",
            "④ 盈亏张力与张力收敛 (左: CYS13/34·ΔCYS剪刀差 | 右: κCYC 斐波收敛)",
            "⑤ 量子相干与战略动能 (左: DMD相干模态纯度·β1拓扑射流 | 右: CYF66战略动能)",
        ]
    )

    # ══════════════════════════════════════════
    # Row 1: 空间引力与推土做功
    # ══════════════════════════════════════════
    # CYC 均线群
    fig.add_trace(go.Scatter(
        x=x, y=df["CYC5"], mode="lines", name="CYC5(天蓝)",
        line=dict(color=P_COLORS["cyc5"], width=1.1),
        hovertemplate="CYC5: %{y:.2f}<extra></extra>"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=x, y=df["CYC13"], mode="lines", name="CYC13(琥珀)",
        line=dict(color=P_COLORS["cyc13"], width=1.3),
        hovertemplate="CYC13: %{y:.2f}<extra></extra>"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=x, y=df["CYC34"], mode="lines", name="CYC34(紫)",
        line=dict(color=P_COLORS["cyc34"], width=1.5),
        hovertemplate="CYC34: %{y:.2f}<extra></extra>"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=x, y=df["CYC_inf"], mode="lines", name="CYC_inf(质心)",
        line=dict(color=P_COLORS["cyc_inf"], width=1.0, dash="dash"),
        hovertemplate="CYC_inf: %{y:.2f}<extra></extra>"
    ), row=1, col=1, secondary_y=False)

    # 收盘价
    fig.add_trace(go.Scatter(
        x=x, y=df["Close"], mode="lines", name="Close(收盘)",
        line=dict(color=P_COLORS["price"], width=1.8),
        hovertemplate="收盘价: %{y:.2f}<extra></extra>"
    ), row=1, col=1, secondary_y=False)

    # 右轴: W_cost 做功能量 (元/股) 柱状图
    w_colors = ["rgba(16, 185, 129, 0.7)" if w >= 0.4 else "rgba(16, 185, 129, 0.3)" for w in df["W_cost"]]
    fig.add_trace(go.Bar(
        x=x, y=df["W_cost"], name="W_cost做功",
        marker=dict(color=w_colors, line=dict(color="#10B981", width=0.8)),
        width=0.5,
        hovertemplate="W_cost(搬运功): %{y:.3f} 元/股<extra></extra>"
    ), row=1, col=1, secondary_y=True)

    # ══════════════════════════════════════════
    # Row 2: 势阱相变与断层真空
    # ══════════════════════════════════════════
    # Z_Profit 获利盘 (金色区域)
    fig.add_trace(go.Scatter(
        x=x, y=df["Z_Profit"], mode="lines", name="Z'获利盘",
        line=dict(color=P_COLORS["z_profit"], width=1.6),
        fill="tozeroy", fillcolor="rgba(251, 191, 36, 0.08)",
        hovertemplate="Z_Profit: %{y:.1f}%<extra></extra>"
    ), row=2, col=1, secondary_y=False)

    # ASR 活动筹码
    fig.add_trace(go.Scatter(
        x=x, y=df["ASR"], mode="lines", name="ASR活筹",
        line=dict(color=P_COLORS["asr"], width=1.4),
        hovertemplate="ASR: %{y:.1f}%<extra></extra>"
    ), row=2, col=1, secondary_y=False)

    # P_escape 势阱逃逸概率 (相变绿)
    fig.add_trace(go.Scatter(
        x=x, y=df["P_escape"], mode="lines", name="P_esc逃逸率",
        line=dict(color=P_COLORS["p_escape"], width=2.2),
        hovertemplate="P_escape(势阱穿透): %{y:.1f}%<extra></extra>"
    ), row=2, col=1, secondary_y=False)

    # 逃逸警戒线 75%
    fig.add_hline(y=75.0, line=dict(color="#10B981", width=1, dash="dash"), opacity=0.5, row=2, col=1)

    # 右轴: BRI 断层真空指数
    fig.add_trace(go.Scatter(
        x=x, y=df["BRI"], mode="lines", name="BRI真空走廊",
        line=dict(color=P_COLORS["bri"], width=1.6),
        hovertemplate="BRI(断层真空): %{y:.1f}<extra></extra>"
    ), row=2, col=1, secondary_y=True)
    fig.add_hline(y=30.0, line=dict(color="#C084FC", width=1, dash="dot"), opacity=0.4, row=2, col=1, secondary_y=True)

    # ══════════════════════════════════════════
    # Row 3: 筹码刚性与护城河剪刀差
    # ══════════════════════════════════════════
    # LFS 锁仓因子
    fig.add_trace(go.Scatter(
        x=x, y=df["LFS"], mode="lines", name="LFS锁仓底座",
        line=dict(color=P_COLORS["lfs"], width=2.0),
        hovertemplate="LFS: %{y:.1f}<extra></extra>"
    ), row=3, col=1, secondary_y=False)

    # X70 集中度
    fig.add_trace(go.Scatter(
        x=x, y=df["X70"], mode="lines", name="X70集中度",
        line=dict(color=P_COLORS["x70"], width=1.3),
        hovertemplate="X70: %{y:.1f}%<extra></extra>"
    ), row=3, col=1, secondary_y=False)

    # 剪刀差正负面积填充
    scissor_vals = df["Scissor"].tolist()
    sci_pos = [v if v >= 0 else 0 for v in scissor_vals]
    sci_neg = [v if v < 0 else 0 for v in scissor_vals]
    fig.add_trace(go.Scatter(
        x=x, y=sci_pos, mode="lines",
        line=dict(width=0), fill="tozeroy", fillcolor=P_COLORS["scissor_pos"],
        showlegend=False, hoverinfo="skip"
    ), row=3, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(
        x=x, y=sci_neg, mode="lines",
        line=dict(width=0), fill="tozeroy", fillcolor=P_COLORS["scissor_neg"],
        showlegend=False, hoverinfo="skip"
    ), row=3, col=1, secondary_y=False)

    # 右轴: CPR 筹码刚性度
    fig.add_trace(go.Scatter(
        x=x, y=df["CPR"], mode="lines", name="CPR刚性度",
        line=dict(color=P_COLORS["cpr"], width=2.0),
        hovertemplate="CPR: %{y:.1f}<extra></extra>"
    ), row=3, col=1, secondary_y=True)
    fig.add_hline(y=25.0, line=dict(color="#F43F5E", width=1.2, dash="dash"), opacity=0.6, row=3, col=1, secondary_y=True)

    # ══════════════════════════════════════════
    # Row 4: 盈亏张力与斐波收敛
    # ══════════════════════════════════════════
    # CYS13 & CYS34
    fig.add_trace(go.Scatter(
        x=x, y=df["CYS13"], mode="lines", name="CYS13短线盈亏",
        line=dict(color=P_COLORS["cys13"], width=1.2),
        hovertemplate="CYS13: %{y:+.2f}%<extra></extra>"
    ), row=4, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=x, y=df["CYS34"], mode="lines", name="CYS34中线盈亏",
        line=dict(color=P_COLORS["cys34"], width=1.5),
        hovertemplate="CYS34: %{y:+.2f}%<extra></extra>"
    ), row=4, col=1, secondary_y=False)

    # 盈亏剪刀差 ΔCYS 柱状图
    dcys_colors = [P_COLORS["delta_cys_pos"] if v >= 0 else P_COLORS["delta_cys_neg"] for v in df["Delta_CYS"]]
    fig.add_trace(go.Bar(
        x=x, y=df["Delta_CYS"], name="ΔCYS剪刀差",
        marker=dict(color=dcys_colors, opacity=0.75),
        width=0.45,
        hovertemplate="ΔCYS(剪刀差): %{y:+.2f}%<extra></extra>"
    ), row=4, col=1, secondary_y=False)

    # 零轴
    fig.add_hline(y=0.0, line=dict(color="rgba(255,255,255,0.2)", width=0.8), row=4, col=1)

    # 右轴: κCYC 斐波张力收敛度
    fig.add_trace(go.Scatter(
        x=x, y=df["Kappa_CYC"], mode="lines", name="κCYC斐波收敛",
        line=dict(color=P_COLORS["kappa_cyc"], width=1.4),
        hovertemplate="κCYC(张力收敛): %{y:.2f}%<extra></extra>"
    ), row=4, col=1, secondary_y=True)
    fig.add_hline(y=2.0, line=dict(color="#84CC16", width=1, dash="dot"), opacity=0.5, row=4, col=1, secondary_y=True)

    # ══════════════════════════════════════════
    # Row 5: 量子相干模态与资金流向
    # ══════════════════════════════════════════
    # DMD 模态纯度
    fig.add_trace(go.Scatter(
        x=x, y=df["DMD_Score"], mode="lines", name="DMD相干模态",
        line=dict(color=P_COLORS["dmd"], width=2.2),
        hovertemplate="DMD相干纯度: %{y:.1f}分<extra></extra>"
    ), row=5, col=1, secondary_y=False)
    fig.add_hline(y=80.0, line=dict(color="#A855F7", width=1, dash="dash"), opacity=0.4, row=5, col=1)

    # TDA 拓扑主轴比 (映射到同一子图左轴便于对比)
    fig.add_trace(go.Scatter(
        x=x, y=df["TDA_Ratio"] * 15.0, mode="lines", name="β1拓扑射流(x15)",
        line=dict(color=P_COLORS["tda"], width=1.4),
        hovertemplate="β1拓扑比: %{customdata:.2f}<extra></extra>",
        customdata=df["TDA_Ratio"]
    ), row=5, col=1, secondary_y=False)

    # 右轴: CYF66 动能势能
    fig.add_trace(go.Scatter(
        x=x, y=df["CYF66_Raw"], mode="lines", name="CYF66动能",
        line=dict(color=P_COLORS["cyf66"], width=1.4),
        hovertemplate="CYF66: %{y:.1f}<extra></extra>"
    ), row=5, col=1, secondary_y=True)

    fig.add_trace(go.Scatter(
        x=x, y=df["VMA55"], mode="lines", name="VMA55基线",
        line=dict(color=P_COLORS["vma55"], width=1.1, dash="dash"),
        hovertemplate="VMA55: %{y:.1f}<extra></extra>"
    ), row=5, col=1, secondary_y=True)

    # ══════════════════════════════════════════
    # 统一 Layout 战术暗黑配置
    # ══════════════════════════════════════════
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=PANEL_COLOR,
        height=820,
        margin=dict(l=55, r=55, t=35, b=30),
        showlegend=False,
        hovermode="x unified",
    )

    # 缩小子图标题字体至 11px，沉稳内敛不喧宾夺主
    fig.for_each_annotation(lambda a: a.update(
        font=dict(size=11, color="#94A3B8"),
        xanchor="left",
        x=0.012
    ))

    # 统一刻度风格
    for row_idx in range(1, 6):
        fig.update_xaxes(
            gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
            tickfont=dict(size=9, color=MUTE_COLOR),
            row=row_idx, col=1
        )
        fig.update_yaxes(
            gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR,
            tickfont=dict(size=9, color=MUTE_COLOR),
            ticks="outside", ticklen=3,
            row=row_idx, col=1, secondary_y=False
        )
        fig.update_yaxes(
            showgrid=False, zerolinecolor="rgba(0,0,0,0)",
            tickfont=dict(size=9, color=MUTE_COLOR),
            ticks="outside", ticklen=3,
            row=row_idx, col=1, secondary_y=True
        )

    # 最底排 X 轴显示真实日期标签
    step = max(1, n // 10)
    tickvals = list(range(0, n, step))
    if n - 1 not in tickvals:
        tickvals.append(n - 1)
    ticktext = [dates_disp[i] for i in tickvals]

    fig.update_xaxes(
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        row=5, col=1
    )

    return fig


def render_quantum_physics_with_hud(
    fig: go.Figure,
    df_input: Any,
    stock_name: str,
    height: int = 820
):
    """
    将 18 物理真值量子图表与右侧 HUD 悬浮面板打包成一体化 Streamlit 前端组件。
    纯前端 JavaScript 毫秒级准星交互，零延迟，零额外服务器开销。
    """
    df_pd = compute_quantum_physics_series(df_input)
    fig_json = fig.to_json()

    # 导出 HUD 需要的 JSON 列
    hud_cols = [
        "Date_Full", "Date_Disp", "Close", "Turnover",
        "CYC5", "CYC13", "CYC34", "CYC_inf", "W_cost",
        "Z_Profit", "ASR", "P_escape", "BRI",
        "LFS", "X70", "Scissor", "CPR",
        "CYS13", "CYS34", "Delta_CYS", "BIAS_5_20", "Kappa_CYC", "Eta_V",
        "DMD_Score", "TDA_Ratio", "SMPI", "CYF66_Raw", "VMA55", "Delta_CYF",
        "Main_Pct", "Dare_Pct", "D_Pos"
    ]
    existing_cols = [c for c in hud_cols if c in df_pd.columns]
    rows_data = df_pd[existing_cols].to_dict(orient="records")
    rows_json = json.dumps(rows_data, ensure_ascii=False, default=str)
    total = len(rows_data)

    html_code = f"""
    <div id="quantum-root" style="display:flex; gap:10px; height:{height}px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', sans-serif;">
        <div id="quantum-chart" style="flex:5; min-width:0;"></div>
        <div id="quantum-hud" style="flex:1.35; overflow-y:auto; font-size:11.5px; color:#E2E8F0; padding-right:4px;">
            <div id="qhud-header" class="qcard"></div>
            <div id="qhud-status" class="qcard" style="border-left:3px solid #10B981;"></div>
            <div id="qhud-p1" class="qcard"></div>
            <div id="qhud-p2" class="qcard"></div>
            <div id="qhud-p3" class="qcard"></div>
            <div id="qhud-p4" class="qcard"></div>
            <div id="qhud-p5" class="qcard"></div>
        </div>
    </div>

    <style>
    #quantum-root .qcard {{
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85));
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 6px;
        padding: 6px 8px;
        margin-bottom: 5px;
    }}
    #quantum-root .qtitle {{
        color: #94A3B8;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 3px;
        padding-bottom: 2px;
        border-bottom: 1px dashed rgba(255,255,255,0.1);
        display: flex;
        justify-content: space-between;
    }}
    #quantum-root .qrow {{
        display: flex;
        justify-content: space-between;
        padding: 1.5px 0;
        font-size: 11px;
    }}
    #quantum-root .ql {{
        color: #94A3B8;
        font-weight: 500;
    }}
    #quantum-root .qv {{
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }}
    </style>

    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <script>
    (function() {{
        const figData = {fig_json};
        const allRows = {rows_json};
        const stockName = "{stock_name}";
        const total = {total};
        const chartDiv = document.getElementById('quantum-chart');

        if (!figData.layout.shapes) figData.layout.shapes = [];
        figData.layout.shapes.push({{
            type: 'line', x0: 0, x1: 0, y0: 0, y1: 1,
            xref: 'x', yref: 'paper',
            line: {{ color: '#38BDF8', width: 1.2, dash: 'dot' }},
            opacity: 0, name: 'crosshair'
        }});

        Plotly.newPlot(chartDiv, figData.data, figData.layout, {{
            displayModeBar: false, responsive: true
        }});

        chartDiv.on('plotly_hover', function(ev) {{
            if (!ev || !ev.points || !ev.points.length) return;
            const pt = ev.points[0];
            const idx = Math.round(pt.x);
            if (idx < 0 || idx >= total) return;

            const shapes = chartDiv.layout.shapes.map((s, i) => {{
                if (i === chartDiv.layout.shapes.length - 1) {{
                    return Object.assign({{}}, s, {{ x0: idx, x1: idx, opacity: 0.85 }});
                }}
                return s;
            }});
            Plotly.relayout(chartDiv, {{ shapes }});

            updateQuantumHUD(idx);
        }});

        chartDiv.on('plotly_unhover', function() {{
            const shapes = chartDiv.layout.shapes.map((s, i) => {{
                if (i === chartDiv.layout.shapes.length - 1) return Object.assign({{}}, s, {{ opacity: 0 }});
                return s;
            }});
            Plotly.relayout(chartDiv, {{ shapes }});
        }});

        // 初始化加载最新日
        updateQuantumHUD(total - 1);

        function fmt(v, digits=2, sign=false) {{
            if (v == null || isNaN(v)) return '-';
            let num = Number(v);
            let s = num.toFixed(digits);
            if (sign && num > 0) s = '+' + s;
            return s;
        }}

        function updateQuantumHUD(idx) {{
            const d = allRows[idx];
            if (!d) return;

            // 1. 顶部标的与日期
            document.getElementById('qhud-header').innerHTML = `
                <div class="qtitle"><span>🛸 物理连续场 · 空间真值</span><span>#${{idx+1}}/${{total}}</span></div>
                <div style="font-size:13px; font-weight:800; color:#38BDF8; margin-bottom:2px;">${{stockName}}</div>
                <div style="display:flex; justify-content:space-between; font-size:11px; color:#CBD5E1;">
                    <span>${{d.Date_Full||d.Date_Disp||''}}</span>
                    <span>价: <b style="color:#FFF;">${{fmt(d.Close, 2)}}</b> (换手: <b style="color:#FBBF24;">${{fmt(d.Turnover, 2)}}%</b>)</span>
                </div>
            `;

            // 2. 战场物理微积分多维综合裁决与多重打分
            const cpr = Number(d.CPR || 0);
            const pesc = Number(d.P_escape || 0);
            const dmd = Number(d.DMD_Score || 0);
            const wcost = Number(d.W_cost || 0);
            const cys34 = Number(d.CYS34 || 0);
            const dcys = Number(d.Delta_CYS || 0);
            const kcyc = Number(d.Kappa_CYC || 0);
            const bri = Number(d.BRI || 0);
            const lfs = Number(d.LFS || 0);
            const asr = Number(d.ASR || 0);
            const tda = Number(d.TDA_Ratio || 0);
            const smpi = Number(d.SMPI || 0);
            const scissor = Number(d.Scissor || 0);

            // 科学量化打分 (100分制)
            let s_esc = pesc >= 75 ? 25 : (pesc >= 50 ? 18 : (pesc >= 25 ? 10 : 5));
            let s_work = wcost >= 1.0 ? 20 : (wcost >= 0.4 ? 16 : (wcost >= 0.1 ? 11 : 6));
            let s_cpr = cpr >= 25 ? 25 : (cpr >= 15 ? 20 : (cpr >= 8 ? 13 : 4));
            let s_dmd = dmd >= 80 ? 15 : (dmd >= 60 ? 11 : (dmd >= 40 ? 7 : 3));
            let s_vac = (bri >= 25 ? 8 : (bri >= 12 ? 5 : 2)) + (kcyc <= 2.5 ? 7 : (kcyc <= 5 ? 4 : 2));
            let totalScore = Math.min(99.0, Math.max(12.0, s_esc + s_work + s_cpr + s_dmd + s_vac));

            // 指令判定与战术评级
            let orderTag = "🛡️【底座防御蓄势令】";
            let orderColor = "#38BDF8";
            let orderDesc = "筹码微积分场常态运行，主力底座坚固，维持纪律底仓。";

            if (totalScore >= 80 && cpr >= 25) {{
                orderTag = "👑【超导主升猛攻令】";
                orderColor = "#10B981";
                orderDesc = "筹码超导绝对死锁，势垒全维穿透，主力强相干同相暴拉！";
            }} else if (totalScore >= 70 || (pesc >= 75 && wcost >= 0.35)) {{
                orderTag = "🚀【势垒穿透突击令】";
                orderColor = "#10B981";
                orderDesc = "福克-普朗克势阱成功穿透，真实推土做功确立，发起一类突击！";
            }} else if (cys34 <= -8 && dcys > 0) {{
                orderTag = "💎【战略黄金坑伏击令】";
                orderColor = "#F59E0B";
                orderDesc = "短中期盈亏剪刀差向上金叉，极端超卖出清，绝佳逆向买点！";
            }} else if (cpr < 8 && asr > 50) {{
                orderTag = "⚠️【浮筹溃散撤退令】";
                orderColor = "#EF4444";
                orderDesc = "活动浮筹激增失控，底座严重溃散，严禁追高防范主力对倒出逃！";
            }}

            function lgt(cond, text) {{
                return cond ? `<span style="color:#10B981;">🟢 ${{text}}</span>` : `<span style="color:#EF4444;">🔴 ${{text}}</span>`;
            }}
            function lgt3(v, gThresh, yThresh, gText, yText, rText) {{
                if (v >= gThresh) return `<span style="color:#10B981;">🟢 ${{gText}}</span>`;
                if (v >= yThresh) return `<span style="color:#FBBF24;">🟡 ${{yText}}</span>`;
                return `<span style="color:#EF4444;">🔴 ${{rText}}</span>`;
            }}

            const sCard = document.getElementById('qhud-status');
            sCard.style.borderLeftColor = orderColor;
            sCard.innerHTML = `
                <div class="qtitle" style="color:${{orderColor}};">
                    <span>⚔️ 全息物理综合裁决</span>
                    <span style="font-size:12px; font-weight:900; color:${{orderColor}};">${{totalScore.toFixed(1)}}分</span>
                </div>
                <div style="font-size:12px; font-weight:800; color:${{orderColor}}; margin:3px 0 2px 0;">${{orderTag}}</div>
                <div style="font-size:9.5px; color:#94A3B8; line-height:1.3; margin-bottom:5px;">${{orderDesc}}</div>
                
                <div style="height:4px; background:rgba(255,255,255,0.1); border-radius:2px; overflow:hidden; margin-bottom:5px;">
                    <div style="height:100%; width:${{totalScore}}%; background:${{orderColor}};"></div>
                </div>

                <div style="font-size:9.5px; background:rgba(0,0,0,0.3); border-radius:4px; padding:3px 5px;">
                    <div class="qrow">
                        <span class="ql">势垒相变:</span>
                        <span>${{lgt3(pesc, 75, 45, '相变穿透', '临界蓄势', '势阱受阻')}} (${{pesc.toFixed(1)}}%)</span>
                    </div>
                    <div class="qrow">
                        <span class="ql">筹码刚性:</span>
                        <span>${{lgt3(cpr, 25, 12, '超导死锁', '底座稳固', '筹码溃散')}} (CPR ${{cpr.toFixed(1)}})</span>
                    </div>
                    <div class="qrow">
                        <span class="ql">推土做功:</span>
                        <span>${{lgt3(wcost, 0.4, 0.1, '单向做功', '温和搬砖', '无位移')}} (${{wcost.toFixed(2)}}元)</span>
                    </div>
                    <div class="qrow">
                        <span class="ql">相干模态:</span>
                        <span>${{lgt3(dmd, 70, 45, '机构强控', '弱相干态', '耗散对倒')}} (${{dmd.toFixed(1)}}分)</span>
                    </div>
                    <div class="qrow">
                        <span class="ql">盈亏剪刀:</span>
                        <span>${{lgt(dcys > 0, dcys > 0 ? '多头加速' : '空头承压')}} (${{dcys > 0 ? '+' : ''}}${{dcys.toFixed(1)}}%)</span>
                    </div>
                    <div class="qrow">
                        <span class="ql">断层真空:</span>
                        <span>${{lgt3(bri, 25, 12, '真空走廊', '常规通道', '重叠阻滞')}} (BRI ${{bri.toFixed(1)}})</span>
                    </div>
                </div>
            `;

            // 3. 维度一: 引力做功
            document.getElementById('qhud-p1').innerHTML = `
                <div class="qtitle"><span style="color:#38BDF8;">① 空间引力与推土功</span></div>
                <div class="qrow"><span class="ql">W_cost(推土做功):</span><span class="qv" style="color:#10B981;">${{fmt(d.W_cost, 3)}} 元/股</span></div>
                <div class="qrow"><span class="ql">CYC5 / CYC13:</span><span class="qv">${{fmt(d.CYC5)}} / ${{fmt(d.CYC13)}}</span></div>
                <div class="qrow"><span class="ql">CYC34 / CYC_inf:</span><span class="qv">${{fmt(d.CYC34)}} / ${{fmt(d.CYC_inf)}}</span></div>
            `;

            // 4. 维度二: 势阱真空
            document.getElementById('qhud-p2').innerHTML = `
                <div class="qtitle"><span style="color:#FBBF24;">② 势阱相变与断层真空</span></div>
                <div class="qrow"><span class="ql">P_escape(逃逸率):</span><span class="qv" style="color:${{pesc>=75?'#10B981':'#F59E0B'}};">${{fmt(d.P_escape, 1)}}%</span></div>
                <div class="qrow"><span class="ql">BRI(断层真空度):</span><span class="qv" style="color:#C084FC;">${{fmt(d.BRI, 1)}}</span></div>
                <div class="qrow"><span class="ql">Z'(获利盘) / ASR:</span><span class="qv" style="color:#FBBF24;">${{fmt(d.Z_Profit, 1)}}% / ${{fmt(d.ASR, 1)}}%</span></div>
            `;

            // 5. 维度三: 筹码刚性
            document.getElementById('qhud-p3').innerHTML = `
                <div class="qtitle"><span style="color:#F43F5E;">③ 筹码锁仓与微观刚性</span></div>
                <div class="qrow"><span class="ql">CPR(筹码刚性度):</span><span class="qv" style="color:${{cpr>=25?'#F43F5E':'#94A3B8'}};">${{fmt(d.CPR, 1)}}</span></div>
                <div class="qrow"><span class="ql">LFS(底座) / X70:</span><span class="qv" style="color:#3B82F6;">${{fmt(d.LFS, 1)}} / ${{fmt(d.X70, 1)}}%</span></div>
                <div class="qrow"><span class="ql">Scissor(剪刀差):</span><span class="qv" style="color:${{d.Scissor>=0?'#10B981':'#EF4444'}};">${{fmt(d.Scissor, 1, true)}}</span></div>
            `;

            // 6. 维度四: 盈亏张力
            document.getElementById('qhud-p4').innerHTML = `
                <div class="qtitle"><span style="color:#818CF8;">④ 盈亏剪刀差与均线偏离</span></div>
                <div class="qrow"><span class="ql">ΔCYS(剪刀差):</span><span class="qv" style="color:${{dcys>=0?'#10B981':'#EF4444'}};">${{fmt(d.Delta_CYS, 2, true)}}%</span></div>
                <div class="qrow"><span class="ql">CYS13 / CYS34:</span><span class="qv">${{fmt(d.CYS13, 2, true)}}% / ${{fmt(d.CYS34, 2, true)}}%</span></div>
                <div class="qrow"><span class="ql">κCYC(斐波收敛):</span><span class="qv" style="color:#84CC16;">${{fmt(d.Kappa_CYC, 2)}}%</span></div>
            `;

            // 7. 维度五: 量子相干与动能
            document.getElementById('qhud-p5').innerHTML = `
                <div class="qtitle"><span style="color:#A855F7;">⑤ 模态相干与拓扑射流</span></div>
                <div class="qrow"><span class="ql">DMD相干模态:</span><span class="qv" style="color:#A855F7;">${{fmt(d.DMD_Score, 1)}} 分</span></div>
                <div class="qrow"><span class="ql">β1拓扑主轴比:</span><span class="qv" style="color:#22D3EE;">${{fmt(d.TDA_Ratio, 2)}}</span></div>
                <div class="qrow"><span class="ql">SMPI / CYF66:</span><span class="qv" style="color:#EAB308;">${{fmt(d.SMPI, 2, true)}} / ${{fmt(d.CYF66_Raw, 1)}}</span></div>
            `;
        }}
    }})();
    </script>
    """

    components.html(html_code, height=height, scrolling=False)
