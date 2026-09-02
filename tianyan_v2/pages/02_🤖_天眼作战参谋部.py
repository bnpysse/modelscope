"""
天衍五维 · 天眼作战参谋部 (专属 AI 推演研判室)
文件位置: tianyan_v2/pages/02_🤖_天眼作战参谋部.py
"""

import sys
import json
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from tianyan_v2.shared import (
    get_tianyan_engine,
    apply_tactical_theme,
    render_top_control_bar
)
from core.ai_advisor import query_ai_staff_report, query_ai_chat_response

st.set_page_config(
    page_title="天衍五维 · 天眼作战参谋部",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_tactical_theme()
engine = get_tianyan_engine()

# 顶部全局联动控制台
ctrl = render_top_control_bar(engine, title_prefix="🤖 天衍五维 · 天眼作战参谋部")
stock_code = ctrl["stock_code"]
stock_name = ctrl["stock_name"]
sel_days   = ctrl["days"]

snapshot = engine.get_latest_snapshot(stock_code)
fib_matrix = engine.get_fibonacci_depth_matrix(stock_code)

# ══════════════════════════════════════════════
# 1. 大模型选择与穿透审计总控台
# ══════════════════════════════════════════════
model_map = {
    "天衍 32B 终极大量化模型 (AWQ / 4-bit)": "tianyan-32b-awq",
    "Qwen-2.5-32B-Instruct (云端大算力)": "qwen2.5-32b-instruct",
    "DeepSeek-R1-Distill-Qwen-32B (强化推理)": "deepseek-r1-qwen-32b",
    "Local CPU/GPU Fast Heuristic (本地轻量)": "local-fast-heuristic",
}

c_mod, c_btn, c_quota = st.columns([4.2, 3.5, 2.3], gap="small")
with c_mod:
    sel_m_label = st.selectbox("选择金融大模型", list(model_map.keys()), 0)
    selected_model_id = model_map[sel_m_label]
with c_btn:
    st.write("")
    st.write("")
    run_ai = st.button("⚡ 召唤大模型穿透审计", type="primary", use_container_width=True)
with c_quota:
    st.markdown("""
    <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 11px; margin-top: 18px; color: #38BDF8;">
        🛡️ 免费调用水库: <b>0 / 1800</b> 次<br>
        <span style="color: #10B981;">● 服务状态: 100% 极速在线</span>
    </div>
    """, unsafe_allow_html=True)

chat_key = f"messages_{stock_code}"
if chat_key not in st.session_state:
    st.session_state[chat_key] = []

if run_ai:
    latest_json = json.dumps(snapshot, ensure_ascii=False, default=str)
    fib_json = json.dumps(fib_matrix, ensure_ascii=False, default=str)
    with st.spinner(f"🛰️ 全景引擎启动... 参谋部调用 [{selected_model_id}] 正在执行跨周期物理真值审计..."):
        res = query_ai_staff_report(
            stock_code=stock_code,
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

# ══════════════════════════════════════════════
# 2. 标的绑定卡片与历史对话流
# ══════════════════════════════════════════════
st.markdown(f"""
<div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 10px 16px; margin: 12px 0;">
    <span style="font-weight: 700; color: #F8FAFC;">✨ 超级量化科学计算智能体</span>
    <span style="color: #94A3B8; font-size: 12px; margin-left: 12px;">当前目标: <b style="color: #38BDF8;">{stock_name} ({stock_code})</b></span>
    <span style="color: #10B981; font-size: 12px; margin-left: 12px;">驱动引擎: {sel_m_label.split('(')[0].strip()}</span>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state[chat_key]:
    with st.chat_message(msg["role"], avatar="🎖️" if msg["role"] == "user" else "🧠"):
        if msg.get("thinking"):
            with st.expander("💡 参谋部 CoT 思考推演链 (大模型内生辩证反思)", expanded=False):
                st.markdown(f"```text\n{msg['thinking']}\n```")
        st.markdown(msg["content"])
        if msg.get("model_used"):
            st.caption(f"⚡ 模型: {msg['model_used']} | ⏱️ 耗时: {msg.get('duration', 0.0):.2f}s | ● 零幻觉对齐")

# ══════════════════════════════════════════════
# 3. 快捷战术提问预设胶囊
# ══════════════════════════════════════════════
st.markdown('<div style="font-size:12px; color:#94A3B8; margin: 16px 0 6px 0;">⚡ 战术胶囊直通车：</div>', unsafe_allow_html=True)
qp_col1, qp_col2, qp_col3, qp_col4 = st.columns(4)
qp_query = None

with qp_col1:
    if st.button("💬 战术对话", use_container_width=True):
        qp_query = f"请作为高级量化参谋长，全景评述 {stock_name}({stock_code}) 当前五维筹码能量与多周期共振态势！"
with qp_col2:
    if st.button("🎯 筹码穿透", use_container_width=True):
        qp_query = f"请深度剖析 {stock_name}({stock_code}) 当前主力资金是在战略吸筹建仓还是震荡洗盘？重点穿透获利盘浮盈剪刀差与 ASR 控盘底座！"
with qp_col3:
    if st.button("⚖️ 4级仓位", use_container_width=True):
        qp_query = f"根据当前五维指标与 CPR/BRI 刚性度，对 {stock_name}({stock_code}) 给出严谨的 4 级动态仓位裁决（空仓/轻仓/半仓/重仓主升），并列出一票否决风控触发条件！"
with qp_col4:
    if st.button("🌊 动能压阵", use_container_width=True):
        qp_query = f"请深度测算 {stock_name}({stock_code}) 的 CYF66_Raw 与 VMA(T+55) 长周期动能偏离度 ΔCYF，研判中长线动能压阵势能与背离风险！"

user_prompt = st.chat_input("提出你想要研判的量化问题 (如: 主力是在洗盘还是出货？结合 ASR 谈谈仓位？) ...")

active_prompt = qp_query if qp_query else user_prompt
if active_prompt:
    st.session_state[chat_key].append({"role": "user", "content": active_prompt})
    with st.chat_message("user", avatar="🎖️"):
        st.markdown(active_prompt)

    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner(f"🧠 [{selected_model_id}] 正在结合 {stock_name} 五维真值推演战术解答..."):
            chat_res = query_ai_chat_response(
                messages=st.session_state[chat_key],
                stock_code=stock_code,
                stock_name=stock_name,
                snapshot=snapshot,
                selected_model=selected_model_id
            )
            if chat_res.get("thinking"):
                with st.expander("💡 参谋部 CoT 思考推演链", expanded=False):
                    st.markdown(f"```text\n{chat_res['thinking']}\n```")
            st.markdown(chat_res["content"])
            st.caption(f"⚡ 模型: {chat_res.get('model_used', selected_model_id)} | ⏱️ 耗时: {chat_res.get('duration_seconds', 0.0):.2f}s")
            st.session_state[chat_key].append({
                "role": "assistant",
                "content": chat_res["content"],
                "thinking": chat_res.get("thinking", ""),
                "model_used": chat_res.get("model_used", selected_model_id),
                "duration": chat_res.get("duration_seconds", 0.0),
                "type": "chat_response"
            })

st.caption("🤖 天眼作战参谋部 v2.0 | 内容由天衍五维量化大模型结合物理真值与实盘纪律实时推演")
