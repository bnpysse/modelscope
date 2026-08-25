"""
天眼全息智导系统 V7.0 (ModelScope Edition) — Streamlit 主入口

启动: uv run streamlit run streamlit_app/app.py
"""
import sys
import json
from pathlib import Path

ROOT_DIR = str(Path(__file__).parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd

from core.engine import create_engine
from core.models import FIB_PERIODS, DIM5_MA_PERIODS
from core.ai_advisor import query_ai_staff_report
from core.providers.modelscope_client import modelscope_client
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
.block-container { padding: 0.3rem 0.8rem 0.8rem 0.8rem !important; max-width: 100% !important; }

/* 顶栏紧凑控件 */
div[data-testid="stSelectbox"],
div[data-testid="stRadio"] { margin: 0 !important; padding: 0 !important; }
div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label { display: none !important; }
div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 4px !important; }
div[data-testid="stRadio"] > div > label { display: flex !important; padding: 2px 8px !important; font-size: 0.75rem !important; }

/* 配额微型徽章 */
.quota-badge {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    color: #94A3B8;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 36px;
}
.quota-badge b { color: #10B981; }

/* 报告输出容器 */
.report-container {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    padding: 18px 22px;
    border-radius: 8px;
    border: 1px solid #334155;
    border-left: 4px solid #F59E0B;
    color: #F1F5F9;
    line-height: 1.7;
    font-size: 13.5px;
    margin-top: 10px;
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
targets = engine.get_targets()

# 获取 ModelScope 今日免费配额水位
quota = modelscope_client.get_quota_status()
ratio_pct = round(quota["remaining_ratio"] * 100, 1)

# ==========================================
# 顶栏全控制台 (标的 / 周期 / 维五 / 模型选择 / 配额水库)
# ==========================================
t1, t2, t3, t4, t5 = st.columns([2.2, 1.1, 2.6, 2.6, 2.0], gap="small")

with t1:
    tgt_opts = {f"{t.name} ({t.code})": t.code for t in targets}
    sel_label = st.selectbox("t", list(tgt_opts.keys()), 0, label_visibility="collapsed")
    sel_code = tgt_opts[sel_label]

with t2:
    fib_l = [n for n, _ in FIB_PERIODS]
    fib_v = [v for _, v in FIB_PERIODS]
    fi = st.selectbox("f", range(len(fib_l)), 3,
                      format_func=lambda i: fib_l[i], label_visibility="collapsed")
    sel_days = fib_v[fi]

with t3:
    d5l = [n for n, _ in DIM5_MA_PERIODS]
    d5v = [v for _, v in DIM5_MA_PERIODS]
    d5i = st.radio("d", range(len(d5l)), 3,
                   format_func=lambda i: d5l[i], horizontal=True, label_visibility="collapsed")
    sel_dim5 = d5v[d5i]

with t4:
    model_map = {
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
# 数据切片
# ==========================================
df = engine.get_stock_data(sel_code, days=sel_days)
if df.is_empty():
    st.error(f"⚠️ 未找到标的 {sel_code} 的数据。")
    st.stop()

stock_name = engine.get_stock_name(sel_code)
snapshot = engine.get_latest_snapshot(sel_code)
fib_matrix = engine.get_fibonacci_depth_matrix(sel_code)

# ==========================================
# 全 JS 交互组件 (图表 + HUD 一体化，鼠标悬停实时联动)
# ==========================================
fig = build_radar_figure(df, stock_name, dim5_mode=sel_dim5)
render_radar_with_hud(fig, df, stock_name, dim5_mode=sel_dim5, height=800)

# ==========================================
# 斐波那契战略纵深矩阵与参谋部 AI 全景审计面板
# ==========================================
st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

with st.expander("📊 198 交易日斐波那契战略纵深矩阵 (5, 13, 34, 55, 89, 144, 198)", expanded=False):
    if fib_matrix:
        fib_df = pd.DataFrame(fib_matrix)
        st.dataframe(fib_df, use_container_width=True, hide_index=True)

with st.expander(f"🤖 天眼参谋部 · AI 深度量化全景穿透审计 ({sel_m_label.split(' ')[1]})", expanded=False):
    c1, c2 = st.columns([2.8, 7.2])
    with c1:
        run_ai = st.button(f"⚡ 召唤 {sel_m_label.split(' ')[1]} 执行穿透审计", type="primary", use_container_width=True)
    with c2:
        st.markdown("<span style='font-size:12px; color:#9CA3AF;'>依据 198 交易日斐波那契时序纵深、最新截面 22 项物理真值与三大战术铁律执行严格 CoT 穿透推演。</span>", unsafe_allow_html=True)
    
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
            
            # 如果包含思维链，渲染展开折叠栏
            if res.get("thinking"):
                with st.expander("💡 参谋部 CoT 思考推演链 (大模型内生逻辑)", expanded=False):
                    st.markdown(f"```text\n{res['thinking']}\n```")
            
            st.markdown(f'<div class="report-container">{res["content"]}</div>', unsafe_allow_html=True)
            st.caption(f"⚡ 审计模型: `{res.get('model_used')}` | 耗时: `{res.get('duration_seconds')}s` | 状态: `{res.get('status')}`")
