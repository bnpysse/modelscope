# -*- coding: utf-8 -*-
"""
天衍五维 · AI 哨兵前向跟踪与趋势验证独立总台 (V2.0 独立一级导航页面)
文件位置: pages/05_🔭_哨兵前向跟踪.py
"""

import sys
import json
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent if (CURRENT_FILE.parent / "core").exists() else (CURRENT_FILE.parent.parent if (CURRENT_FILE.parent.parent / "core").exists() else CURRENT_FILE.parent.parent.parent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import numpy as np
import pandas as pd

from tianyan_v2.shared import (
    get_tianyan_engine,
    apply_tactical_theme,
    render_top_control_bar
)
from core.forward_sentinel_tracker import sentinel_tracker, extract_daily_top_picks_from_snapshot
from core.components.report_sanitizer import sanitize_ai_report_markdown

st.set_page_config(
    page_title="天衍五维 · AI 哨兵前向跟踪与战法归因",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_tactical_theme()

# 注入针对前向研报排版的精细化高清晰度 CSS
st.markdown("""
<style>
/* 研报全局排版与字体紧凑度优化 */
.stMarkdown h1, .stMarkdown [data-testid="stMarkdownContainer"] h1 {
    font-size: 20px !important;
    font-weight: 800 !important;
    color: #38BDF8 !important;
    margin-top: 14px !important;
    margin-bottom: 8px !important;
    letter-spacing: -0.01em !important;
}
.stMarkdown h2, .stMarkdown [data-testid="stMarkdownContainer"] h2 {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
    margin-top: 16px !important;
    margin-bottom: 8px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding-bottom: 4px !important;
}
.stMarkdown h3, .stMarkdown [data-testid="stMarkdownContainer"] h3 {
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #93C5FD !important;
    margin-top: 12px !important;
    margin-bottom: 6px !important;
}
.stMarkdown h4, .stMarkdown [data-testid="stMarkdownContainer"] h4 {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #CBD5E1 !important;
    margin-top: 8px !important;
    margin-bottom: 4px !important;
}
.stMarkdown p, .stMarkdown li, .stMarkdown [data-testid="stMarkdownContainer"] p, .stMarkdown [data-testid="stMarkdownContainer"] li {
    font-size: 12.5px !important;
    line-height: 1.65 !important;
    color: #E2E8F0 !important;
}
.stMarkdown blockquote {
    font-size: 12px !important;
    background: rgba(15, 23, 42, 0.6) !important;
    border-left: 3px solid #38BDF8 !important;
    padding: 6px 12px !important;
    border-radius: 4px !important;
    color: #94A3B8 !important;
    margin: 8px 0 !important;
}

/* 研报战术表格高级渲染 (深色科技风 + 完美对齐 + 斑马纹) */
.stMarkdown table, [data-testid="stMarkdownContainer"] table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 10px 0 16px 0 !important;
    font-size: 12px !important;
    border-radius: 6px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background: rgba(15, 23, 42, 0.7) !important;
}
.stMarkdown th, [data-testid="stMarkdownContainer"] th {
    background: rgba(30, 41, 59, 0.9) !important;
    color: #38BDF8 !important;
    font-weight: 700 !important;
    padding: 8px 10px !important;
    text-align: left !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    font-size: 12px !important;
    white-space: nowrap !important;
}
.stMarkdown td, [data-testid="stMarkdownContainer"] td {
    padding: 6px 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    color: #F1F5F9 !important;
    font-size: 12px !important;
}
.stMarkdown tr:nth-child(even), [data-testid="stMarkdownContainer"] tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02) !important;
}
.stMarkdown tr:hover, [data-testid="stMarkdownContainer"] tr:hover {
    background: rgba(56, 189, 248, 0.08) !important;
}
</style>
""", unsafe_allow_html=True)

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import importlib
import core.sentiment_radar
importlib.reload(core.sentiment_radar)
from core.sentiment_radar import fetch_intraday_minute_chart


@st.dialog("📈 标的实时分时走势与量能全息透视", width="large")
def show_stock_intraday_modal(stock_code: str, stock_name: str = ""):
    """点击标的弹出的当日毫秒级实时分时行情全息弹窗"""
    with st.spinner(f"正在拉取 {stock_name}({stock_code}) 当日全部分时行情..."):
        info = fetch_intraday_minute_chart(stock_code)
    
    if "error" in info or not info.get("times"):
        st.warning(f"未能获取到 {stock_name} ({stock_code}) 的当日分时数据（可能是停牌或接口限制）。")
        return

    name = info.get("name") or stock_name
    prev_c = info.get("prev_close", 0.0)
    cur_p = info.get("latest_price", 0.0)
    pct = info.get("pct_chg", 0.0)
    high_p = info.get("high", 0.0)
    low_p = info.get("low", 0.0)
    vol_wan = round(info.get("volume", 0.0) / 10000.0, 1)
    amt_yi = round(info.get("amount", 0.0) / 100000000.0, 2)
    color = "#22C55E" if pct >= 0 else "#EF4444"

    # 顶栏实时指标卡
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("标的", f"{name}", f"{stock_code}")
    m2.metric("现价", f"¥{cur_p:.2f}", f"{pct:+.2f}%")
    m3.metric("昨收", f"¥{prev_c:.2f}")
    m4.metric("最高 / 最低", f"¥{high_p:.2f}", f"¥{low_p:.2f}")
    m5.metric("成交量", f"{vol_wan} 万股")
    m6.metric("成交额", f"{amt_yi} 亿元")

    # 绘制高科技深色分时图 (分时价格 + 分时均线 + 成交量)
    times = info.get("times", [])
    prices = info.get("prices", [])
    vwap = info.get("vwap", [])
    volumes = info.get("volumes", [])

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25]
    )

    # 1. 昨收基准虚线
    if prev_c > 0:
        fig.add_hline(
            y=prev_c, line_dash="dash", line_color="rgba(148, 163, 184, 0.5)",
            line_width=1, row=1, col=1
        )

    # 2. 分时现价曲线 (带半透明填充)
    fill_color = "rgba(34, 197, 94, 0.12)" if pct >= 0 else "rgba(239, 68, 68, 0.12)"
    line_color = "#22C55E" if pct >= 0 else "#EF4444"
    fig.add_trace(
        go.Scatter(
            x=times, y=prices,
            mode='lines',
            name='现价',
            line=dict(color=line_color, width=2),
            fill='tozeroy' if prev_c <= 0 else None,
            fillcolor=fill_color,
            hoverinfo='x+y'
        ),
        row=1, col=1
    )

    # 3. 分时 VWAP 均线 (黄色)
    if vwap and len(vwap) == len(times):
        fig.add_trace(
            go.Scatter(
                x=times, y=vwap,
                mode='lines',
                name='分时均价 (VWAP)',
                line=dict(color='#FACC15', width=1.5, dash='dot'),
                hoverinfo='x+y'
            ),
            row=1, col=1
        )

    # 4. 下方成交量柱状图
    vol_colors = []
    for i in range(len(prices)):
        if i == 0:
            vol_colors.append(line_color)
        else:
            vol_colors.append('#22C55E' if prices[i] >= prices[i-1] else '#EF4444')

    fig.add_trace(
        go.Bar(
            x=times, y=volumes,
            name='成交量 (股)',
            marker_color=vol_colors,
            opacity=0.8
        ),
        row=2, col=1
    )

    # 布局美化
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.8)",
        plot_bgcolor="rgba(15, 23, 42, 0.95)",
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis2=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.05)",
            nticks=8
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.08)",
            tickformat=".2f"
        ),
        yaxis2=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.05)",
            showticklabels=False
        )
    )

    st.plotly_chart(fig, use_container_width=True)


engine = get_tianyan_engine()

# 侧边栏
with st.sidebar:
    st.markdown("""
    <div style="padding: 4px 0 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px;">
        <span style="font-size: 14px; font-weight: 800; color: #38BDF8;">🔭 哨兵前向跟踪总台</span>
        <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">实战前向存证 · 选股原则深度归因</div>
    </div>
    """, unsafe_allow_html=True)
    st.info("追踪从 T+1 至 T+132 的真实涨跌幅与筹码演化。点击【🧠 召唤 32B 大脑深度复盘】可穿透哪些选股原则最具实战价值！")

# 顶部导航控制条
ctrl = render_top_control_bar(engine, title_prefix="🔭 天衍五维 · AI 哨兵前向跟踪与选股归因")

# ══════════════════════════════════════════════
# 模块 ①：顶栏战备动作与实时刷新
# ══════════════════════════════════════════════
c_title, c_actions = st.columns([6.0, 4.0])
with c_title:
    st.markdown("### 🔭 天衍 AI 哨兵前向跟踪与趋势验证台账")
    st.caption("🛡️ **前向实战闭环与中长期趋势验证**：每日四大战法 Top 标的自动建仓存证，追踪 **1个月 (T+22)、1季度 (T+66)、半年 (T+132)** 战略趋势的形成与筹码健康度。")


# 自动/手动刷新实时行情
with c_actions:
    col_act1, col_act2, col_act3 = st.columns([1.1, 1.1, 1.3])
    with col_act1:
        if st.button("⚡ 实时现价核算", help="直通腾讯行情接口，秒级刷新当前在踪标的的最新盘中现价与真实浮盈", use_container_width=True, type="primary"):
            from core import forward_sentinel_tracker
            import importlib
            importlib.reload(forward_sentinel_tracker)
            updated = forward_sentinel_tracker.sentinel_tracker.refresh_realtime_pnl()
            st.toast(f"✅ 成功刷新 {updated} 只在踪标的的最新实时盘中现价与收益！")
            st.rerun()
    with col_act2:
        if st.button("📥 裂变同步自选", help="按【建仓日期批次】分别创建专属战备池（如【🤖 哨兵-0904批次】、【🤖 哨兵-0908批次】），隔离跟踪", use_container_width=True):
            from core import forward_sentinel_tracker
            import importlib
            importlib.reload(forward_sentinel_tracker)
            forward_sentinel_tracker.sentinel_tracker.sync_to_watchlist("🤖 AI 哨兵自选跟踪池", sync_by_batch=True)
            st.toast("✅ 已按【建仓批次】分别裂变建立专属自选跟踪池！")
            st.rerun()
    with col_act3:
        if st.button("🌱 自动/补齐最新建仓", help="自动检测最新物化快照，若最新交易日未建仓则自动按四大战法新建仓（含双创高弹性标的）", use_container_width=True):
            snap_path = Path("/mnt/workspace/quant_data/full_market_snapshot.parquet")
            if not snap_path.exists():
                snap_path = PROJECT_ROOT / "quant_data" / "full_market_snapshot.parquet"
            if snap_path.exists():
                from core import forward_sentinel_tracker
                import importlib
                importlib.reload(forward_sentinel_tracker)
                res_seed = forward_sentinel_tracker.auto_seed_missing_batches(snap_path)
                if res_seed.get("status") == "seeded":
                    st.toast(f"✅ 成功补齐最新({res_seed.get('date')})新批次观察池，新增入库 {res_seed.get('added_count')} 只标的！")
                    st.rerun()
                elif res_seed.get("status") == "already_exists":
                    st.info(f"🟢 最新交易日 ({res_seed.get('date')}) 已建仓完毕（共 {res_seed.get('count')} 只标的在踪），无需重复录入。")
                else:
                    st.warning(f"建仓巡检状态: {res_seed}")
            else:
                st.error("未找到 full_market_snapshot.parquet 快照！")

# ══════════════════════════════════════════════
# 模块 ②：战略胜率卡片与整体大盘
# ══════════════════════════════════════════════
stats = sentinel_tracker.get_strategy_performance_stats()
records_df = sentinel_tracker.get_all_records()

c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
with c_kpi1:
    st.metric("🎯 累计在踪标的", f"{stats.get('total_picks', 0)} 只", help="AI 哨兵前向跟踪库已收录标的总数")
with c_kpi2:
    win_rate = stats.get('overall_win_rate', 0.0)
    delta_str = f"{win_rate-50.0:+.1f}% vs 50%基准" if stats.get('total_picks', 0) > 0 else None
    st.metric("🏆 整体浮盈胜率", f"{win_rate:.1f}%", delta=delta_str)
with c_kpi3:
    avg_pnl = stats.get('avg_pnl', 0.0)
    st.metric("📈 平均累计收益", f"{avg_pnl:+.2f}%", delta=f"{avg_pnl:+.2f}%")
with c_kpi4:
    st.metric("⏳ 核心检验周期", "1个月 (T+22)", delta="季度(T+66)/半年(T+132)")

st.markdown("---")

# ══════════════════════════════════════════════
# 双轮驱动 Tab 布局：绝不破坏原有体系，以独立面板无缝融合新能力
# ══════════════════════════════════════════════
tab_forward, tab_sentiment = st.tabs([
    "🔭 哨兵前向实战台账与复盘",
    "⚡ 超短情绪雷达与异动前哨 (Layer 8 融合)"
])

with tab_forward:
    # 战略战法天梯榜横向对比
    strat_dict = stats.get("strategy_breakdown", {})
    if strat_dict:
        st.markdown("#### ⚔️ 四大核心战法实盘实效天梯榜 (前向真实收益对决)")
        c_cols = st.columns(len(strat_dict))
        for idx, (st_name, st_val) in enumerate(strat_dict.items()):
            with c_cols[idx]:
                w_rate = st_val.get("win_rate", 0.0)
                a_pnl = st_val.get("avg_pnl", 0.0)
                color = "#22C55E" if a_pnl > 0 else "#EF4444"
                border_color = "rgba(34, 197, 94, 0.4)" if a_pnl > 0 else "rgba(255, 255, 255, 0.1)"
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid {border_color}; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px;">
                    <div style="font-size: 13px; font-weight: 700; color: #F8FAFC;">{st_name}</div>
                    <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">入池标的: <b>{st_val.get('count', 0)}</b> 只</div>
                    <div style="font-size: 18px; font-weight: 800; color: {color}; margin: 4px 0;">{a_pnl:+.2f}%</div>
                    <div style="font-size: 11px; color: #CBD5E1;">实盘胜率: <b>{w_rate:.1f}%</b> | 最高: <b>+{st_val.get('max_pnl', 0.0):.2f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
    # ══════════════════════════════════════════════
    # 模块 ③：板块特化筛选与批次管理表
    # ══════════════════════════════════════════════
    if not records_df.empty:
        c_f1, c_f2, c_f3 = st.columns([3.5, 3.5, 3.0])
        with c_f1:
            board_option = st.selectbox(
                "🏛️ 板块特化重点聚焦",
                ["👑 重点聚焦：创业板 (300) & 科创板 (688)", "⭐ 全市场 (主板+双创)", "🏢 仅主板 (60/00)"],
                key="sentinel_board_focus"
            )
        with c_f2:
            st_filter = st.selectbox(
                "🎯 战法类型筛选",
                ["全部战法"] + list(records_df["strategy"].unique()),
                key="sentinel_strat_filter_standalone"
            )
        with c_f3:
            all_dates = sorted(list(records_df["entry_date"].unique()), reverse=True)
            date_filter = st.selectbox(
                "📅 建仓日期批次",
                ["全部批次"] + all_dates,
                key="sentinel_date_filter_standalone"
            )

        # 数据过滤
        view_df = records_df.copy()
        
        # 板块过滤逻辑
        if "创业板" in board_option:
            view_df = view_df[view_df["code"].astype(str).str.startswith(("300", "688"))]
        elif "仅主板" in board_option:
            view_df = view_df[~view_df["code"].astype(str).str.startswith(("300", "688", "8", "4"))]

        if st_filter != "全部战法":
            view_df = view_df[view_df["strategy"] == st_filter]
        if date_filter != "全部批次":
            view_df = view_df[view_df["entry_date"] == date_filter]

        display_cols = [
            "entry_date", "strategy", "code", "name", "entry_close", "latest_close",
            "holding_days", "pnl_pct", "max_high_pct", "max_drawdown_pct",
            "trend_status", "chip_evolution"
        ]
        show_df = view_df[display_cols].copy()

        # 增加一行便捷穿透动作条：点击或选择即可秒级弹出走势图
        c_pick_label, c_pick_box, c_pick_btn = st.columns([2.5, 5.5, 2.0])
        with c_pick_label:
            st.markdown("<div style='font-size:12px; color:#38BDF8; font-weight:700; padding-top:6px;'>🔍 标的分时行情全息透视：</div>", unsafe_allow_html=True)
        with c_pick_box:
            stock_options = [f"{r['code']} - {r['name']} ({r['strategy']})" for _, r in show_df.iterrows()]
            selected_stock_str = st.selectbox(
                "选择标的穿透全息分时走势",
                options=stock_options,
                label_visibility="collapsed",
                key="sel_stock_tab1"
            )
        with c_pick_btn:
            if st.button("📈 弹出当日分时走势", use_container_width=True, type="primary"):
                if selected_stock_str:
                    c_code = selected_stock_str.split(" - ")[0].strip()
                    c_name = selected_stock_str.split(" - ")[1].split(" ")[0].strip()
                    show_stock_intraday_modal(c_code, c_name)

        df_event = st.dataframe(
            show_df,
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
            key="sentinel_tab1_table",
            column_config={
                "entry_date": st.column_config.TextColumn("📅 建仓日期"),
                "strategy": st.column_config.TextColumn("🎯 入选战法"),
                "code": st.column_config.TextColumn("代码"),
                "name": st.column_config.TextColumn("名称"),
                "entry_close": st.column_config.NumberColumn("💰 初始基准价", format="%.2f"),
                "latest_close": st.column_config.NumberColumn("当前实时价", format="%.2f"),
                "holding_days": st.column_config.NumberColumn("持仓天数", format="T+%d"),
                "pnl_pct": st.column_config.NumberColumn("📈 实时收益率", format="%.2f%%"),
                "max_high_pct": st.column_config.NumberColumn("🔥 最高脉冲", format="%.2f%%"),
                "max_drawdown_pct": st.column_config.NumberColumn("🛡️ 最大回撤", format="%.2f%%"),
                "trend_status": st.column_config.TextColumn("📊 趋势定性"),
                "chip_evolution": st.column_config.TextColumn("🔒 筹码演化"),
            }
        )

        # 若用户在表格中直接点击选中某一行，自动弹出该标的分时图
        if df_event and hasattr(df_event, "selection") and df_event.selection and df_event.selection.rows:
            sel_idx = df_event.selection.rows[0]
            if sel_idx < len(show_df):
                sel_row = show_df.iloc[sel_idx]
                show_stock_intraday_modal(str(sel_row["code"]), str(sel_row["name"]))
    else:
        st.info("AI 哨兵前向账本暂无记录，可点击右上角【🌱 导入今日双创标的】或由凌晨流水线自动建仓入库。")

    st.markdown("---")

    # ══════════════════════════════════════════════
    # 模块 ④：【核心大杀器】多模型前向复盘与 Google Drive 云端归档
    # ══════════════════════════════════════════════
    st.markdown("### 🧠 跨模型实盘前向推演：我们的选股原则中哪些最具实战暴利价值？")
    st.caption("🤖 由 ModelScope 双旗舰大模型（MiniMax-M1 深度思维反思 + Qwen3-30B 极速结构化指令）对所有历史前向批次标的进行横向对照，客观穿透哪些物理因子最有效，自动生成 Markdown 并同步归档至 **Google Drive** 与 DSW。")

    col_ai_btn, col_ai_quick, col_ai_info = st.columns([3.5, 3.5, 3])
    with col_ai_btn:
        btn_generate_multi_report = st.button("🚀 生成多模型全景研报 & 同步 Google Drive", type="primary", use_container_width=True, help="同时召唤 MiniMax-M1 与 Qwen3-30B 双脑推演，生成多视角归因战报，并秒级直通保存到 Google Drive！")
    with col_ai_quick:
        btn_eval_rules = st.button("⚡ 快速屏幕单兵推演 (30B 秒级)", use_container_width=True, help="快速在当前网页屏幕输出 30B 归因分析")
    with col_ai_info:
        st.markdown("<div style='font-size:12px; color:#94A3B8; padding-top:6px;'>直通腾讯现价真值，100% 杜绝后视镜幻觉。</div>", unsafe_allow_html=True)

    # 历史研报查看与加载
    rep_dir = PROJECT_ROOT / "quant_data" / "reports"
    if not rep_dir.exists():
        rep_dir = Path("/mnt/workspace/quant_data/reports")
    rep_files = sorted(list(rep_dir.glob("Tianyan_Sentinel_Review_*.md")), reverse=True) if rep_dir.exists() else []

    if rep_files:
        with st.expander("📚 历史前向复盘研报文库 (已归档至 Google Drive)", expanded=False):
            c_sel_rep, c_down_rep = st.columns([7, 3])
            rep_map = {f.name: f for f in rep_files}
            selected_rep_name = c_sel_rep.selectbox("选择历史复盘研报：", options=list(rep_map.keys()), index=0)
            selected_rep_file = rep_map[selected_rep_name]
            with open(selected_rep_file, "r", encoding="utf-8") as rf:
                rep_text = rf.read()
            c_down_rep.download_button(
                label=f"💾 下载 {selected_rep_name}",
                data=rep_text,
                file_name=selected_rep_name,
                mime="text/markdown",
                use_container_width=True
            )
            st.markdown(sanitize_ai_report_markdown(rep_text))

    # 触发一键生成多模型全景研报并同步 Google Drive
    if btn_generate_multi_report:
        if records_df.empty:
            st.warning("当前账本无记录，无法执行归因推演。")
        else:
            with st.spinner("🛰️ 正在召唤 ModelScope 双旗舰模型进行宏观与微观双重视角交叉推演，并将研报归档至 Google Drive..."):
                try:
                    from scripts.generate_sentinel_multi_model_reports import generate_sentinel_multi_model_report
                    out_path = generate_sentinel_multi_model_report()
                    if out_path and out_path.exists():
                        st.success(f"🎉 成功生成多模型前向复盘研报！已保存并同步至 Google Drive: `{out_path.name}`")
                        with open(out_path, "r", encoding="utf-8") as f_out:
                            content_md = f_out.read()
                        st.markdown(sanitize_ai_report_markdown(content_md))
                        st.rerun()
                except Exception as e_rep:
                    st.error(f"研报生成异常: {e_rep}")

    # 快速屏幕单兵推演
    if btn_eval_rules:
        if records_df.empty:
            st.warning("当前账本无记录，无法执行归因推演。")
        else:
            with st.spinner("🛰️ 30B 参谋大脑正在深度复盘所有历史前向标的，结合超短情绪背景解算战法价值贡献度..."):
                eval_rows = []
                for _, r in records_df.iterrows():
                    eval_rows.append(
                        f"- 标的: {r['name']} ({r['code']}), 战法: {r['strategy']}, 建仓日: {r['entry_date']}, "
                        f"初始成本: {r['entry_close']:.2f}, 当前现价: {r['latest_close']:.2f}, 浮盈: {r['pnl_pct']:+.2f}%, "
                        f"持仓: T+{r['holding_days']}, 初始CPR: {r.get('entry_cpr', 0.0):.2f}, 初始BRI: {r.get('entry_bri', 0.0):.2f}, "
                        f"初始LFS: {r.get('entry_lfs', 0.0):.2f}, 状态: {r.get('trend_status', '跟踪中')}"
                    )
                context_text = "\n".join(eval_rows[:35])

                # 提取战法对比
                strat_text = "\n".join([
                    f"- {k}: 样本 {v.get('count',0)}只, 平均浮盈 {v.get('avg_pnl',0):+.2f}%, 胜率 {v.get('win_rate',0):.1f}%"
                    for k, v in stats.get("strategy_breakdown", {}).items()
                ])

                # 提取超短情绪背景
                try:
                    from core.sentiment_radar import calculate_sentiment_summary
                    cur_sm = calculate_sentiment_summary()
                    sm_text = f"今日涨停 {cur_sm.get('zt_count',0)}家, 炸板率 {cur_sm.get('break_rate',0)}%, 最高连板 {cur_sm.get('max_height',0)}板, 领涨行业: {cur_sm.get('top_industries',[])[:3]}"
                except Exception:
                    sm_text = "情绪温度平稳"

                attribution_prompt = f"""你是由天衍全息量化系统驱动的 30B 首席战术参谋总长。
统帅要求对天衍 AI 哨兵自建仓以来的全部前向标的执行【前向实战复盘与四大战法归因评估】。

【统帅战略定力与核心导向】：
在当今 A 股市场，极短线与分秒级打板博弈为顶级量化高频程序主导，普通资金不可盲目追随；
天衍系统的根基在于【确定性物理筹码选股战术】（CPR 锁仓刚性、BRI 断层真空、κCYC 斐波收敛），追求波段与中短期（T+5 至 T+22）正期望超额。
全市场的超短打板情绪与题材归因（{sm_text}）必须作为【大盘风向研判】与【排雷红线】，以辅助物理选股战术！

【四大选股战法实盘收益比真实战况】：
{strat_text}

【历史建仓标的实盘演化台账（包含初始物理张量与真实走出来的盈亏）】：
{context_text}

【战役复盘与原则归因研判指令】：
请严格遵循实战客观事实，杜绝任何模板废话，直接输出三大板块（统一使用 ### 三级标题，严禁输出任何 ASCII 字符方框，数据采用列表或加粗呈现）：

### ⚔️ 一、 四大战法实战收益比横向对决（哪种战法最具价值？）
- 分析真实走势最好、超额收益最显著的标的，它们在建仓时具有哪些**绝对共同的物理量化特征**？
- 对比四大战法表现：为什么超级主升与物理真空领跑？为什么战略黄金坑在震荡市遭遇阻力？给出确凿的物理筹码动量诠释。

### ⚠️ 二、 破位与滞涨标的反思（触犯了哪些隐性暗礁与排雷红线？）
- 深入剖析走势落后、发生回撤或洗盘受阻的标的，当时选股时忽略了什么潜在风险？
- 确立必须增设的“一票否决”排雷红线（上方筹码密集套牢峰、换手率急剧异常放大等）。

### 🏹 三、 统帅当下选股决策指引（当务之急该怎么选？）
- 结合当前最新行情特征，尤其针对【创业板 (300) 与科创板 (688)】的高弹性标的，给出统帅在本周选股时的明确参数阈值推荐：
  1. CPR 刚性度必须大于多少？
  2. BRI 断层真空度必须大于多少？
  3. LFS 安全阈值区间是多少？
  4. 建议四大战法的配置权重倾斜比例。
"""

                try:
                    from core.providers.modelscope_client import ModelScopeClient
                    client = ModelScopeClient()
                    res = client.create_chat_completion(
                        messages=[{"role": "user", "content": attribution_prompt}],
                        model="Qwen/Qwen3-Coder-30B-A3B-Instruct",
                        temperature=0.1
                    )
                    thinking = res.get("thinking", "")
                    content = res.get("content", "")
                    
                    with st.chat_message("assistant", avatar="🧠"):
                        if thinking:
                            with st.expander("💡 参谋大脑深度反思与归因推演链", expanded=False):
                                st.markdown(f"```text\n{thinking}\n```")
                        st.markdown(sanitize_ai_report_markdown(content))
                        st.caption(f"⚡ 推理引擎: {res.get('model', 'Qwen3-Coder-30B')} | ⏱️ 耗时: {res.get('duration_seconds', 0.0):.2f}s | ● 纯客观真值归因")
                except Exception as e:
                    st.error(f"⚠️ 大模型调用提示: {e}")

# ══════════════════════════════════════════════
# Tab 2：超短情绪雷达与异动前哨（Layer 8 打板连板融合体系）
# ══════════════════════════════════════════════
with tab_sentiment:
    c_st_title, c_st_act = st.columns([7.0, 3.0])
    with c_st_title:
        st.markdown("### ⚡ 全市场超短情绪温度计 & 题材催化前哨")
        st.caption("🛡️ **无缝融合开源 Layer 8 军械库**：实时感知全市场涨停板封板质量、连板高度梯队、炸板率、题材归因与财联社电报，为前向战法提供宏观风控与超短流动性指引。")
    with c_st_act:
        import datetime
        now_time_str = datetime.datetime.now().strftime("%H:%M:%S")
        if st.button("🔄 立即刷新超短雷达", help="直连交易所涨停板与财联社流，毫秒级获取最新实时打板数据", use_container_width=True, type="primary"):
            st.toast("✅ 情绪雷达与即时快讯已刷新！")
            st.rerun()
        st.caption(f"<div style='text-align:right; font-size:11px; color:#94A3B8;'>⏱️ 盘中数据时间: {now_time_str}</div>", unsafe_allow_html=True)

    from core.sentiment_radar import calculate_sentiment_summary, fetch_cls_telegraph, fetch_stock_monitors

    # 顶部情绪指标卡
    try:
        sm = calculate_sentiment_summary()
    except Exception as e_s:
        sm = {"zt_count": 0, "zb_count": 0, "dt_count": 0, "break_rate": 0.0, "max_height": 0, "ladder": {}, "top_industries": []}

    c_s1, c_s2, c_s3, c_s4, c_s5 = st.columns(5)
    with c_s1:
        st.metric("🔥 今日涨停家数", f"{sm.get('zt_count', 0)} 只", delta="打板先锋")
    with c_s2:
        st.metric("💥 炸板家数", f"{sm.get('zb_count', 0)} 只", delta=f"炸板率 {sm.get('break_rate', 0.0)}%", delta_color="inverse")
    with c_s3:
        st.metric("🧊 跌停家数", f"{sm.get('dt_count', 0)} 只", delta="冰点监控", delta_color="inverse")
    with c_s4:
        st.metric("👑 最高连板高度", f"{sm.get('max_height', 0)} 连板", delta="空间龙头")
    with c_s5:
        ladder_txt = " / ".join([f"{k}板({v})" for k, v in sm.get("ladder", {}).items()]) or "无梯队"
        st.metric("🪜 连板梯队分布", ladder_txt)

    st.markdown("---")

    col_zt_left, col_news_right = st.columns([6.0, 4.0])

    with col_zt_left:
        st.markdown("#### 🎯 实时涨停池精选与连板梯队")
        zt_list = sm.get("zt_samples", [])
        if zt_list:
            zt_df = pd.DataFrame(zt_list)[["code", "name", "price", "pct", "limit_days", "first_seal", "industry"]]
            
            # 便捷弹窗选择器
            c_zt_sel_box, c_zt_sel_btn = st.columns([7, 3])
            with c_zt_sel_box:
                zt_options = [f"{r['code']} - {r['name']} ({r['limit_days']}板, {r['industry']})" for _, r in zt_df.iterrows()]
                sel_zt_str = st.selectbox("选择涨停标的查看分时走势", options=zt_options, label_visibility="collapsed", key="sel_zt_opt")
            with c_zt_sel_btn:
                if st.button("📈 弹出涨停分时", use_container_width=True):
                    if sel_zt_str:
                        zt_c = sel_zt_str.split(" - ")[0].strip()
                        zt_n = sel_zt_str.split(" - ")[1].split(" ")[0].strip()
                        show_stock_intraday_modal(zt_c, zt_n)

            zt_event = st.dataframe(
                zt_df,
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="zt_table_interactive",
                column_config={
                    "code": st.column_config.TextColumn("代码"),
                    "name": st.column_config.TextColumn("名称"),
                    "price": st.column_config.NumberColumn("现价", format="%.2f"),
                    "pct": st.column_config.NumberColumn("涨幅", format="%.2f%%"),
                    "limit_days": st.column_config.NumberColumn("连板数", format="%d板"),
                    "first_seal": st.column_config.TextColumn("首封时间"),
                    "industry": st.column_config.TextColumn("所属行业")
                }
            )

            # 点击表格任意行直接弹出全息分时图
            if zt_event and hasattr(zt_event, "selection") and zt_event.selection and zt_event.selection.rows:
                sel_zt_idx = zt_event.selection.rows[0]
                if sel_zt_idx < len(zt_df):
                    sel_zt_row = zt_df.iloc[sel_zt_idx]
                    show_stock_intraday_modal(str(sel_zt_row["code"]), str(sel_zt_row["name"]))
        else:
            st.info("当前暂无涨停池数据或非交易时段。")

        # 重点监控与异动排雷
        st.markdown("#### ⚠️ 交易所重点监控与风险警示池 (一票否决参考)")
        mon_list = fetch_stock_monitors()
        if mon_list:
            mon_df = pd.DataFrame(mon_list)[["code", "name", "start", "end"]]
            st.dataframe(
                mon_df.head(10),
                hide_index=True,
                use_container_width=True,
                column_config={
                    "code": st.column_config.TextColumn("标的代码"),
                    "name": st.column_config.TextColumn("标的名称"),
                    "start": st.column_config.TextColumn("监控生效起"),
                    "end": st.column_config.TextColumn("监控生效止")
                }
            )
        else:
            st.success("🟢 暂无生效中的交易所严重异动重点监控标的。")

    with col_news_right:
        st.markdown("#### ⚡ 财联社 7×24 实时财经电报 (本地签名直通)")
        news_items = fetch_cls_telegraph(15)
        if news_items:
            for item in news_items:
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.6); border-left: 3px solid #38BDF8; padding: 6px 10px; margin-bottom: 8px; border-radius: 4px;">
                    <div style="font-size: 11px; color: #38BDF8; font-weight: 700;">⏱️ {item['time']}</div>
                    <div style="font-size: 12px; color: #F1F5F9; font-weight: 600; margin-top: 2px;">{item['title']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("正在获取财联社即时快讯...")

