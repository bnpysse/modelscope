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
    col_act1, col_act2, col_act3 = st.columns([1.1, 1.1, 1.2])
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
        if st.button("🌱 建立今日(9-8)追踪池", help="为今日(9-8)按四大战法建立全新批次观察池（含双创高弹性标的）", use_container_width=True):
            snap_path = Path("/mnt/workspace/quant_data/full_market_snapshot.parquet")
            if not snap_path.exists():
                snap_path = PROJECT_ROOT / "quant_data" / "full_market_snapshot.parquet"
            if snap_path.exists():
                from core import forward_sentinel_tracker
                import importlib
                importlib.reload(forward_sentinel_tracker)
                today_str = "2026-09-08"
                all_picks = forward_sentinel_tracker.extract_daily_top_picks_from_snapshot(snap_path, board_filter="all")
                star_picks = forward_sentinel_tracker.extract_daily_top_picks_from_snapshot(snap_path, board_filter="chinext_star")
                
                # 合并建仓列表
                combined_picks = all_picks + star_picks
                cnt = forward_sentinel_tracker.sentinel_tracker.seed_daily_picks(today_str, combined_picks)
                forward_sentinel_tracker.sentinel_tracker.refresh_realtime_pnl()
                forward_sentinel_tracker.sentinel_tracker.sync_to_watchlist("🤖 AI 哨兵自选跟踪池", sync_by_batch=True)
                st.toast(f"✅ 成功建立今日({today_str})新批次观察池，新增入库 {cnt} 只标的！")
                st.rerun()
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

    st.dataframe(
        show_df,
        hide_index=True,
        use_container_width=True,
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
else:
    st.info("AI 哨兵前向账本暂无记录，可点击右上角【🌱 导入今日双创标的】或由凌晨流水线自动建仓入库。")

st.markdown("---")

# ══════════════════════════════════════════════
# 模块 ④：【核心大杀器】大模型前向复盘与选股原则深度归因
# ══════════════════════════════════════════════
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
        with st.spinner("🛰️ 30B 参谋大脑正在深度复盘所有历史前向标的，解算量化原则价值贡献度..."):
            eval_rows = []
            for _, r in records_df.iterrows():
                eval_rows.append(
                    f"- 标的: {r['name']} ({r['code']}), 战法: {r['strategy']}, 建仓日: {r['entry_date']}, "
                    f"初始成本: {r['entry_close']:.2f}, 当前现价: {r['latest_close']:.2f}, 浮盈: {r['pnl_pct']:+.2f}%, "
                    f"持仓: T+{r['holding_days']}, 初始CPR: {r.get('entry_cpr', 0.0):.2f}, 初始BRI: {r.get('entry_bri', 0.0):.2f}, "
                    f"初始LFS: {r.get('entry_lfs', 0.0):.2f}, 状态: {r.get('trend_status', '跟踪中')}"
                )
            context_text = "\n".join(eval_rows[:35])

            attribution_prompt = f"""你是由天衍全息量化系统驱动的 30B 首席战术参谋总长。
统帅要求对天衍 AI 哨兵自建仓以来的全部前向标的执行【前向实战复盘与选股原则归因评估】。

【历史建仓标的实盘演化台账（包含初始物理张量与真实走出来的盈亏）】：
{context_text}

【战役复盘与原则归因研判指令】：
请严格遵循实战客观事实，杜绝任何模板废话，直接输出三大板块（统一使用 ### 三级标题，严禁输出任何 ASCII 字符方框，数据采用列表或加粗呈现）：

### 🎯 一、 领涨先锋特征归因（哪些原则最具价值？）
- 分析真实走势最好、超额收益最显著的标的，它们在建仓时具有哪些**绝对共同的物理量化特征**？（高 CPR 刚性锁定、高 BRI 断层真空、低 LFS 浮筹？）
- 明确指出：在我们的四大战法与五维物理体系中，**哪 1~2 个核心原则是产生暴利的最强引擎**？

### ⚠️ 二、 破位滞涨标的反思（触犯了哪些隐性隐患？）
- 深入剖析走势落后、发生回撤或洗盘受阻的标的，当时选股时忽略了什么潜在风险？
- 指出必须增设的“一票否决”排雷红线。

### 🏹 三、 统帅当下周选股决策指引（当务之急该怎么选？）
- 结合当前最新行情特征，尤其针对【创业板 (300) 与科创板 (688)】的高弹性标的，给出统帅在本周选股时的明确参数阈值推荐：
  1. CPR 刚性度必须大于多少？
  2. BRI 断层真空度必须大于多少？
  3. 建议首选哪一类战法阵列进行猛攻？
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
