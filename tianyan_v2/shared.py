"""
天衍五维 · 下一代现代化多页面架构共享核心总线
文件位置: tianyan_v2/shared.py
"""

import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from core.engine import create_engine
from core.models import FIB_PERIODS

@st.cache_resource
def get_tianyan_engine():
    return create_engine(PROJECT_ROOT)

def init_shared_state():
    defaults = {
        "selected_group": "⭐ 全部标的池",
        "selected_stock_code": "300475",
        "selected_stock_name": "香农芯创",
        "selected_days": 34,
        "selected_dim5": 0,
        "chat_messages": [],
        "ai_auto_audit": False,
        "active_capsule": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def apply_tactical_theme():
    st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 50% 0%, #0d1527 0%, #060913 100%) !important;
    color: #E2E8F0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 98% !important;
}

.tactical-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-left: 4px solid #EF4444;
    border-radius: 8px;
    padding: 8px 16px;
    margin-bottom: 12px;
    font-size: 13px;
    color: #F87171;
}

.indicator-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 6px;
    margin-bottom: 12px;
}
.indicator-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 6px 10px;
    transition: all 0.2s ease;
}
.indicator-card:hover {
    border-color: rgba(56, 189, 248, 0.5);
    background: rgba(15, 23, 42, 0.9);
}
.indicator-title {
    font-size: 10px;
    color: #94A3B8;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.indicator-val {
    font-size: 14px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.indicator-sub {
    font-size: 9px;
    color: #64748B;
}

button[kind="primary"] {
    background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4) !important;
}
button[kind="secondary"] {
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}
</style>
""", unsafe_allow_html=True)

def render_top_control_bar(engine, title_prefix="🛸 天衍五维"):
    init_shared_state()
    custom_groups = engine.get_custom_groups()
    group_names = ["⭐ 全部标的池"] + list(custom_groups.keys())

    curr_group = st.session_state.get("selected_group", "⭐ 全部标的池")
    if curr_group not in group_names:
        curr_group = "⭐ 全部标的池"

    c_logo, c_grp, c_stock, c_fib, c_d5 = st.columns([2.8, 1.8, 2.2, 1.8, 2.2], gap="small")

    with c_logo:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; height: 38px;">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10B981; box-shadow:0 0 10px #10B981;"></span>
            <span style="font-size: 15px; font-weight: 800; letter-spacing: 0.05em; background: linear-gradient(90deg, #38BDF8, #818CF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{title_prefix}</span>
        </div>
        """, unsafe_allow_html=True)

    with c_grp:
        sel_group = st.selectbox("分组", group_names, index=group_names.index(curr_group), key="top_group_sel", label_visibility="collapsed")
        if sel_group != st.session_state["selected_group"]:
            st.session_state["selected_group"] = sel_group
            st.rerun()

    if sel_group == "⭐ 全部标的池":
        pool_targets = engine.get_all_targets()
    else:
        pool_targets = custom_groups.get(sel_group, [])

    code_to_name = {t["code"]: t.get("name", t["code"]) for t in pool_targets}
    if not code_to_name:
        code_to_name = {"300475": "香农芯创"}

    curr_code = st.session_state.get("selected_stock_code", "300475")
    all_codes = list(code_to_name.keys())
    c_idx = all_codes.index(curr_code) if curr_code in all_codes else 0

    with c_stock:
        sel_code = st.selectbox("标的", all_codes, index=c_idx, format_func=lambda c: f"{code_to_name.get(c, c)} ({c})", key="top_stock_sel", label_visibility="collapsed")
        if sel_code != st.session_state["selected_stock_code"]:
            st.session_state["selected_stock_code"] = sel_code
            st.session_state["selected_stock_name"] = code_to_name.get(sel_code, sel_code)
            st.rerun()

    with c_fib:
        fib_l = [n for n, _ in FIB_PERIODS]
        fib_v = [v for _, v in FIB_PERIODS]
        if "200日 (年线大波段)" not in fib_l:
            fib_l.append("200日 (年线大波段)")
            fib_v.append(200)
        curr_days = st.session_state.get("selected_days", 34)
        f_idx = fib_v.index(curr_days) if curr_days in fib_v else 3
        sel_f_idx = st.selectbox("周期", range(len(fib_l)), index=f_idx, format_func=lambda i: fib_l[i], key="top_fib_sel", label_visibility="collapsed")
        if fib_v[sel_f_idx] != st.session_state["selected_days"]:
            st.session_state["selected_days"] = fib_v[sel_f_idx]
            st.rerun()

    with c_d5:
        d5_opts = {
            "🌊 5+20日多维共振": 0,
            "⚡ 5日短线游资": 5,
            "📊 10日波段中枢": 10,
            "🛡️ 20日标准月线": 20,
        }
        d5_vals = list(d5_opts.values())
        curr_d5 = st.session_state.get("selected_dim5", 0)
        d_idx = d5_vals.index(curr_d5) if curr_d5 in d5_vals else 0
        sel_d5_lbl = st.selectbox("维度", list(d5_opts.keys()), index=d_idx, key="top_d5_sel", label_visibility="collapsed")
        if d5_opts[sel_d5_lbl] != st.session_state["selected_dim5"]:
            st.session_state["selected_dim5"] = d5_opts[sel_d5_lbl]
            st.rerun()

    return {
        "stock_code": st.session_state["selected_stock_code"],
        "stock_name": st.session_state["selected_stock_name"],
        "days": st.session_state["selected_days"],
        "dim5": st.session_state["selected_dim5"],
        "group": st.session_state["selected_group"]
    }
