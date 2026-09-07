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
    from core.user_preference import get_user_preference
    prefs = get_user_preference()
    defaults = {
        "selected_group": prefs.get("selected_group", "🎯 指南针实盘真值持仓组"),
        "selected_stock_code": "001309",
        "selected_stock_name": "德明利",
        "selected_days": prefs.get("selected_days", 55),
        "selected_dim5": 0,
        "chat_messages": [],
        "ai_auto_audit": False,
        "active_capsule": None,
        "data_source_mode": prefs.get("data_source_mode", "compass_ocr"),
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

    st.markdown('''<style>
    /* 缩小全局下拉框字体，防止过长截断 */
    div[data-baseweb="select"] { font-size: 13px !important; }
    div[data-baseweb="select"] ul { font-size: 13px !important; }
    </style>''', unsafe_allow_html=True)

    init_shared_state()
    groups_dict = engine.get_groups()
    group_names = ["⭐ 全部标的池"] + [g for g in groups_dict.keys() if g != "⭐ 全部标的池"]

    curr_group = st.session_state.get("selected_group", "⭐ 全部标的池")
    if curr_group not in group_names:
        curr_group = "⭐ 全部标的池"

    c_logo, c_ds, c_grp, c_stock, c_fib, c_d5 = st.columns([1.8, 2.3, 2.3, 2.0, 1.6, 2.0], gap="small")

    with c_logo:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; height: 38px;">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10B981; box-shadow:0 0 10px #10B981;"></span>
            <span style="font-size: 15px; font-weight: 800; letter-spacing: 0.05em; background: linear-gradient(90deg, #38BDF8, #818CF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{title_prefix}</span>
        </div>
        """, unsafe_allow_html=True)

    with c_ds:
        from core.user_preference import save_user_preference
        ds_opts = {
            "🎯 指南针真值 (OCR)": "compass_ocr",
            "⚡ 微分推导 (DuckDB)": "duckdb"
        }
        ds_labels = list(ds_opts.keys())
        curr_mode = st.session_state.get("data_source_mode", "compass_ocr")
        ds_idx = 0 if curr_mode == "compass_ocr" else 1
        sel_ds_label = st.selectbox("基座", ds_labels, index=ds_idx, key="top_data_source_sel", label_visibility="collapsed")
        chosen_mode = ds_opts[sel_ds_label]
        if chosen_mode != st.session_state.get("data_source_mode"):
            st.session_state["data_source_mode"] = chosen_mode
            save_user_preference("data_source_mode", chosen_mode)
            st.rerun()

    with c_grp:
        sel_group = st.selectbox("分组", group_names, index=group_names.index(curr_group), key="top_group_sel", label_visibility="collapsed")
        if sel_group != st.session_state["selected_group"]:
            st.session_state["selected_group"] = sel_group
            save_user_preference("selected_group", sel_group)
            st.rerun()

    pool_targets = engine.get_targets(None if sel_group == "⭐ 全部标的池" else sel_group)

    code_to_name = {}
    for t in pool_targets:
        c = getattr(t, "code", None) or (t.get("code") if isinstance(t, dict) else str(t))
        n = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else c)
        code_to_name[str(c)] = str(n)

    if not code_to_name:
        code_to_name = {"300475": "香农芯创"}

    curr_code = st.session_state.get("selected_stock_code", "001309")
    all_codes = list(code_to_name.keys())
    if curr_code not in all_codes:
        curr_code = all_codes[0]
        st.session_state["selected_stock_code"] = curr_code
        st.session_state["selected_stock_name"] = code_to_name.get(curr_code, curr_code)

    c_idx = all_codes.index(curr_code)

    with c_stock:
        stock_sel_key = f"top_stock_sel_{sel_group}"
        sel_code = st.selectbox("标的", all_codes, index=c_idx, format_func=lambda c: f"{code_to_name.get(c, c)} ({c})", key=stock_sel_key, label_visibility="collapsed")
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
        curr_days = st.session_state.get("selected_days", 55)
        f_idx = fib_v.index(curr_days) if curr_days in fib_v else 4
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
        "group": st.session_state["selected_group"],
        "data_source_mode": st.session_state.get("data_source_mode", "compass_ocr")
    }


def render_quota_badge(as_popover: bool = True):
    """
    渲染 ModelScope 大模型每日免费配额监控徽章 / 弹窗控制台
    - 每日安全硬锁：1,800 次 (官方 2,000 次，预留 10% 缓冲)
    - 零扣费硬保护状态展示
    - Token 消耗与各模型细分明细
    """
    import pandas as pd
    from core.providers.modelscope_client import modelscope_client
    
    try:
        quota_st = modelscope_client.get_quota_status()
    except Exception as e:
        quota_st = {
            "date": "今日",
            "used_calls": 0,
            "limit_calls": 1800,
            "remaining_calls": 1800,
            "remaining_ratio": 1.0,
            "total_tokens": 0,
            "is_safe": True,
            "models": []
        }

    u_calls = quota_st.get("used_calls", 0)
    l_calls = quota_st.get("limit_calls", 1800)
    r_calls = quota_st.get("remaining_calls", 1800)
    r_ratio = quota_st.get("remaining_ratio", 1.0)
    total_tokens = quota_st.get("total_tokens", 0)

    # 状态指示
    status_dot = "🟢" if r_ratio > 0.3 else ("🟡" if r_ratio > 0.1 else "🔴")
    pop_btn_text = f"🛡️ 配额: {u_calls}/{l_calls} ({status_dot}余{r_calls})"

    if as_popover:
        with st.popover(pop_btn_text, help="ModelScope 每日 1,800 次免费配额与零扣费安全硬锁监控", use_container_width=True):
            st.markdown("#### 🛡️ ModelScope 免费算力水库与预算门神")
            st.caption(f"📅 统计周期: {quota_st.get('date')} | 每日 00:00 自动重置")

            # 配额余量进度条
            st.progress(r_ratio, text=f"可用余量: {round(r_ratio * 100, 1)}% (剩余 {r_calls} / {l_calls} 次)")

            m_c1, m_c2 = st.columns(2)
            official_used = quota_st.get("official_used_calls")
            local_used = quota_st.get("local_used_calls", u_calls)
            with m_c1:
                st.metric("官方全账号已用", f"{u_calls} 次", help="与 ModelScope 官方云端实时同步的全账号今日总调用量")
            with m_c2:
                st.metric("本地天衍调用", f"{local_used} 次", help=f"本地天衍系统今日贡献的调用量 (累计消耗 {total_tokens:,} Tokens)")

            st.markdown("---")
            st.markdown("**🛡️ 权威真值校准与零费用硬锁机制**")
            st.info(
                "• **官方真值校准**: 已直连 ModelScope 官方用量接口 (`/api/v1/inference/rate-limit`)，全账号当日用量与魔搭后台 100% 同步。\n"
                "• **安全硬锁**: 系统内置 `ModelScopeBudgetGuard` 守护门神，设置 **1,800 次/天** 物理硬顶（官方上限 2,000 次），达标后直接硬拦截，**100% 杜绝任何超额扣费**。\n"
                "• **本地细分审计**: 本地 SQLite (`modelscope_budget.db`) 精准记录各模型调用分布与 Token 明细。"
            )

            models_data = quota_st.get("models", [])
            if models_data:
                st.markdown("**📊 今日各模型调用细分**")
                m_df = pd.DataFrame(models_data)
                m_df.columns = ["模型名称", "调用次数", "Token 消耗"]
                st.dataframe(m_df, use_container_width=True, hide_index=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(15, 23, 42, 0.8)); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 6px; padding: 6px 10px; font-size: 11px; color: #94A3B8;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <span style="color:#6EE7B7; font-weight:700;">🛡️ ModelScope 配额</span>
                <span style="color:{'#10B981' if r_ratio>0.3 else '#EF4444'}; font-weight:700;">{status_dot} 零扣费硬锁</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:10px; color:#CBD5E1;">
                <span>已用: <b style="color:#F59E0B;">{u_calls}</b> / {l_calls} 次</span>
                <span>余: <b style="color:#10B981;">{r_calls}</b> 次 ({round(r_ratio*100, 1)}%)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

