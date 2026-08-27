"""
天眼全息智导系统 V7.0 (ModelScope Edition) — Streamlit 主入口

启动: uv run streamlit run streamlit_app/app.py
"""
import sys
import json
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd

from core.engine import create_engine
from core.models import FIB_PERIODS
from core.ai_advisor import query_ai_staff_report, evaluate_local_tactical_status
from core.providers.modelscope_client import modelscope_client
from core.full_market_screener import screener
from core.level2_tick_engine import level2_engine
from core.research_report_engine import report_engine
from streamlit_app.components.radar_chart import build_radar_figure
from streamlit_app.components.crosshair import render_radar_with_hud

# ==========================================
# 页面配置 (全屏沉浸式紧凑布局)
# ==========================================
st.set_page_config(
    page_title="天眼全息智导系统 V7.0 · ModelScope",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="collapsedControl"] { display: none !important; }
.stApp { background-color: #0B0F19; color: #E5E7EB; }
header, #MainMenu, footer { display: none !important; }
.block-container { padding: 0.2rem 0.6rem 0.6rem 0.6rem !important; max-width: 100% !important; }

/* 顶栏紧凑控件与小字号 */
div[data-testid="stSelectbox"] { margin: 0 !important; padding: 0 !important; }
div[data-testid="stSelectbox"] label { display: none !important; }
div[data-testid="stSelectbox"] div[data-baseweb="select"] { min-height: 28px !important; height: 28px !important; }
div[data-testid="stSelectbox"] * { font-size: 11px !important; }

/* 折叠栏 Expander 统一微型小字号与紧凑内边距 */
div[data-testid="stExpander"] { margin-bottom: 4px !important; }
div[data-testid="stExpander"] summary {
    font-size: 11.5px !important;
    padding: 3px 8px !important;
    min-height: 28px !important;
    background: #0F172A !important;
    border: 1px solid #1E293B !important;
    border-radius: 4px !important;
}
div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    padding: 6px 10px !important;
    background: #0B0F19 !important;
    border: 1px solid #1E293B !important;
    border-top: none !important;
}

/* 分组管理与输入框统一微型小字号 */
div[data-testid="stTextInput"] { margin: 0 !important; padding: 0 !important; }
div[data-testid="stTextInput"] label { font-size: 10.5px !important; color: #94A3B8 !important; padding-bottom: 1px !important; }
div[data-testid="stTextInput"] input { height: 28px !important; font-size: 11px !important; background-color: #1E293B !important; color: #F1F5F9 !important; border-radius: 4px !important; border: 1px solid #334155 !important; }
div[data-testid="stButton"] button { height: 28px !important; font-size: 11px !important; border-radius: 4px !important; padding: 0 10px !important; }

/* Tabs 标签小字号 */
button[data-baseweb="tab"] { font-size: 11px !important; padding: 4px 12px !important; }

/* 配额微型徽章 */
.quota-badge {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10.5px;
    color: #94A3B8;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 28px;
}
.quota-badge b { color: #10B981; }

/* 战术状态条 */
.tactical-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #0F172A;
    border: 1px solid #1E293B;
    border-radius: 4px;
    padding: 4px 10px;
    margin: 2px 0 5px 0;
    font-size: 11px;
}
.pos-tag {
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 3px;
    display: inline-block;
    font-size: 10.5px;
}

/* 指标卡片网格 */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 6px;
    margin: 2px 0 6px 0;
}
.metric-card {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 10.5px;
}
.metric-card-title {
    color: #94A3B8;
    font-size: 10px;
    margin-bottom: 2px;
}
.metric-card-value {
    font-size: 13px;
    font-weight: 700;
    font-family: monospace;
}
.metric-card-sub {
    font-size: 9.5px;
    color: #64748B;
    margin-top: 1px;
}

/* 报告输出容器 */
.report-container {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    padding: 12px 16px;
    border-radius: 4px;
    border: 1px solid #334155;
    border-left: 3px solid #F59E0B;
    color: #F1F5F9;
    line-height: 1.6;
    font-size: 12px;
    margin-top: 4px;
    white-space: pre-wrap;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 引擎加载
# ==========================================
@st.cache_resource
def load_engine():
    return create_engine(ROOT_DIR)

engine = load_engine()
group_names = engine.get_group_names()
if "selected_group" not in st.session_state:
    st.session_state["selected_group"] = group_names[0] if group_names else "⭐ 全部标的池"

quota = modelscope_client.get_quota_status()
ratio_pct = round(quota["remaining_ratio"] * 100, 1)

# ==========================================
# 1. 顶栏六合一全控制台 (自选分组 / 标的 / 周期 / 维五下拉 / 金融大模型选择 / 配额水库)
# ==========================================
t0, t1, t2, t3, t4, t5 = st.columns([1.6, 1.8, 1.1, 1.6, 2.4, 1.5], gap="small")

with t0:
    sel_group = st.selectbox("g", group_names, 0, key="group_selector", label_visibility="collapsed")
    st.session_state["selected_group"] = sel_group

targets = engine.get_targets(sel_group)

with t1:
    tgt_opts = {f"{t.name} ({t.code})": t.code for t in targets}
    if not tgt_opts:
        tgt_opts = {"暂无标的 (请在下方添加)": ""}
    sel_label = st.selectbox("t", list(tgt_opts.keys()), 0, label_visibility="collapsed")
    sel_code = tgt_opts[sel_label]

with t2:
    fib_l = [n for n, _ in FIB_PERIODS]
    fib_v = [v for _, v in FIB_PERIODS]
    fi = st.selectbox("f", range(len(fib_l)), 3,
                      format_func=lambda i: fib_l[i], label_visibility="collapsed")
    sel_days = fib_v[fi]

with t3:
    # 严格使用 int 避免类型错误: 0 代表 5+20日共振, 5 代表 5日, 10 代表 10日, 20 代表 20日
    d5_opts = {
        "🌊 5+20日多维共振": 0,
        "⚡ 5日短线游资": 5,
        "📊 10日波段中枢": 10,
        "🛡️ 20日标准月线": 20,
    }
    sel_d5_label = st.selectbox("d5", list(d5_opts.keys()), 0, label_visibility="collapsed")
    sel_dim5 = d5_opts[sel_d5_label]

with t4:
    model_map = {
        "🧠 度小满轩辕-13B (XuanYuan 金融旗舰)": "Duxiaoman-DI/XuanYuan-13B-Chat",
        "🧠 度小满 FinX1 (金融深度推理模型)": "Duxiaoman-DI/XuanYuan-FinX1-Preview",
        "🧠 清华 FinGLM (中文金融逻辑)": "finglm/FinGLM",
        "🧠 Omni-FinLLM (天衍专属量化超脑)": "bnpysse/Tianyan",
        "⚡ Qwen3 Coder 30B (1.2s极速)": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "📖 MiniMax M1 (80K长文思考)": "MiniMax/MiniMax-M1-80k",
        "🏆 Qwen3 235B (2350亿旗舰)": "Qwen/Qwen3-235B-A22B-Thinking-2507",
        "🔀 智能级联调度 (Auto)": "auto",
    }
    sel_m_label = st.selectbox("m", list(model_map.keys()), 0, label_visibility="collapsed")
    selected_model_id = model_map[sel_m_label]

with t5:
    st.markdown(f"""
    <div class="quota-badge" title="ModelScope 官方每日 2,000 次免费配额，安全硬顶 1,800 次，每日 00:00 重置">
        <span>🛡️ 免费: <b>{quota['used_calls']}</b>/{quota['limit_calls']}</span>
        <span>余: <b style="color:#10B981;">{ratio_pct}%</b></span>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 自选股票池与多分组管理紧凑抽屉
# ==========================================
with st.expander("⚙️ 自选股票池与多分组管理 (自主新建分组 / 全市场标的动态入池)", expanded=False):
    tab_m1, tab_m2 = st.tabs(["➕ 添加标的到分组", "📁 新建/管理自选分组"])
    
    with tab_m1:
        c_in1, c_in2, c_in3, c_in4 = st.columns([2.5, 2.5, 2.5, 1.8], gap="small")
        with c_in1:
            target_group = st.selectbox("归属分组", [g for g in group_names if g != "⭐ 全部标的池"], 0, label_visibility="visible")
        with c_in2:
            new_code = st.text_input("股票代码", key="add_stock_code", placeholder="例如 600519 或 300750")
        with c_in3:
            new_name = st.text_input("股票名称 (可选)", key="add_stock_name", placeholder="例如 贵州茅台")
        with c_in4:
            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            add_btn = st.button("➕ 加入分组", use_container_width=True)
            if add_btn and new_code:
                code_c = new_code.strip()
                name_c = new_name.strip()
                engine.add_custom_target(code_c, name_c, group_name=target_group)
                st.success(f"标的 {name_c or code_c} ({code_c}) 已成功归入【{target_group}】！")
                st.rerun()

    with tab_m2:
        c_g1, c_g2 = st.columns([7, 3], gap="small")
        with c_g1:
            new_group_name = st.text_input("新建分组名称", placeholder="例如：度小满观察池、战略核心持仓组")
        with c_g2:
            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            create_g_btn = st.button("📁 立即创建分组", use_container_width=True)
            if create_g_btn and new_group_name:
                engine.create_custom_group(new_group_name.strip())
                st.success(f"分组【{new_group_name.strip()}】已成功创建！")
                st.rerun()

# ==========================================
# 3. DuckDB 全市场五维筹码毫秒级战术初筛雷达榜 (移至上部，方便全市场选股)
# ==========================================
with st.expander("🔍 DuckDB 全市场五维筹码毫秒级初筛雷达榜 (真空走廊 / 黄金坑 / 主升浪 · 一键建池)", expanded=False):
    tab1, tab2, tab3 = st.tabs(["🌟 物理真空走廊 + 极度单峰", "💎 战略黄金坑逆向超卖", "👑 超级主升浪筹码多头金叉"])
    
    with tab1:
        try:
            vac_df = screener.scan_vacuum_corridor()
            st.dataframe(vac_df.to_pandas(), use_container_width=True, hide_index=True)
            if st.button("📥 一键将【真空走廊 Top 15】加入「🚀 物理真空走廊突击组」", key="import_vac"):
                records = vac_df.select(["code"]).to_dicts()
                engine.add_stocks_to_group("🚀 物理真空走廊突击组", records)
                st.success("✅ 战术榜标的已全部自动同步至「🚀 物理真空走廊突击组」！")
                st.rerun()
        except Exception as e:
            st.info(f"全市场初筛载入中: {e}")

    with tab2:
        try:
            pit_df = screener.scan_golden_pit()
            st.dataframe(pit_df.to_pandas(), use_container_width=True, hide_index=True)
            if st.button("📥 一键将【黄金坑 Top 15】加入「💎 黄金坑逆向抄底池」", key="import_pit"):
                records = pit_df.select(["code"]).to_dicts()
                engine.create_custom_group("💎 黄金坑逆向抄底池")
                engine.add_stocks_to_group("💎 黄金坑逆向抄底池", records)
                st.success("✅ 黄金坑标的已全部自动同步至「💎 黄金坑逆向抄底池」！")
                st.rerun()
        except Exception as e:
            st.info(f"全市场初筛载入中: {e}")

    with tab3:
        try:
            res_df = screener.scan_super_resonance()
            st.dataframe(res_df.to_pandas(), use_container_width=True, hide_index=True)
            if st.button("📥 一键将【超级共振 Top 15】加入「👑 超级主升浪共振池」", key="import_res"):
                records = res_df.select(["code"]).to_dicts()
                engine.create_custom_group("👑 超级主升浪共振池")
                engine.add_stocks_to_group("👑 超级主升浪共振池", records)
                st.success("✅ 超级共振标的已全部自动同步至「👑 超级主升浪共振池」！")
                st.rerun()
        except Exception as e:
            st.info(f"全市场初筛载入中: {e}")

# ==========================================
# 数据切片与状态推演
# ==========================================
if not sel_code:
    st.info("💡 当前分组暂无标的，请在上方【自选股票池管理】中添加股票代码。")
    st.stop()

df = engine.get_stock_data(sel_code, days=sel_days)
if df.is_empty():
    st.error(f"⚠️ 未找到标的 {sel_code} 的数据。")
    st.stop()

stock_name = engine.get_stock_name(sel_code)
snapshot = engine.get_latest_snapshot(sel_code)
fib_matrix = engine.get_fibonacci_depth_matrix(sel_code)
local_eval = evaluate_local_tactical_status(snapshot)
micro_order = level2_engine.get_micro_features_safely(sel_code, snapshot)
consensus = report_engine.get_stock_broker_consensus(sel_code, current_price=float(snapshot.get("Close", 10.0)))

# ==========================================
# 4. 指标分析类核心内容 (战术军令条 + 五维指标穿透卡片 + 斐波那契矩阵 + AI参谋部)
# ==========================================
res_color = "#FFD700" if local_eval.get("resonance_score", 50) >= 80 else "#10B981"
st.markdown(f"""
<div class="tactical-bar">
    <div>
        <span class="pos-tag" style="background:{local_eval['badge_color']}22; color:{local_eval['badge_color']}; border:1px solid {local_eval['badge_color']};">
            {local_eval['order']} · 建议仓位 {local_eval['target_position_pct']}%
        </span>
        <span style="margin-left:8px; color:#94A3B8;">{local_eval['status_title']}</span>
    </div>
    <div style="display:flex; gap:12px; font-family:monospace;">
        <span>跨周期共振: <b style="color:{res_color};">{snapshot.get('Resonance_Score', 50):.1f}</b></span>
        <span>Norm_BIAS: <b style="color:#E5E7EB;">{snapshot.get('Norm_BIAS_5_20', 0):.2f}</b></span>
        <span>微观推升效率: <b style="color:#10B981;">{micro_order.get('eta_micro_thrust', 0):+.2f}</b> (ABR: {micro_order.get('active_buy_ratio_%', 50):.1f}%)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 五维物理场与研报共振指标快速卡片网格
lfs_val = float(snapshot.get("LFS", 50.0))
z_val = float(snapshot.get("Z_Profit", 0.0))
asr_val = float(snapshot.get("ASR", 20.0))
x70_val = float(snapshot.get("X70", 15.0))
upside_val = float(consensus.get("target_price_upside_%", 20.0))

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-card-title">① 筹码底座锁定 (LFS)</div>
        <div class="metric-card-value" style="color:{'#10B981' if lfs_val >= 55 else '#94A3B8'};">{lfs_val:.1f}</div>
        <div class="metric-card-sub">{'主力高锁仓防线' if lfs_val >= 55 else '常规筹码离散'}</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-title">② 空间获利真空 (Z')</div>
        <div class="metric-card-value" style="color:{'#F59E0B' if z_val >= 10 else '#3B82F6'};">{z_val:+.1f}%</div>
        <div class="metric-card-sub">{'触发物理真空主升' if z_val >= 10 else '中枢箱体蓄势'}</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-title">③ 筹码聚集度 (X70/ASR)</div>
        <div class="metric-card-value" style="color:#8B5CF6;">{x70_val:.1f}% <span style="font-size:9.5px; color:#94A3B8;">/ {asr_val:.1f}</span></div>
        <div class="metric-card-sub">{'超级单峰聚集' if x70_val <= 10 else '常规分布'}</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-title">④ 微观主力推力 (η/ABR)</div>
        <div class="metric-card-value" style="color:#10B981;">{micro_order.get('eta_micro_thrust', 0):+.2f} <span style="font-size:9.5px; color:#94A3B8;">({micro_order.get('active_buy_ratio_%', 50):.0f}%)</span></div>
        <div class="metric-card-sub">订单流主动买盘主导</div>
    </div>
    <div class="metric-card">
        <div class="metric-card-title">⑤ 券商研报目标溢价</div>
        <div class="metric-card-value" style="color:#EC4899;">{upside_val:+.1f}%</div>
        <div class="metric-card-sub">{consensus.get('consensus_grade', 'A 级 (常规看多)')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 斐波那契战略纵深矩阵
with st.expander("📊 198 交易日斐波那契战略纵深矩阵 (5, 13, 34, 55, 89, 144, 198)", expanded=False):
    if fib_matrix:
        fib_df = pd.DataFrame(fib_matrix)
        st.dataframe(fib_df, use_container_width=True, hide_index=True)

# 参谋部 AI 深度穿透审计
with st.expander(f"🤖 天眼参谋部 · AI 深度量化全景穿透审计 ({sel_m_label.split(' ')[1]})", expanded=False):
    c1, c2 = st.columns([2.6, 7.4], gap="small")
    with c1:
        run_ai = st.button(f"⚡ 召唤 {sel_m_label.split(' ')[1]} 执行穿透审计", type="primary", use_container_width=True)
    with c2:
        st.markdown("<span style='font-size:11px; color:#9CA3AF;'>依据 198 交易日斐波那契时序纵深、最新截面 28 项物理真值与 4 级动态仓位铁律执行严格 CoT 穿透推演。</span>", unsafe_allow_html=True)
    
    if run_ai:
        latest_json = json.dumps(snapshot, ensure_ascii=False, default=str)
        fib_json = json.dumps(fib_matrix, ensure_ascii=False, default=str)
        with st.spinner(f"🛰️ 全景引擎启动... 参谋部调用 ModelScope [{selected_model_id}] 正在执行跨周期物理真值审计..."):
            res = query_ai_staff_report(
                stock_code=sel_code,
                stock_name=stock_name,
                snapshot_json=latest_json,
                fib_matrix_json=fib_json,
                selected_model=selected_model_id
            )
            
            if res.get("thinking"):
                with st.expander("💡 参谋部 CoT 思考推演链 (大模型内生逻辑)", expanded=False):
                    st.markdown(f"```text\n{res['thinking']}\n```")
            
            st.markdown(f'<div class="report-container">{res["content"]}</div>', unsafe_allow_html=True)
            st.caption(f"⚡ 审计模型: `{res.get('model_used')}` | 耗时: `{res.get('duration_seconds')}s` | 状态: `{res.get('status')}`")

# ==========================================
# 5. 图形全息展示区 (全息五维雷达图 + HUD 右侧实时战术看板)
# ==========================================
fig = build_radar_figure(df, stock_name, dim5_mode=sel_dim5)
render_radar_with_hud(fig, df, stock_name, dim5_mode=sel_dim5, height=750)
