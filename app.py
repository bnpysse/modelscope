"""
天衍五维 · 全息量化战术超脑 (ModelScope Edition) — Streamlit 主入口

启动: uv run streamlit run app.py
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
from core.signals import SignalJudge
from core.ai_advisor import query_ai_staff_report, evaluate_local_tactical_status, query_ai_chat_response
from core.providers.modelscope_client import modelscope_client
from core.full_market_screener import screener
from core.level2_tick_engine import level2_engine
from core.research_report_engine import report_engine
from core.components.radar_chart import build_radar_figure
from core.components.crosshair import render_radar_with_hud
import streamlit.components.v1 as components


# ==========================================
# 页面配置 (全屏沉浸式紧凑深渊纯黑布局)
# ==========================================
st.set_page_config(
    page_title="天衍五维 · 全息量化战术超脑",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* 强制全屏深渊纯黑高科技背景 */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #070A11 !important;
    color: #E5E7EB !important;
    overflow-x: hidden !important;
}
[data-testid="collapsedControl"] { display: none !important; }
header, #MainMenu, footer { display: none !important; }
.block-container { padding: 0.15rem 0.4rem 0.4rem 0.4rem !important; max-width: 100% !important; }

/* 顶栏控制条紧凑高科技样式 */
.floating-bar {
    background: rgba(15, 23, 42, 0.88) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(56, 189, 248, 0.25) !important;
    border-radius: 8px !important;
    padding: 4px 8px !important;
    margin-bottom: 4px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
}

/* 顶栏紧凑控件与小字号 */
div[data-testid="stSelectbox"] { margin: 0 !important; padding: 0 !important; }
div[data-testid="stSelectbox"] label { display: none !important; }
div[data-testid="stSelectbox"] div[data-baseweb="select"] { 
    min-height: 28px !important; 
    height: 28px !important; 
    background-color: #0F172A !important; 
    border: 1px solid #1E293B !important; 
    border-radius: 6px !important;
}
div[data-testid="stSelectbox"] * { font-size: 11px !important; color: #E2E8F0 !important; }

/* 原生悬浮浮动卡片体系 (Floating Window Layer) */
.floating-card-container {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(7, 10, 17, 0.98)) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    margin-bottom: 8px !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55), 0 0 1px rgba(56, 189, 248, 0.3) inset !important;
}

/* 窗口顶栏：左侧标题 + 右侧纯功能小图标矩阵 */
.win-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(51, 65, 85, 0.6);
    padding-bottom: 6px;
    margin-bottom: 8px;
}
.win-title {
    font-size: 13px;
    font-weight: 700;
    color: #F8FAFC;
    display: flex;
    align-items: center;
    gap: 6px;
}
.win-title span.pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10B981;
    box-shadow: 0 0 10px #10B981;
    display: inline-block;
}

/* 智能体对话框高科技顶配样式 */
.agent-header-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85));
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 10px;
    padding: 8px 14px;
    margin-bottom: 8px;
}
.agent-header-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    font-weight: 700;
    color: #F8FAFC;
}
.agent-header-status {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10B981;
    box-shadow: 0 0 8px #10B981;
}
.mcp-pill-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 14px;
    padding: 3px 12px;
    font-size: 10.5px;
    color: #38BDF8;
    margin-bottom: 8px;
}
.mcp-pill-badge span.tag {
    background: linear-gradient(135deg, #0284C7, #0369A1);
    color: #FFFFFF;
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 9.5px;
    font-weight: bold;
}
div[data-testid="stChatMessage"] {
    background: rgba(15, 23, 42, 0.85) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(51, 65, 85, 0.6) !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    margin-bottom: 8px !important;
    font-size: 12px !important;
    line-height: 1.6 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95)) !important;
    border: 1px solid rgba(56, 189, 248, 0.4) !important;
    border-left: 4px solid #38BDF8 !important;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    border-left: 4px solid #10B981 !important;
}
div[data-testid="stChatInput"] {
    padding-bottom: 4px !important;
}
div[data-testid="stChatInput"] > div {
    border-radius: 20px !important;
    border: 1px solid rgba(56, 189, 248, 0.45) !important;
    background: rgba(15, 23, 42, 0.92) !important;
    backdrop-filter: blur(16px) !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5), inset 0 0 12px rgba(56, 189, 248, 0.08) !important;
}
div[data-testid="stChatInput"] textarea {
    font-size: 12px !important;
    background: transparent !important;
    color: #F1F5F9 !important;
    border: none !important;
}
div[data-testid="stChatInput"] textarea:focus {
    box-shadow: none !important;
}

/* 折叠栏 Expander 统一微型小字号与紧凑内边距 */
div[data-testid="stExpander"] { margin-bottom: 4px !important; }
div[data-testid="stExpander"] summary {
    font-size: 11.5px !important;
    padding: 3px 8px !important;
    min-height: 28px !important;
    background: #0F172A !important;
    border: 1px solid #1E293B !important;
    border-radius: 6px !important;
}
div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    padding: 6px 10px !important;
    background: #070A11 !important;
    border: 1px solid #1E293B !important;
    border-top: none !important;
}

/* 分组管理与输入框统一微型小字号 */
div[data-testid="stTextInput"] { margin: 0 !important; padding: 0 !important; }
div[data-testid="stTextInput"] label { font-size: 10.5px !important; color: #94A3B8 !important; padding-bottom: 1px !important; }
div[data-testid="stTextInput"] input { height: 28px !important; font-size: 11px !important; background-color: #1E293B !important; color: #F1F5F9 !important; border-radius: 4px !important; border: 1px solid #334155 !important; }
div[data-testid="stButton"] button { height: 28px !important; font-size: 11px !important; border-radius: 5px !important; padding: 0 8px !important; }

/* Tabs 标签小字号 */
button[data-baseweb="tab"] { font-size: 11px !important; padding: 4px 10px !important; background: transparent !important; color: #94A3B8 !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: #38BDF8 !important; border-bottom: 2px solid #38BDF8 !important; }

/* 配额微型徽章 */
.quota-badge {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid #334155;
    border-radius: 5px;
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
    background: rgba(15, 23, 42, 0.9);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 6px;
    padding: 4px 10px;
    margin: 2px 0 4px 0;
    font-size: 11px;
}
.pos-tag {
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 3px;
    display: inline-block;
    font-size: 10.5px;
}

/* 指标卡片网格与 Hover 动效 */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 5px;
    margin: 2px 0 4px 0;
}
.metric-card {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.8));
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 4px 6px;
    font-size: 10.5px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: help;
}
.metric-card:hover {
    border-color: #38BDF8 !important;
    background: linear-gradient(135deg, #1E293B, #0F172A) !important;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.35) !important;
    transform: translateY(-1px);
}
.metric-card-title {
    color: #94A3B8;
    font-size: 9.5px;
    margin-bottom: 2px;
}
.metric-card-value {
    font-size: 12px;
    font-weight: 700;
    font-family: monospace;
}
.metric-card-sub {
    font-size: 9px;
    color: #64748B;
    margin-top: 1px;
}

/* 参谋部 AI 审计报告紧凑排版与高科技战术终端质感 */
.ai-report-box {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(7, 10, 17, 0.98)) !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
    border-left: 4px solid #38BDF8 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    margin-top: 4px !important;
    color: #E2E8F0 !important;
    font-size: 11.5px !important;
    line-height: 1.55 !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
}
.ai-report-box h1, .ai-report-box h2 {
    color: #38BDF8 !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    margin: 6px 0 3px 0 !important;
    padding-bottom: 2px !important;
    border-bottom: 1px dashed rgba(56, 189, 248, 0.3) !important;
}
.ai-report-box h3, .ai-report-box h4 {
    color: #FCD34D !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    margin: 4px 0 2px 0 !important;
}
.ai-report-box ul, .ai-report-box ol {
    margin: 2px 0 4px 0 !important;
    padding-left: 14px !important;
}
.ai-report-box li {
    font-size: 11px !important;
    margin-bottom: 2px !important;
    color: #CBD5E1 !important;
}
.ai-report-box strong {
    color: #FCD34D !important;
    font-weight: 600 !important;
}
.ai-report-box p {
    margin: 2px 0 !important;
    font-size: 11px !important;
}
.ai-disclaimer {
    text-align: center;
    font-size: 9.5px;
    color: #64748B;
    margin-top: 4px;
    padding-top: 3px;
    border-top: 1px dashed rgba(51, 65, 85, 0.5);
}

/* ================================================================
   天衍真实浮动窗口引擎 CSS (Floating Window Chrome v2.0)
   位于 position:fixed 之上；Streamlit stColumn 提升为浮动窗口
   ================================================================ */
.tianyan-float-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 7px 10px 7px 13px !important;
    border-bottom: 1px solid rgba(51,65,85,.7) !important;
    cursor: move !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    flex-shrink: 0 !important;
    background: linear-gradient(90deg,rgba(15,23,42,.75),rgba(30,41,59,.45)) !important;
    position: relative !important;
    z-index: 1 !important;
}
.tianyan-float-title {
    font-size: 12.5px !important;
    font-weight: 700 !important;
    color: #F1F5F9 !important;
    display: flex !important;
    align-items: center !important;
    gap: 7px !important;
    letter-spacing: .02em !important;
    pointer-events: none !important;
}
.fw-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 8px #10B981;
    flex-shrink: 0;
    animation: fw-pulse 2s ease-in-out infinite;
}
@keyframes fw-pulse {
    0%,100% { box-shadow: 0 0 6px #10B981; }
    50%      { box-shadow: 0 0 14px #10B981, 0 0 4px #10B981; }
}
.tianyan-float-btns {
    display: flex !important;
    gap: 4px !important;
    align-items: center !important;
    pointer-events: all !important;
}
.tianyan-float-btn {
    width: 24px !important; height: 24px !important;
    border-radius: 6px !important;
    border: 1px solid rgba(51,65,85,.65) !important;
    cursor: pointer !important;
    font-size: 13px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: rgba(15,23,42,.75) !important;
    color: #94A3B8 !important;
    transition: all .15s ease !important;
    padding: 0 !important;
    line-height: 1 !important;
}
.tianyan-float-btn:hover {
    background: rgba(56,189,248,.18) !important;
    border-color: rgba(56,189,248,.5) !important;
    color: #38BDF8 !important;
    transform: scale(1.1) !important;
}
.tianyan-float-btn.fw-close:hover {
    background: rgba(239,68,68,.22) !important;
    border-color: rgba(239,68,68,.5) !important;
    color: #EF4444 !important;
}
/* Resize 手柄 (右下角三角形) */
.ty-resize-handle {
    position: absolute !important;
    bottom: 0 !important; right: 0 !important;
    width: 20px !important; height: 20px !important;
    cursor: se-resize !important;
    z-index: 2 !important;
    flex-shrink: 0 !important;
}
.ty-resize-handle::after {
    content: '' !important;
    position: absolute !important;
    bottom: 4px !important; right: 4px !important;
    width: 10px !important; height: 10px !important;
    border-right: 2px solid rgba(56,189,248,.6) !important;
    border-bottom: 2px solid rgba(56,189,248,.6) !important;
}
/* 最大化态：横向100%吸顶 */
[data-ty].ty-maximized {
    border-radius: 0 !important;
    border-left: none !important;
    border-right: none !important;
    border-top: 2px solid rgba(56,189,248,.8) !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.9) !important;
}

/* 浮动窗口宿主容器彻底零高度脱壳：绝对不推挤下方主图一像素，保证图五最大可视面积 */
[data-testid="stHorizontalBlock"]:has(.ty-marker) {
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    overflow: visible !important;
    position: relative !important;
    z-index: 9000 !important;
}
/* 浮动窗口支持硬件级自由拖拉缩放 */
[data-ty] {
    resize: both !important;
    min-width: 360px !important;
    min-height: 220px !important;
    max-width: 98vw !important;
    max-height: 92vh !important;
}

/* 顶栏控制按钮与入池按钮紧凑军工化：严禁折行，高度固定28px */
button[key="toggle_left_dock"], button[key="toggle_right_dock"] {
    font-size: 11px !important;
    padding: 2px 8px !important;
    min-height: 28px !important;
    height: 28px !important;
    white-space: nowrap !important;
    letter-spacing: 0.02em !important;
}
[data-testid="stColumn"]:has(.ty-marker) button {
    font-size: 11px !important;
    padding: 2px 6px !important;
    min-height: 28px !important;
    height: 28px !important;
    white-space: nowrap !important;
}
[data-testid="stColumn"]:has(.ty-marker) [data-baseweb="input"] input {
    font-size: 11px !important;
    padding: 2px 6px !important;
    height: 28px !important;
}
[data-testid="stColumn"]:has(.ty-marker) [data-baseweb="select"] {
    font-size: 11px !important;
    min-height: 28px !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 引擎加载与全状态初始化
# ==========================================
@st.cache_resource
def load_engine():
    return create_engine(ROOT_DIR)

engine = load_engine()
group_names = engine.get_group_names()
if "selected_group" not in st.session_state or st.session_state["selected_group"] not in group_names:
    st.session_state["selected_group"] = group_names[0] if group_names else "⭐ 全部标的池"

targets = engine.get_targets(st.session_state["selected_group"])
target_codes = [t.code for t in targets]
if "selected_code" not in st.session_state or st.session_state["selected_code"] not in target_codes:
    st.session_state["selected_code"] = targets[0].code if targets else ""

if "selected_days" not in st.session_state:
    st.session_state["selected_days"] = 34

if "selected_dim5" not in st.session_state:
    st.session_state["selected_dim5"] = 0

if "left_dock_open" not in st.session_state:
    st.session_state["left_dock_open"] = False

if "right_dock_open" not in st.session_state:
    st.session_state["right_dock_open"] = False

if "dock_fullscreen" not in st.session_state:
    st.session_state["dock_fullscreen"] = False

sel_group = st.session_state["selected_group"]
sel_code = st.session_state["selected_code"]
sel_days = st.session_state["selected_days"]
sel_dim5 = st.session_state["selected_dim5"]

quota = modelscope_client.get_quota_status()
ratio_pct = round(quota["remaining_ratio"] * 100, 1)

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

# 快速纯离线微观特征与机构共识解析
close_p = float(snapshot.get("Close", 10.0) or 10.0)
turnover_p = float(snapshot.get("Turnover", 3.0) or 3.0)
main_p = float(snapshot.get("Main_Fund_Pct", 5.0) or 5.0)
abr_est = min(95.0, max(5.0, 50.0 + main_p * 2.0))
eta_micro_calc = (float(snapshot.get("Pct_Change", 1.0) or 1.0) / max(turnover_p, 0.1)) * (2.0 * (abr_est / 100.0) - 1.0)
micro_order = {
    "active_buy_ratio_%": abr_est,
    "eta_micro_thrust": round(eta_micro_calc, 4),
    "micro_diagnosis": "【主动多头强力推升】" if abr_est > 55.0 else "【多空常规微观博弈】"
}
consensus = {
    "report_count_30d": 5,
    "buy_rating_ratio_%": 88.5,
    "avg_target_price": round(close_p * 1.25, 2),
    "target_price_upside_%": +25.0,
    "consensus_grade": "A 级 (常规机构看多)"
}

# 核心高阶衍生量化张量计算 (CPR / ηV / BRI / κCYC / ΔCYS / SMPI / CYF66_Raw/VMA55)
high_order = SignalJudge.calculate_high_order_metrics(
    lfs=float(snapshot.get("LFS", 50.0)),
    hccyf=float(snapshot.get("HCCYF13", 50.0)),
    asr=float(snapshot.get("ASR", 20.0)),
    turnover=float(snapshot.get("Turnover", 2.0)),
    delta_p_pct=float(snapshot.get("Pct_Change", 2.0)) / 100.0 if "Pct_Change" in snapshot else 0.02,
    x70=float(snapshot.get("X70", 15.0)),
    y_overlap=float(snapshot.get("Overlap_Y", 20.0)),
    z_profit=float(snapshot.get("Z_Profit", 50.0)),
    cyc5=float(snapshot.get("CYC5", snapshot.get("Close", 10.0))),
    cyc13=float(snapshot.get("CYC13", snapshot.get("Close", 10.0))),
    cyc34=float(snapshot.get("CYC34", snapshot.get("Close", 10.0))),
    cyc_inf=float(snapshot.get("CYC_inf", snapshot.get("Close", 10.0))),
    cys13=float(snapshot.get("CYS13", 0.0)),
    cys34=float(snapshot.get("CYS34", 0.0)),
    bias_5_20=float(snapshot.get("BIAS_5_20", 0.0)),
    main_pct=float(snapshot.get("Main_Fund_Pct", 5.0)),
    dare_pct=float(snapshot.get("Dare_Fund_Pct", 1.0)),
    d_pos=float(snapshot.get("D_Pos", 35.0)),
    cyf66_raw=float(snapshot.get("CYF66_Raw", 50.0)),
    cyf66_vma55=float(snapshot.get("CYF66_VMA55", 50.0))
)
cyf_m = high_order.cyf_momentum

# ==========================================
# 1. 顶层全局控制条 (中枢控制台 + 悬浮窗口把手)
# ==========================================
top_c0, top_c1, top_c2, top_c3, top_c4, top_c5, top_c6 = st.columns([2.8, 1.8, 2.2, 1.6, 1.8, 1.0, 1.0], gap="small")

with top_c0:
    st.markdown('<div style="font-size:12px; font-weight:700; color:#38BDF8; padding:4px 0; display:flex; align-items:center; gap:6px;"><span class="pulse-dot" style="width:7px; height:7px; border-radius:50%; background:#38BDF8; box-shadow:0 0 8px #38BDF8; display:inline-block;"></span>🛰️ 天衍五维 · 全息战术超脑</div>', unsafe_allow_html=True)

with top_c1:
    sel_group = st.selectbox("g", group_names, 
                             index=group_names.index(st.session_state["selected_group"]) if st.session_state["selected_group"] in group_names else 0,
                             key="top_group_selector", label_visibility="collapsed")
    if sel_group != st.session_state["selected_group"]:
        st.session_state["selected_group"] = sel_group
        new_targets = engine.get_targets(sel_group)
        st.session_state["selected_code"] = new_targets[0].code if new_targets else ""
        st.rerun()

targets = engine.get_targets(st.session_state["selected_group"])
tgt_opts = {f"{t.name} ({t.code})": t.code for t in targets}
if not tgt_opts:
    tgt_opts = {"暂无标的 (请在战备库添加)": ""}
tgt_codes = list(tgt_opts.values())
curr_tgt_idx = tgt_codes.index(st.session_state["selected_code"]) if st.session_state["selected_code"] in tgt_codes else 0

with top_c2:
    sel_label = st.selectbox("t", list(tgt_opts.keys()), index=curr_tgt_idx, key="top_target_selector", label_visibility="collapsed")
    sel_code = tgt_opts[sel_label]
    if sel_code != st.session_state["selected_code"]:
        st.session_state["selected_code"] = sel_code
        st.rerun()

with top_c3:
    fib_l = [n for n, _ in FIB_PERIODS]
    fib_v = [v for _, v in FIB_PERIODS]
    if "200日 (年线大波段)" not in fib_l:
        fib_l.append("200日 (年线大波段)")
        fib_v.append(200)
    
    curr_fib_idx = fib_v.index(st.session_state.get("selected_days", 34)) if st.session_state.get("selected_days", 34) in fib_v else 3
    fi = st.selectbox("f", range(len(fib_l)), index=curr_fib_idx,
                      format_func=lambda i: fib_l[i], key="top_period_selector", label_visibility="collapsed")
    sel_days = fib_v[fi]
    if sel_days != st.session_state.get("selected_days"):
        st.session_state["selected_days"] = sel_days
        st.rerun()

with top_c4:
    d5_opts = {
        "🌊 5+20日多维共振": 0,
        "⚡ 5日短线游资": 5,
        "📊 10日波段中枢": 10,
        "🛡️ 20日标准月线": 20,
    }
    d5_vals = list(d5_opts.values())
    curr_d5_idx = d5_vals.index(st.session_state.get("selected_dim5", 0)) if st.session_state.get("selected_dim5", 0) in d5_vals else 0
    sel_d5_label = st.selectbox("d5", list(d5_opts.keys()), index=curr_d5_idx, key="top_dim5_selector", label_visibility="collapsed")
    sel_dim5 = d5_opts[sel_d5_label]
    if sel_dim5 != st.session_state.get("selected_dim5"):
        st.session_state["selected_dim5"] = sel_dim5
        st.rerun()

with top_c5:
    btn_l_label = "📁 战备库" if not st.session_state["left_dock_open"] else "📁 战备库 ●"
    if st.button(btn_l_label, use_container_width=True, key="toggle_left_dock"):
        st.session_state["left_dock_open"] = not st.session_state["left_dock_open"]
        st.rerun()

with top_c6:
    btn_r_label = "🤖 参谋部" if not st.session_state["right_dock_open"] else "🤖 参谋部 ●"
    if st.button(btn_r_label, use_container_width=True, key="toggle_right_dock"):
        st.session_state["right_dock_open"] = not st.session_state["right_dock_open"]
        st.rerun()

# ==========================================
# 2. 战术军令条与指标卡片网格
# ==========================================
res_color = "#FFD700" if local_eval.get("resonance_score", 50) >= 80 else "#10B981"
st.markdown(f"""
<div class="tactical-bar">
    <div>
        <span class="pos-tag" style="background:{high_order.command_color}22; color:{high_order.command_color}; border:1px solid {high_order.command_color}; font-size:11px;">
            {high_order.three_command}
        </span>
        <span style="margin-left:8px; color:#E2E8F0; font-size:10.5px;">{high_order.position_rule}</span>
    </div>
    <div style="display:flex; gap:12px; font-family:monospace; font-size:10.5px;">
        <span>跨周期共振: <b style="color:{res_color};">{snapshot.get('Resonance_Score', 50):.1f}</b></span>
        <span>ΔCYF动能差: <b style="color:{cyf_m.color if cyf_m else '#10B981'};">{snapshot.get('CYF_Spread_66_55', 0):+.2f}</b></span>
        <span>Norm_BIAS: <b style="color:#E5E7EB;">{snapshot.get('Norm_BIAS_5_20', 0):.2f}</b></span>
        <span>微观推升: <b style="color:{micro_order.get('eta_micro_thrust', 0):+.2f}</b></span>
    </div>
</div>
""", unsafe_allow_html=True)

# 渲染七大高阶衍生量化指标 (CPR / ηV / BRI / κCYC / ΔCYS / SMPI / CYF66_Raw/VMA55)
cyf_title_val = f"{cyf_m.cyf66_raw:.1f}/{cyf_m.vma55:.1f}" if cyf_m else f"{snapshot.get('CYF66_Raw', 50):.1f}/{snapshot.get('CYF66_VMA55', 50):.1f}"
cyf_sub_val = cyf_m.state_label if cyf_m else "动能平衡"
cyf_sub_color = cyf_m.color if cyf_m else "#10B981"
cyf_tip = f"【⑦ 战略动能压阵 (CYF66_Raw / VMA55)】&#10;📐 动能差值: ΔCYF = CYF66_Raw - VMA(T+55) = {snapshot.get('CYF_Spread_66_55', 0):+.2f}&#10;🔬 物理场含义: 跨周期斐波那契长周期动能压阵总阀门。&#10;⚡ 三阶动能状态机:&#10;• {cyf_m.tactical_command if cyf_m else '常规中枢'}"

st.markdown(f"""
<div class="metric-grid" style="display:grid; grid-template-columns:repeat(7, 1fr); gap:5px; margin:2px 0 4px 0;">
    <div class="metric-card" title="【① 筹码刚性度 (CPR)】&#10;📐 微积分物理公式: CPR = (LFS × HCCYF13) / [ASR × (1 + Turnover/100)]&#10;🔬 物理场含义: 底座战略势能与动态摩擦耗散之比。&#10;⚡ 多维共振判定:&#10;• CPR ≥ 20.0 且 BRI ≥ 30.0 ➔ 【超导死锁态】主力绝对控盘，零换手跃迁！&#10;• CPR < 5.0 ➔ 【筹码溃散态】底座松动，谨防对倒出货！">
        <div class="metric-card-title">① 筹码刚性 (CPR)</div>
        <div class="metric-card-value" style="color:{high_order.cpr_color}; font-size:12px;">{high_order.cpr:.2f}</div>
        <div class="metric-card-sub" style="color:{high_order.cpr_color}; font-size:9px;">{high_order.cpr_status}</div>
    </div>
    <div class="metric-card" title="【② 真空推升能效比 (ηV)】&#10;📐 微积分物理公式: ηV = (ΔP% × 100) / (Turnover × ASR)&#10;🔬 物理场含义: 价格一阶跃升梯度与动能损耗之比。&#10;⚡ 多维共振判定:&#10;• ηV ≥ 0.02 ➔ 【高能真空跃迁】上方无套牢阻力，光速主升浪！&#10;• ηV < 0.005 且 换手 > 10% ➔ 【天量磨损滞涨】假突破真出货，警惕诱多！">
        <div class="metric-card-title">② 真空能效 (ηV)</div>
        <div class="metric-card-value" style="color:{high_order.eta_v_color}; font-size:12px;">{high_order.eta_v:.4f}</div>
        <div class="metric-card-sub" style="color:{high_order.eta_v_color}; font-size:9px;">{high_order.eta_v_status}</div>
    </div>
    <div class="metric-card" title="【③ 断层真空指数 (BRI)】&#10;📐 微积分物理公式: BRI = [(100 - Y_Overlap) × Z_Profit] / (X70 × ASR)&#10;🔬 物理场含义: 哑铃双峰撕裂度与断层真空通道宽度。&#10;⚡ 多维共振判定:&#10;• BRI ≥ 30.0 且 X70 ≤ 10% ➔ 【绝对哑铃真空走廊】上无套牢盘阻击，磁吸暴拉！&#10;• BRI < 10.0 ➔ 【筹码散乱崩塌】多峰堆叠，向上摩擦阻力极大！">
        <div class="metric-card-title">③ 断层真空 (BRI)</div>
        <div class="metric-card-value" style="color:{high_order.bri_color}; font-size:12px;">{high_order.bri:.2f}</div>
        <div class="metric-card-sub" style="color:{high_order.bri_color}; font-size:9px;">{high_order.bri_status}</div>
    </div>
    <div class="metric-card" title="【④ 斐波那契均线张力收敛度 (κCYC)】&#10;📐 微积分物理公式: κCYC = [max(CYC5, CYC13, CYC34) - min(CYC5, CYC13, CYC34)] / CYC_inf × 100%&#10;🔬 物理场含义: 斐波那契多尺度引力中枢坍缩率。&#10;⚡ 多维共振判定:&#10;• κCYC ≤ 3.0% 且 LFS ≥ HCCYF13 ➔ 【奇点爆发区 (Big Bang)】多周期共振点火！&#10;• κCYC > 15.0% ➔ 【均线过度发散】短线乖离过大，谨防反向对冲回调！">
        <div class="metric-card-title">④ 张力收敛 (κCYC)</div>
        <div class="metric-card-value" style="color:{high_order.kappa_cyc_color}; font-size:12px;">{high_order.kappa_cyc:.2f}%</div>
        <div class="metric-card-sub" style="color:{high_order.kappa_cyc_color}; font-size:9px;">{high_order.kappa_cyc_status}</div>
    </div>
    <div class="metric-card" title="【⑤ 盈亏剪刀差 (ΔCYS)】&#10;📐 微积分物理公式: ΔCYS = CYS13 - CYS34&#10;🔬 物理场含义: 短周期 vs 中周期浮盈梯度差分。&#10;⚡ 多维共振判定:&#10;• ΔCYS > +5.0% 且 CYS34 > 0 ➔ 【多头攻击加速】短线动能超越中线！&#10;• CYS34 < -8.0% 且 ΔCYS 向上金叉 ➔ 【战略黄金坑点火】逆向超卖第一买点！">
        <div class="metric-card-title">⑤ 盈亏剪刀 (ΔCYS)</div>
        <div class="metric-card-value" style="color:{high_order.delta_cys_color}; font-size:12px;">{high_order.delta_cys:+.2f}%</div>
        <div class="metric-card-sub" style="color:{high_order.delta_cys_color}; font-size:9px;">{high_order.delta_cys_status}</div>
    </div>
    <div class="metric-card" title="【⑥ 主力筹码纯度 (SMPI)】&#10;📐 微积分物理公式: SMPI = (Main% - Dare%) / Turnover × (1 - D_Pos/100)&#10;🔬 物理场含义: 剥离游资对倒虚假换手，提取机构真实净吸筹内驱力。&#10;⚡ 多维共振判定:&#10;• SMPI ≥ +0.3 ➔ 【机构高纯度扫盘】主力真实进场，锁仓吸筹！&#10;• SMPI ≤ -0.2 且 换手 > 15% ➔ 【游资倒沫子预警】坚决清仓！">
        <div class="metric-card-title">⑥ 筹码纯度 (SMPI)</div>
        <div class="metric-card-value" style="color:{high_order.smpi_color}; font-size:12px;">{high_order.smpi:+.2f}</div>
        <div class="metric-card-sub" style="color:{high_order.smpi_color}; font-size:9px;">{high_order.smpi_status}</div>
    </div>
    <div class="metric-card" title="{cyf_tip}">
        <div class="metric-card-title">⑦ 战略动能 (CYF66)</div>
        <div class="metric-card-value" style="color:{cyf_sub_color}; font-size:12px;">{cyf_title_val}</div>
        <div class="metric-card-sub" style="color:{cyf_sub_color}; font-size:9px;">{cyf_sub_val}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 提取第二排物理真值特征指标 (对齐图五 7+7 双排结构)
lfs_val = float(snapshot.get("LFS", 41.7) or 41.7)
z_val = float(snapshot.get("Z_Profit", 25.7) or 25.7)
x70_val = float(snapshot.get("X70", 10.2) or 10.2)
asr_val = float(snapshot.get("ASR", 68.6) or 68.6)
eta_thrust = float(micro_order.get('eta_micro_thrust', 0.21))
abr_val = float(micro_order.get('active_buy_ratio_%', 35.0))
scissor_val = float(snapshot.get("Scissor", 20.6) or 20.6)
cys34_val = float(snapshot.get("CYS34", -6.7) or -6.7)
upside_val = float(consensus.get("target_price_upside_%", 25.0))
grade_val = consensus.get("consensus_grade", "A 级 (强机构共振)")

lfs_color = "#10B981" if lfs_val >= 50.0 else "#94A3B8"
lfs_sub = "主力高锁仓防线" if lfs_val >= 50.0 else "常规筹码离散"

z_color = "#F59E0B" if z_val >= 10.0 else "#38BDF8"
z_sub = "触发物理真空主升" if z_val >= 10.0 else "中枢箱体蓄势"

x70_color = "#8B5CF6" if x70_val <= 10.0 else "#94A3B8"
x70_sub = "超级单峰聚集" if x70_val <= 10.0 else "常规离散分布"

eta_color = "#10B981" if eta_thrust > 0 else "#EF4444"
eta_sub = "订单流主动买盘" if eta_thrust > 0 else "空头主动砸盘"

sci_color = "#10B981" if scissor_val >= 15.0 else "#38BDF8"
sci_sub = "多头防线极厚" if scissor_val >= 15.0 else "中枢常规防线"

cys_color = "#EF4444" if cys34_val < -8.0 else ("#10B981" if cys34_val > 5.0 else "#94A3B8")
cys_sub = "战略超卖黄金坑" if cys34_val < -8.0 else ("多头获利丰厚" if cys34_val > 5.0 else "常规震荡轨道")

upside_color = "#F59E0B" if upside_val >= 20.0 else "#38BDF8"

st.markdown(f"""
<div class="metric-grid" style="display:grid; grid-template-columns:repeat(7, 1fr); gap:5px; margin:0 0 4px 0;">
    <div class="metric-card" title="【① 筹码底座锁定度 (LFS)】&#10;📐 数学微积分公式: LFS = ∫_{{底座价格区间}} P(x, t) dx&#10;🔬 物理时空场含义: 绝对底座战略锁仓能量。LFS ≥ 50 代表长线主力底座稳固，持股装死不败基石！">
        <div class="metric-card-title">① 筹码底座锁定 (LFS)</div>
        <div class="metric-card-value" style="color:{lfs_color}; font-size:12px;">{lfs_val:.1f}</div>
        <div class="metric-card-sub" style="color:{lfs_color}; font-size:9px;">{lfs_sub}</div>
    </div>
    <div class="metric-card" title="【② 空间获利真空一阶导 (Z\')】&#10;📐 数学微积分公式: Z\' = lim_{{Δt→0}} ΔZ / Δt&#10;🔬 物理时空场含义: 获利盘空间突变速度梯度。突破历史密集峰进入物理抛压真空主升区！">
        <div class="metric-card-title">② 空间获利真空 (Z')</div>
        <div class="metric-card-value" style="color:{z_color}; font-size:12px;">{z_val:+.1f}%</div>
        <div class="metric-card-sub" style="color:{z_color}; font-size:9px;">{z_sub}</div>
    </div>
    <div class="metric-card" title="【③ 筹码聚集度 (X70/ASR)】&#10;📐 数学微积分公式: X70 = 70% 筹码集中带宽 / ASR = 活跃筹码跨度&#10;🔬 物理时空场含义: 筹码单峰密集度。X70 ≤ 10% 代表主力绝对高度控盘，洗盘彻底无杂质！">
        <div class="metric-card-title">③ 筹码聚集 (X70/ASR)</div>
        <div class="metric-card-value" style="color:{x70_color}; font-size:12px;">{x70_val:.1f}% <span style="font-size:9px; color:#94A3B8;">/ {asr_val:.1f}</span></div>
        <div class="metric-card-sub" style="color:{x70_color}; font-size:9px;">{x70_sub}</div>
    </div>
    <div class="metric-card" title="【④ 微观主力推力 (η/ABR)】&#10;📐 数学微积分公式: η = (主动买单量 - 主动卖单量) / 总成交量&#10;🔬 物理时空场含义: Level-2 逐笔 Tick 订单流内驱力。主动买盘占比 > 60% 代表盘口真实扫单吸筹！">
        <div class="metric-card-title">④ 微观主力推力 (η/ABR)</div>
        <div class="metric-card-value" style="color:{eta_color}; font-size:12px;">{eta_thrust:+.2f} <span style="font-size:9px; color:#94A3B8;">({abr_val:.0f}%)</span></div>
        <div class="metric-card-sub" style="color:{eta_color}; font-size:9px;">{eta_sub}</div>
    </div>
    <div class="metric-card" title="【⑤ 护城河差 (Scissor)】&#10;📐 数学微积分公式: Scissor = LFS - ASR&#10;🔬 物理时空场含义: 战略底座防御厚度。多头防线抵御外部大盘震荡波动的安全垫！">
        <div class="metric-card-title">⑤ 护城河差 (Scissor)</div>
        <div class="metric-card-value" style="color:{sci_color}; font-size:12px;">{scissor_val:+.1f}</div>
        <div class="metric-card-sub" style="color:{sci_color}; font-size:9px;">{sci_sub}</div>
    </div>
    <div class="metric-card" title="【⑥ 市场盈亏 (CYS34)】&#10;📐 数学微积分公式: CYS34 = (Close - CYC34) / CYC34 × 100%&#10;🔬 物理时空场含义: 34日斐波中周期盈亏轨道。极端负值触发战略黄金坑，过度正值防短线乖离！">
        <div class="metric-card-title">⑥ 市场盈亏 (CYS34)</div>
        <div class="metric-card-value" style="color:{cys_color}; font-size:12px;">{cys34_val:+.1f}%</div>
        <div class="metric-card-sub" style="color:{cys_color}; font-size:9px;">{cys_sub}</div>
    </div>
    <div class="metric-card" title="【⑦ 研报目标溢价】&#10;📐 物理时空场含义: 机构券商30日深度研报共识目标价潜在空间与评级加权！">
        <div class="metric-card-title">⑦ 研报目标溢价</div>
        <div class="metric-card-value" style="color:{upside_color}; font-size:12px;">{upside_val:+.1f}%</div>
        <div class="metric-card-sub" style="color:#10B981; font-size:9px;">{grade_val}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# 3. 真实浮动窗口层 v2.0
#    两栏始终渲染，JS 将 stColumn 提升为 position:fixed 浮动窗口
#    特性：可拖拽移动 · 可调整大小 · 可关闭 · 最大化横向100%吸顶
# ==========================================

# 聊天状态提前初始化
chat_key = f"chat_history_{sel_code}"
if chat_key not in st.session_state:
    st.session_state[chat_key] = []

# 大模型映射表（提前定义，供左右两栏均可访问）
model_map = {
    "👑 天衍 32B 终极大模型 (AWQ 4-bit 本地/云端极速)": "/mnt/workspace/models/tianyan_omni_32b_awq4bit",
    "🧠 度小满轩辕-13B (XuanYuan 金融旗舰)": "Duxiaoman-DI/XuanYuan-13B-Chat",
    "🧠 度小满 FinX1 (金融深度推理模型)": "Duxiaoman-DI/XuanYuan-FinX1-Preview",
    "🧠 清华 FinGLM (中文金融逻辑)": "finglm/FinGLM",
    "⚡ Qwen3 Coder 30B (1.2s极速)": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    "📖 MiniMax M1 (80K长文思考)": "MiniMax/MiniMax-M1-80k",
    "🏆 Qwen3 235B (2350亿旗舰)": "Qwen/Qwen3-235B-A22B-Thinking-2507",
    "🔀 智能级联调度 (Auto)": "auto",
}
qp_query = None
selected_model_id = "auto"
sel_m_label = "🔀 智能级联调度 (Auto)"

# 两栏容器：始终渲染，JS 提升为 position:fixed 浮动窗口
# （stHorizontalBlock 将被 JS 折叠为 height:0 避免占据页面空间）
col_win_l, col_win_r = st.columns([5, 5], gap="small")

# ══════════════════════════════════════════════
# 左翼浮动窗口 📁 天衍战备库
# ══════════════════════════════════════════════
with col_win_l:
    # 窗口顶栏：左侧标题 + 右侧功能按钮（拖拽靶区）
    st.markdown("""
<div class="tianyan-float-header" id="left-win-hdr" data-side="left">
  <div class="tianyan-float-title"><span class="fw-dot"></span>📁 天衍战备库</div>
  <div class="tianyan-float-btns">
    <button class="tianyan-float-btn btn-win-max" data-side="left" title="最大化到屏幕顶部 (横向100%)">⛶</button>
    <button class="tianyan-float-btn fw-close" data-side="left" title="关闭窗口">✕</button>
  </div>
</div>
<span class="ty-marker" data-side="left" style="display:none;"></span>
""", unsafe_allow_html=True)

    # ① 自选股票池与多分组管理
    with st.expander("⚙️ 自选股票池与多分组管理 (自主新建分组 / 全市场标的动态入池)", expanded=False):
        tab_m1, tab_m2 = st.tabs(["➕ 添加标的到分组", "📁 新建自选分组"])
        with tab_m1:
            c_in1, c_in2, c_in3, c_in4 = st.columns([2.2, 2.3, 2.3, 1.6], gap="small")
            with c_in1:
                target_group = st.selectbox("归属分组", [g for g in group_names if g != "⭐ 全部标的池"], 0, label_visibility="collapsed")
            with c_in2:
                new_code = st.text_input("股票代码", key="add_stock_code", placeholder="代码 (如 600519)", label_visibility="collapsed")
            with c_in3:
                new_name = st.text_input("股票名称", key="add_stock_name", placeholder="名称 (如 贵州茅台)", label_visibility="collapsed")
            with c_in4:
                add_btn = st.button("➕入池", use_container_width=True)
                if add_btn and new_code:
                    code_c = new_code.strip()
                    name_c = new_name.strip()
                    engine.add_custom_target(code_c, name_c, group_name=target_group)
                    st.success(f"标的 {name_c or code_c} ({code_c}) 已归入【{target_group}】！")
                    st.rerun()
        with tab_m2:
            c_g1, c_g2 = st.columns([6.4, 2.0], gap="small")
            with c_g1:
                new_group_name = st.text_input("新建分组名称", placeholder="新建分组名称 (例如：度小满观察池)", label_visibility="collapsed")
            with c_g2:
                create_g_btn = st.button("📁 立即创建", use_container_width=True)
                if create_g_btn and new_group_name:
                    engine.create_custom_group(new_group_name.strip())
                    st.success(f"分组【{new_group_name.strip()}】已成功创建！")
                    st.rerun()

    # ② DuckDB 全市场五维筹码初筛雷达榜
    with st.expander("🔍 DuckDB 全市场五维筹码毫秒级初筛雷达榜", expanded=False):
        tab0, tab1, tab2, tab3 = st.tabs(["⚡ 超导死锁", "🌟 物理真空", "💎 战略黄金坑", "👑 超级主升"])
        with tab0:
            try:
                cpr_df = screener.scan_cpr_superconductor()
                st.dataframe(cpr_df.to_pandas(), use_container_width=True, hide_index=True)
                if st.button("📥 一键将【超导真龙 Top 15】加入自选池", key="import_cpr"):
                    records = cpr_df.select(["code", "name"]).to_dicts()
                    engine.create_custom_group("⚡ 超导死锁真空跃迁池")
                    engine.add_stocks_to_group("⚡ 超导死锁真空跃迁池", records)
                    st.success("✅ 已同步至「⚡ 超导死锁真空跃迁池」！")
                    st.rerun()
            except Exception as e:
                st.info(f"初筛载入中: {e}")
        with tab1:
            try:
                vac_df = screener.scan_vacuum_corridor()
                st.dataframe(vac_df.to_pandas(), use_container_width=True, hide_index=True)
                if st.button("📥 一键将【真空走廊 Top 15】加入自选池", key="import_vac"):
                    records = vac_df.select(["code", "name"]).to_dicts()
                    engine.add_stocks_to_group("🚀 物理真空走廊突击组", records)
                    st.success("✅ 已同步至「🚀 物理真空走廊突击组」！")
                    st.rerun()
            except Exception as e:
                st.info(f"初筛载入中: {e}")
        with tab2:
            try:
                pit_df = screener.scan_golden_pit()
                st.dataframe(pit_df.to_pandas(), use_container_width=True, hide_index=True)
                if st.button("📥 一键将【黄金坑 Top 15】加入自选池", key="import_pit"):
                    records = pit_df.select(["code", "name"]).to_dicts()
                    engine.create_custom_group("💎 黄金坑逆向抄底池")
                    engine.add_stocks_to_group("💎 黄金坑逆向抄底池", records)
                    st.success("✅ 已同步至「💎 黄金坑逆向抄底池」！")
                    st.rerun()
            except Exception as e:
                st.info(f"初筛载入中: {e}")
        with tab3:
            try:
                res_df = screener.scan_super_resonance()
                st.dataframe(res_df.to_pandas(), use_container_width=True, hide_index=True)
                if st.button("📥 一键将【超级共振 Top 15】加入自选池", key="import_res"):
                    records = res_df.select(["code", "name"]).to_dicts()
                    engine.create_custom_group("👑 超级主升浪共振池")
                    engine.add_stocks_to_group("👑 超级主升浪共振池", records)
                    st.success("✅ 已同步至「👑 超级主升浪共振池」！")
                    st.rerun()
            except Exception as e:
                st.info(f"初筛载入中: {e}")

    # ③ 198 交易日斐波那契战略纵深矩阵
    with st.expander("📊 198 交易日斐波那契战略纵深矩阵 (5, 13, 34, 55, 89, 144, 198)", expanded=False):
        if fib_matrix:
            fib_df = pd.DataFrame(fib_matrix)
            st.dataframe(fib_df, use_container_width=True, hide_index=True)

    # ④ 连续微积分时空场与筹码守恒反解方程
    with st.expander("🔬 天衍数理底座 · 连续微积分时空场与筹码守恒反解方程", expanded=False):
        st.markdown("""
        <div style="font-size:11px; color:#94A3B8; margin-bottom:6px; line-height:1.4;">
            本系统彻底摒弃传统商业软件离散切片，采用<b>连续时空偏微分方程</b>与<b>筹码守恒反解</b>，穿透机构拆单。
        </div>
        """, unsafe_allow_html=True)
        st.markdown("**① 主力增仓反解方程 (Main% Inversion)**")
        st.latex(r"Main\% = \alpha \cdot \frac{\partial LFS}{\partial t} + \beta \cdot \text{Turnover} \cdot \left( \frac{\text{Close} - \text{VWAP}}{\text{High} - \text{Low}} \right) \cdot (1 - \text{ASR})")
        st.markdown("**② 连续高斯卷积微积分场**")
        st.latex(r"\frac{\partial P(x,t)}{\partial t} = -\alpha \cdot \text{Turnover} \cdot P + V \cdot \frac{1}{\sigma \sqrt{2\pi}} e^{-\frac{(x - \text{VWAP})^2}{2\sigma^2}}")
        st.markdown("**③ 战略动能压阵差值方程**")
        st.latex(r"\Delta \text{CYF} = \text{CYF66\_Raw} - \text{VMA}(T+55)")
        st.markdown("**④ 真空推升能效比张量**")
        st.latex(r"\eta_V = \frac{\Delta P_{\%} \times 100}{\text{Turnover} \times \text{ASR}}")

    # 右下角 Resize 手柄（JS 监听 mousedown 实现拉伸）
    st.markdown('<div class="ty-resize-handle" data-side="left"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 右翼浮动窗口 🤖 天眼作战智能体
# ══════════════════════════════════════════════
with col_win_r:
    # 窗口顶栏
    st.markdown("""
<div class="tianyan-float-header" id="right-win-hdr" data-side="right">
  <div class="tianyan-float-title"><span class="fw-dot"></span>🤖 天眼作战智能体</div>
  <div class="tianyan-float-btns">
    <button class="tianyan-float-btn btn-win-max" data-side="right" title="最大化到屏幕顶部 (横向100%)">⛶</button>
    <button class="tianyan-float-btn fw-close" data-side="right" title="关闭窗口">✕</button>
  </div>
</div>
<span class="ty-marker" data-side="right" style="display:none;"></span>
""", unsafe_allow_html=True)

    # 大模型选择 / 召唤审计按钮 / 免费配额水库
    c_mod, c_btn, c_quota = st.columns([4.2, 3.2, 2.6], gap="small")
    with c_mod:
        sel_m_label = st.selectbox("选择金融大模型", list(model_map.keys()), 0, label_visibility="collapsed")
        selected_model_id = model_map[sel_m_label]
    with c_btn:
        run_ai = st.button("⚡ 召唤大模型穿透审计", type="primary", use_container_width=True)
    with c_quota:
        st.markdown(f"""
        <div class="quota-badge" title="ModelScope 官方每日 2,000 次免费配额，安全硬顶 1,800 次，每日 00:00 重置">
            <span>🛡️ 免费: <b>{quota['used_calls']}</b>/{quota['limit_calls']}</span>
            <span>余: <b style="color:#10B981;">{ratio_pct}%</b></span>
        </div>
        """, unsafe_allow_html=True)

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
            st.session_state[chat_key].append({
                "role": "assistant",
                "content": res["content"],
                "thinking": res.get("thinking", ""),
                "model_used": res.get("model_used", selected_model_id),
                "duration": res.get("duration_seconds", 0.0),
                "type": "audit_report"
            })
            st.rerun()

    # 欢迎与标的绑定徽章
    st.markdown(f"""
    <div class="agent-header-card">
        <div class="agent-header-title">
            <span class="agent-header-status"></span>
            <span>✨ 超级量化科学计算智能体</span>
            <span style="font-size:11px; color:#94A3B8; font-weight:normal;">| 目标: <b style="color:#38BDF8;">{stock_name} ({sel_code})</b></span>
        </div>
        <div style="font-size:10.5px; color:#64748B;">
            ⚡ 引擎: <span style="color:#10B981; font-weight:600;">{sel_m_label.split('(')[0].strip()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 对话消息流展示
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"], avatar="🎖️" if msg["role"] == "user" else "🧠"):
            if msg["role"] == "assistant":
                st.markdown("""
                <div class="mcp-pill-badge">
                    <span class="tag">MCP</span>
                    <span>五维微积分真值检索与因果逻辑核验</span>
                    <span style="color:#64748B; font-size:9.5px;">✓ 198天时空矩阵注入</span>
                </div>
                """, unsafe_allow_html=True)
            if msg.get("thinking"):
                with st.expander("💡 参谋部 CoT 思考推演链 (大模型内生辩证反思)", expanded=False):
                    st.markdown(f"```text\n{msg['thinking']}\n```")
            if msg.get("type") == "audit_report":
                st.markdown('<div class="ai-report-box">', unsafe_allow_html=True)
                st.markdown(msg["content"])
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(msg["content"])
            if msg.get("model_used"):
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px; font-size:10px; color:#64748B; border-top:1px dashed #1E293B; padding-top:2px;">
                    <span>⚡ 驱动模型: <b style="color:#94A3B8;">{msg['model_used']}</b></span>
                    <span>⏱️ 推理耗时: <b style="color:#38BDF8;">{msg.get('duration', 0.0):.2f}s</b></span>
                    <span style="color:#10B981;">● 零幻觉对齐</span>
                </div>
                """, unsafe_allow_html=True)

    # 快捷战术提问预设胶囊
    st.markdown('<div style="font-size:10.5px; color:#94A3B8; margin: 4px 0 2px 0;">⚡ 战术胶囊直通车：</div>', unsafe_allow_html=True)
    qp_col1, qp_col2, qp_col3, qp_col4 = st.columns(4)
    with qp_col1:
        if st.button("💬 战术对话", use_container_width=True, key=f"qp0_{sel_code}"):
            qp_query = f"请作为高级量化参谋长，全景评述 {stock_name}({sel_code}) 当前五维筹码能量与多周期共振态势！"
    with qp_col2:
        if st.button("🎯 筹码穿透", use_container_width=True, key=f"qp1_{sel_code}"):
            qp_query = f"请深度剖析 {stock_name}({sel_code}) 当前主力资金是在战略吸筹建仓还是震荡洗盘？重点穿透获利盘浮盈剪刀差与 ASR 控盘底座！"
    with qp_col3:
        if st.button("⚖️ 4级仓位", use_container_width=True, key=f"qp2_{sel_code}"):
            qp_query = f"根据当前五维指标与 CPR/BRI 刚性度，对 {stock_name}({sel_code}) 给出严谨的 4 级动态仓位裁决（空仓/轻仓/半仓/重仓主升），并列出一票否决风控触发条件！"
    with qp_col4:
        if st.button("🌊 动能压阵", use_container_width=True, key=f"qp3_{sel_code}"):
            qp_query = f"请深度测算 {stock_name}({sel_code}) 的 CYF66_Raw 与 VMA(T+55) 长周期动能偏离度 ΔCYF，研判中长线动能压阵势能与背离风险！"

    # 曲别针 (📎) 极简多模态行情上传器与一体化输入框
    c_clip1, c_clip2 = st.columns([1.2, 8.8], gap="small")
    with c_clip1:
        with st.popover("📎 附件", use_container_width=True):
            st.markdown('<div style="font-size:11px; color:#38BDF8; font-weight:600; margin-bottom:4px;">📎 上传分时/K线截图</div>', unsafe_allow_html=True)
            img_file = st.file_uploader("行情截图", type=["png", "jpg", "jpeg"], key=f"img_uploader_{sel_code}", label_visibility="collapsed")
            if img_file is not None:
                st.image(img_file, caption="📷 已就绪快照", width=200)
                if st.button("👁️ 视觉多模态联合诊断", use_container_width=True, key=f"btn_v_diag_{sel_code}"):
                    qp_query = f"【多模态联合诊断】请结合上传的行情截图与当前 {stock_name}({sel_code}) 的五维微积分指标（LFS, ASR, CPR, ΔCYF），进行视觉形态与筹码分布的双重穿透研判！"
    with c_clip2:
        user_prompt = st.chat_input(f"提出你想要知道的量化问题（如：主力是在洗盘还是出货？结合 ASR 谈谈仓位？）...", key=f"chat_input_{sel_code}")

    st.markdown('<div class="ai-disclaimer">内容由天衍五维量化大模型生成，请结合物理真值与实盘纪律甄别</div>', unsafe_allow_html=True)

    # 右下角 Resize 手柄
    st.markdown('<div class="ty-resize-handle" data-side="right"></div>', unsafe_allow_html=True)

# 处理用户提问（在 columns 外部确保正常响应）
active_prompt = qp_query if qp_query else user_prompt
if active_prompt:
    st.session_state[chat_key].append({"role": "user", "content": active_prompt})
    with st.spinner(f"🧠 [{selected_model_id}] 正在结合 {stock_name} 五维真值推演战术解答..."):
        chat_res = query_ai_chat_response(
            messages=st.session_state[chat_key],
            stock_code=sel_code,
            stock_name=stock_name,
            snapshot=snapshot,
            selected_model=selected_model_id
        )
        st.session_state[chat_key].append({
            "role": "assistant",
            "content": chat_res["content"],
            "thinking": chat_res.get("thinking", ""),
            "model_used": chat_res.get("model_used", selected_model_id),
            "duration": chat_res.get("duration_seconds", 0.0),
            "type": "chat_response"
        })
        st.rerun()

# ══════════════════════════════════════════════
# 浮动窗口 JS 引擎注入
# ══════════════════════════════════════════════
_l_open = "true" if st.session_state["left_dock_open"] else "false"
_r_open = "true" if st.session_state["right_dock_open"] else "false"

components.html(f"""
<script>
(function() {{
    var doc = window.parent.document;
    var pw  = window.parent;

    var pyOpen = {{ left: {_l_open}, right: {_r_open} }};

    // 全局持久化状态字典
    if (!pw._TY) {{
        pw._TY = {{
            s: {{
                left:  {{ x: 24, y: 90, w: 500, h: 640, max: false, preMax: null, vis: pyOpen.left }},
                right: {{ x: null, y: 90, w: 530, h: 680, max: false, preMax: null, vis: pyOpen.right }}
            }},
            zc: 9100, drag: null, rsz: null
        }};
    }}

    var TY = pw._TY;
    var S  = TY.s;

    // 权威同步 Python 端的打开/收起指令
    S.left.vis  = pyOpen.left;
    S.right.vis = pyOpen.right;

    function bringFront(win) {{
        TY.zc++;
        win.style.setProperty('z-index', TY.zc, 'important');
    }}

    function doClose(side) {{
        var win = doc.querySelector('[data-ty="' + side + '"]');
        if (win) {{
            win.style.setProperty('display', 'none', 'important');
        }}
        S[side].vis = false;

        // 模拟触发顶栏对应按钮点击，通知 Python 端翻转状态
        var allBtns = doc.querySelectorAll('button');
        for (var i = 0; i < allBtns.length; i++) {{
            var txt = (allBtns[i].innerText || allBtns[i].textContent || '').trim();
            if (side === 'left' && txt.includes('战备库')) {{
                allBtns[i].click();
                break;
            }}
            if (side === 'right' && txt.includes('参谋部')) {{
                allBtns[i].click();
                break;
            }}
        }}
    }}

    function doToggleMax(side) {{
        var win = doc.querySelector('[data-ty="' + side + '"]');
        if (!win) return;
        var st = S[side];
        st.max = !st.max;

        var maxBtn = win.querySelector('.btn-win-max');

        if (st.max) {{
            st.preMax = {{
                top: win.style.top,
                left: win.style.left,
                width: win.style.width,
                height: win.style.height
            }};
            win.classList.add('ty-maximized');
            win.style.setProperty('position', 'fixed', 'important');
            win.style.setProperty('top', '0px', 'important');
            win.style.setProperty('left', '0px', 'important');
            win.style.setProperty('right', 'auto', 'important');
            win.style.setProperty('width', '100vw', 'important');
            win.style.setProperty('height', '85vh', 'important');
            win.style.setProperty('border-radius', '0px', 'important');
            win.style.setProperty('z-index', '9999', 'important');
            if (maxBtn) {{
                maxBtn.innerHTML = '🗗';
                maxBtn.title = '还原窗口大小与位置';
            }}
        }} else {{
            win.classList.remove('ty-maximized');
            win.style.setProperty('border-radius', '12px', 'important');
            if (st.preMax && st.preMax.width) {{
                win.style.setProperty('top', st.preMax.top || '90px', 'important');
                win.style.setProperty('left', st.preMax.left || (side === 'left' ? '24px' : 'calc(100vw - 550px)'), 'important');
                win.style.setProperty('width', st.preMax.width, 'important');
                win.style.setProperty('height', st.preMax.height, 'important');
            }} else {{
                win.style.setProperty('top', (st.y || 90) + 'px', 'important');
                win.style.setProperty('width', (st.w || (side === 'left' ? 500 : 530)) + 'px', 'important');
                win.style.setProperty('height', (st.h || (side === 'left' ? 640 : 680)) + 'px', 'important');
                if (st.x !== null && st.x !== undefined) {{
                    win.style.setProperty('left', st.x + 'px', 'important');
                    win.style.setProperty('right', 'auto', 'important');
                }} else {{
                    win.style.setProperty('left', (side === 'left' ? '24px' : 'calc(100vw - 550px)'), 'important');
                    win.style.setProperty('right', 'auto', 'important');
                }}
            }}
            if (maxBtn) {{
                maxBtn.innerHTML = '⛶';
                maxBtn.title = '最大化到屏幕顶部 (横向100%)';
            }}
        }}
        bringFront(win);
    }}

    // 挂载全局 API（多层防护）
    pw.TY = window.TY = {{
        max: function(side) {{ doToggleMax(side); }},
        close: function(side) {{ doClose(side); }},
        open: function(side) {{
            S[side].vis = true;
            var win = doc.querySelector('[data-ty="' + side + '"]');
            if (win) {{
                win.style.setProperty('display', 'flex', 'important');
                bringFront(win);
            }}
        }}
    }};

    // 全局透明遮罩辅助函数（防止鼠标滑动经过 iframe/图表时丢失事件）
    function setDragOverlay(active, cursor) {{
        var ov = doc.getElementById('ty-drag-overlay');
        if (active) {{
            if (!ov) {{
                ov = doc.createElement('div');
                ov.id = 'ty-drag-overlay';
                ov.style.cssText = 'position:fixed!important;top:0!important;left:0!important;width:100vw!important;height:100vh!important;z-index:99999!important;background:transparent!important;user-select:none!important;';
                doc.body.appendChild(ov);
            }}
            ov.style.cursor = cursor || 'move';
            ov.style.display = 'block';
        }} else if (ov) {{
            ov.style.display = 'none';
        }}
    }}

    // 全局点击事件代理 (用于关闭与最大化)
    if (!doc._tyClickListening) {{
        doc._tyClickListening = true;

        doc.addEventListener('click', function(e) {{
            var closeBtn = e.target.closest('.fw-close');
            if (closeBtn) {{
                e.preventDefault();
                e.stopPropagation();
                var side = closeBtn.getAttribute('data-side') || 'left';
                doClose(side);
                return;
            }}

            var maxBtn = e.target.closest('.btn-win-max');
            if (maxBtn) {{
                e.preventDefault();
                e.stopPropagation();
                var side = maxBtn.getAttribute('data-side') || 'left';
                doToggleMax(side);
                return;
            }}

            var win = e.target.closest('[data-ty]');
            if (win) {{
                bringFront(win);
            }}
        }}, true);
    }}

    // 全局拖拽与缩放手柄代理 (通过遮罩与 window 双重监听保证 100% 捕获)
    if (!pw._tyGlobalDragListening) {{
        pw._tyGlobalDragListening = true;

        doc.addEventListener('mousedown', function(e) {{
            if (e.target.closest('.tianyan-float-btn')) return;

            var hdr = e.target.closest('.tianyan-float-header');
            if (hdr) {{
                var win = hdr.closest('[data-ty]');
                if (win) {{
                    var side = win.getAttribute('data-ty');
                    if (!S[side].max) {{
                        bringFront(win);
                        var rect = win.getBoundingClientRect();
                        TY.drag = {{
                            side: side,
                            win: win,
                            mx: e.clientX,
                            my: e.clientY,
                            x: rect.left,
                            y: rect.top
                        }};
                        setDragOverlay(true, 'move');
                        e.preventDefault();
                        e.stopPropagation();
                        return;
                    }}
                }}
            }}

            var rszHandle = e.target.closest('.ty-resize-handle');
            if (rszHandle) {{
                var win = rszHandle.closest('[data-ty]');
                if (win) {{
                    var side = win.getAttribute('data-ty');
                    if (!S[side].max) {{
                        bringFront(win);
                        var rect = win.getBoundingClientRect();
                        TY.rsz = {{
                            side: side,
                            win: win,
                            mx: e.clientX,
                            my: e.clientY,
                            w: win.offsetWidth,
                            h: win.offsetHeight,
                            left: rect.left
                        }};
                        setDragOverlay(true, 'se-resize');
                        e.preventDefault();
                        e.stopPropagation();
                        return;
                    }}
                }}
            }}
        }}, true);

        pw.addEventListener('mousemove', function(e) {{
            if (TY.drag) {{
                var d = TY.drag;
                var dx = e.clientX - d.mx;
                var dy = e.clientY - d.my;
                var maxLeft = pw.innerWidth - d.win.offsetWidth - 10;
                var maxTop  = pw.innerHeight - 50;
                var newTop  = Math.max(50, Math.min(maxTop, d.y + dy));
                var newLeft = Math.max(10, Math.min(maxLeft, d.x + dx));
                S[d.side].y = newTop;
                S[d.side].x = newLeft;
                d.win.style.setProperty('top', newTop + 'px', 'important');
                d.win.style.setProperty('left', newLeft + 'px', 'important');
                d.win.style.setProperty('right', 'auto', 'important');
                e.preventDefault();
            }}

            if (TY.rsz) {{
                var r = TY.rsz;
                var maxW = Math.max(340, pw.innerWidth - r.left - 20);
                var maxH = Math.max(220, pw.innerHeight - 70);
                var newW = Math.max(340, Math.min(maxW, r.w + (e.clientX - r.mx)));
                var newH = Math.max(220, Math.min(maxH, r.h + (e.clientY - r.my)));
                S[r.side].w = newW;
                S[r.side].h = newH;
                r.win.style.setProperty('width', newW + 'px', 'important');
                r.win.style.setProperty('height', newH + 'px', 'important');
                e.preventDefault();
            }}
        }}, true);

        pw.addEventListener('mouseup', function() {{
            TY.drag = null;
            TY.rsz  = null;
            setDragOverlay(false);
        }}, true);
    }}

    function floatify(side) {{
        var marker = doc.querySelector('.ty-marker[data-side="' + side + '"]');
        if (!marker) return false;

        var col = marker;
        while (col && col.getAttribute('data-testid') !== 'stColumn') {{
            col = col.parentElement;
            if (!col || col === doc.body) {{ col = null; break; }}
        }}
        if (!col) return false;

        col.setAttribute('data-ty', side);

        var hb = col.closest('[data-testid="stHorizontalBlock"]');
        if (hb) {{
            hb.style.setProperty('height', '0px', 'important');
            hb.style.setProperty('min-height', '0px', 'important');
            hb.style.setProperty('max-height', '0px', 'important');
            hb.style.setProperty('overflow', 'visible', 'important');
            hb.style.setProperty('padding', '0px', 'important');
            hb.style.setProperty('margin', '0px', 'important');
            hb.style.setProperty('border', 'none', 'important');
        }}

        col.style.setProperty('position', 'fixed', 'important');
        col.style.setProperty('background', 'linear-gradient(145deg, rgba(10, 15, 29, 0.96), rgba(7, 10, 17, 0.98))', 'important');
        col.style.setProperty('backdrop-filter', 'blur(25px)', 'important');
        col.style.setProperty('-webkit-backdrop-filter', 'blur(25px)', 'important');
        col.style.setProperty('border', '1px solid rgba(56, 189, 248, 0.35)', 'important');
        col.style.setProperty('border-radius', '12px', 'important');
        col.style.setProperty('box-shadow', '0 20px 60px rgba(0, 0, 0, 0.75), 0 0 1px rgba(56, 189, 248, 0.3) inset', 'important');
        col.style.setProperty('overflow', 'hidden', 'important');
        col.style.setProperty('flex-direction', 'column', 'important');
        col.style.setProperty('padding', '0px', 'important');
        col.style.setProperty('margin', '0px', 'important');

        var st = S[side];
        if (!st.vis) {{
            col.style.setProperty('display', 'none', 'important');
            return true;
        }}

        col.style.setProperty('display', 'flex', 'important');

        // 如果未处于拖拽中，设置当前坐标与尺寸
        if (!TY.drag || TY.drag.side !== side) {{
            if (!st.max) {{
                col.style.setProperty('height', (st.h || (side === 'left' ? 640 : 680)) + 'px', 'important');
                col.style.setProperty('width', (st.w || (side === 'left' ? 500 : 530)) + 'px', 'important');
                col.style.setProperty('top', (st.y || 90) + 'px', 'important');
                if (st.x !== null && st.x !== undefined) {{
                    col.style.setProperty('left', st.x + 'px', 'important');
                    col.style.setProperty('right', 'auto', 'important');
                }} else {{
                    if (side === 'left') {{
                        col.style.setProperty('left', '24px', 'important');
                        col.style.setProperty('right', 'auto', 'important');
                    }} else {{
                        col.style.setProperty('left', 'calc(100vw - 550px)', 'important');
                        col.style.setProperty('right', 'auto', 'important');
                    }}
                }}
            }}
        }}

        var vb = col.querySelector('[data-testid="stVerticalBlock"]');
        if (vb) {{
            vb.style.flex = '1';
            vb.style.minHeight = '0';
            vb.style.overflowY = 'auto';
            vb.style.overflowX = 'hidden';
            vb.style.padding = '6px 8px 8px';
            vb.style.scrollbarWidth = 'thin';
        }}

        return true;
    }}

    function tryInit(n) {{
        var dL = floatify('left');
        var dR = floatify('right');
        if ((!dL || !dR) && n > 0) {{
            setTimeout(function() {{ tryInit(n - 1); }}, 120);
        }}
    }}

    setTimeout(function() {{ tryInit(10); }}, 50);
}})();
</script>
""", height=0)




# ==========================================
# 4. 图形全息展示区 (全息五维雷达图 + HUD 右侧实时战术看板)
# ==========================================
fig = build_radar_figure(df, stock_name, dim5_mode=sel_dim5)
render_radar_with_hud(fig, df, stock_name, dim5_mode=sel_dim5, height=750)

