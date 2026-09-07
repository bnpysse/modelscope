# -*- coding: utf-8 -*-
"""
天衍五维 · 前沿试验台高频分时与相空间可视化组件
文件位置: core/components/physics_lab_chart.py
"""

import json
import urllib.request
from typing import Dict, Any, List, Optional
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def fetch_realtime_intraday_bars(code_str: str) -> List[Dict[str, Any]]:
    """
    拉取标的今日实盘 1 分钟线高频分时数据 (腾讯高速行情接口，0 延迟直通)
    返回: [{'time': 'HH:MM', 'price': float, 'volume': float, 'avg_price': float}, ...]
    """
    prefix = "sh" if code_str.startswith(("6", "9")) else "sz"
    url = f"https://web.ifzq.gtimg.cn/appstock/app/minute/query?code={prefix}{code_str}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            raw_list = data.get("data", {}).get(f"{prefix}{code_str}", {}).get("data", {}).get("data", [])
            if not raw_list:
                return []
            
            bars = []
            prev_vol = 0.0
            cum_turnover = 0.0
            cum_vol_total = 0.0
            for r in raw_list:
                parts = r.split()
                if len(parts) >= 3:
                    time_raw = parts[0]
                    price = float(parts[1])
                    cum_vol = float(parts[2])
                    bar_vol = max(0.0, cum_vol - prev_vol)
                    prev_vol = cum_vol
                    
                    cum_vol_total += bar_vol
                    cum_turnover += (price * bar_vol)
                    avg_p = (cum_turnover / cum_vol_total) if cum_vol_total > 0 else price
                    
                    bars.append({
                        "time": f"{time_raw[:2]}:{time_raw[2:]}",
                        "price": price,
                        "volume": bar_vol,
                        "avg_price": round(avg_p, 3)
                    })
            return bars
    except Exception:
        return []


def build_physics_lab_charts(
    stock_code: str,
    stock_name: str,
    prices: np.ndarray,
    volumes: np.ndarray,
    high_barrier: float,
    w_cost: float,
    p_escape: float,
    tda_ratio: float
) -> tuple[go.Figure, go.Figure]:
    """
    构建试验台双核高科技物理图表:
    1. fig_intraday: 今日实盘高频分时与微观势流 (带黄白线、均价线、最高势垒阻力线、推土功支撑位)
    2. fig_phase: 高维相空间拓扑相轨图 (Phase Space Portrait - 动量/速度极限环 vs 主升发散)
    """
    # ── 1. 高频分时图 ──
    intraday_data = fetch_realtime_intraday_bars(stock_code)
    
    fig_intraday = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.72, 0.28],
        subplot_titles=(
            f"⚡ 今日实盘微观分时势流 (势垒高度: {high_barrier:.2f} | 推土功: {w_cost:.3f}元/股)",
            "📊 分时脉冲成交量"
        )
    )

    if intraday_data:
        times = [b["time"] for b in intraday_data]
        m_prices = [b["price"] for b in intraday_data]
        m_avgs = [b["avg_price"] for b in intraday_data]
        m_vols = [b["volume"] for b in intraday_data]
        
        # 现价走势 (纯白科技流)
        fig_intraday.add_trace(
            go.Scatter(
                x=times, y=m_prices,
                mode="lines",
                name="实时分时价",
                line=dict(color="#F8FAFC", width=2),
                hovertemplate="时间: %{x}<br>现价: %{y:.2f}元<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 均价线 (亮黄)
        fig_intraday.add_trace(
            go.Scatter(
                x=times, y=m_avgs,
                mode="lines",
                name="全天均价线",
                line=dict(color="#FBBF24", width=1.5, dash="dot"),
                hovertemplate="时间: %{x}<br>均价: %{y:.2f}元<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 势垒警戒光带 (阻力位)
        fig_intraday.add_hline(
            y=high_barrier,
            line=dict(color="#EF4444", width=1.5, dash="dash"),
            annotation_text=f"福克-普朗克势垒顶: {high_barrier:.2f}元",
            annotation_position="top right",
            annotation_font=dict(size=10, color="#F87171"),
            row=1, col=1
        )
        
        # 最优传输推土支撑带
        support_level = min(m_prices) * 0.99 if m_prices else high_barrier * 0.95
        fig_intraday.add_hline(
            y=support_level,
            line=dict(color="#10B981", width=1.2, dash="dashdot"),
            annotation_text=f"最优传输势能底: {support_level:.2f}元",
            annotation_position="bottom right",
            annotation_font=dict(size=10, color="#34D399"),
            row=1, col=1
        )

        # 量能柱
        vol_colors = ["#10B981" if m_prices[i] >= m_avgs[i] else "#EF4444" for i in range(len(m_prices))]
        fig_intraday.add_trace(
            go.Bar(
                x=times, y=m_vols,
                name="分时成交",
                marker_color=vol_colors,
                opacity=0.75,
                hovertemplate="成交: %{y}<extra></extra>"
            ),
            row=2, col=1
        )
    else:
        # 无分时时的温和占位
        fig_intraday.add_annotation(
            text="盘中休市或等待分时接入",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#64748B")
        )

    fig_intraday.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.75)",
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        margin=dict(l=40, r=40, t=40, b=30),
        height=380,
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        xaxis2=dict(showgrid=False),
        yaxis2=dict(showgrid=False)
    )

    # ── 2. 高维相空间拓扑相轨图 (Phase Space Portrait) ──
    # 横轴: 价格 P(t), 纵轴: 动量速率 dP/dt
    # 计算一阶差分与平滑动量
    p_series = np.array(prices, dtype=float)
    if len(p_series) >= 10:
        dp = np.gradient(p_series)
        acc = np.gradient(dp)
    else:
        dp = np.zeros_like(p_series)
        acc = np.zeros_like(p_series)

    # 渐变色时间步 (早期灰蓝 -> 最新亮青/亮紫)
    n_points = len(p_series)
    color_steps = np.linspace(0, 1, n_points)

    fig_phase = go.Figure()

    # 绘制相轨迹连续曲线
    fig_phase.add_trace(
        go.Scatter(
            x=p_series,
            y=dp,
            mode="lines+markers",
            name="相轨流线",
            line=dict(color="#38BDF8", width=2),
            marker=dict(
                size=6,
                color=color_steps,
                colorscale="Viridis",
                showscale=False
            ),
            hovertemplate="价格位 P: %{x:.2f}<br>动量流速 dP/dt: %{y:.3f}<extra></extra>"
        )
    )

    # 标注当前最新相点
    if len(p_series) > 0:
        fig_phase.add_trace(
            go.Scatter(
                x=[p_series[-1]],
                y=[dp[-1]],
                mode="markers+text",
                name="当前相空间坐标",
                marker=dict(size=14, color="#EF4444", symbol="star"),
                text=["🎯 最新相点"],
                textposition="top center",
                textfont=dict(color="#F87171", size=11, family="monospace")
            )
        )

    # 零动量平衡轴线
    fig_phase.add_hline(y=0, line=dict(color="rgba(255,255,255,0.15)", width=1, dash="dot"))

    fig_phase.update_layout(
        title=f"🌀 高维相空间拓扑相轨 (主轴比 β1: {tda_ratio:.2f} | 逃逸率: {p_escape:.1f}%)",
        title_font=dict(size=13, color="#38BDF8"),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.75)",
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        margin=dict(l=40, r=40, t=40, b=30),
        height=380,
        showlegend=False,
        xaxis=dict(
            title="价格势能位 P(t)",
            title_font=dict(size=11, color="#94A3B8"),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)"
        ),
        yaxis=dict(
            title="动量流速 dP/dt",
            title_font=dict(size=11, color="#94A3B8"),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)"
        )
    )

    return fig_intraday, fig_phase
