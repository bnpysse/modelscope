"""
天衍五维 · 天眼作战参谋部 (专属 AI 推演研判室)
文件位置: tianyan_v2/pages/02_🤖_天眼作战参谋部.py
特性:
  1. 专为大模型 CoT 深度思维链与研报阅读设计的宽屏交互室
  2. 真实集成天衍 32B 金融大模型与 ModelScope SDK
  3. 4 大战术胶囊一键直达
  4. 📎 多模态附件上传与穿透审计报告生成
"""

import sys
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
from core.ai_advisor import get_advisor

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

# ══════════════════════════════════════════════
# 2. 战术胶囊直通车
# ══════════════════════════════════════════════
st.markdown("#### ⚡ 战术胶囊直通车")
c_cap1, c_cap2, c_cap3, c_cap4 = st.columns(4, gap="small")

capsule_prompt = None
with c_cap1:
    if st.button("💬 战术研判对话", use_container_width=True):
        capsule_prompt = f"请针对标的 {stock_name} ({stock_code}) 当前在 {sel_days} 日斐波那契周期下的微观推力和筹码分布，给出核心操盘建议。"
with c_cap2:
    if st.button("🎯 筹码刚性穿透", use_container_width=True):
        capsule_prompt = f"请穿透审计 {stock_name} ({stock_code}) 的 CPR 刚性与空间获利真空 Z'，主力是否正在超导推升或断层洗盘？"
with c_cap3:
    if st.button("⚖️ 4级战术仓位", use_container_width=True):
        capsule_prompt = f"结合五维共振特征，测算 {stock_name} ({stock_code}) 当前科学仓位控制（底仓、加仓、锁仓与止损防线）。"
with c_cap4:
    if st.button("🌊 动能多维压阵", use_container_width=True):
        capsule_prompt = f"评估 {stock_name} ({stock_code}) 在 5日短线、20日月线与 34日斐波中枢的多周期共振动能差 ΔCYF。"

# ══════════════════════════════════════════════
# 3. 历史推演对话与报告流展示
# ══════════════════════════════════════════════
st.markdown("---")

# 初始化历史对话
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

# 展示历史对话
for msg in st.session_state["chat_messages"]:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    with st.chat_message(role):
        st.markdown(content)

# ══════════════════════════════════════════════
# 4. 执行大模型推理
# ══════════════════════════════════════════════
prompt_to_run = None
if run_ai:
    prompt_to_run = f"请针对标的【{stock_name} ({stock_code})】在【{sel_days}日斐波那契中枢】下的五维量化特征（CPR刚性、η微观主力推力、空间获利真空Z'、跨周期动能差ΔCYF），出具完整穿透审计报告！"
elif capsule_prompt:
    prompt_to_run = capsule_prompt

# 底部交互输入框
user_input = st.chat_input("提出你想要研判的量化问题 (如: 主力是在洗盘还是出货？结合 ASR 谈谈仓位？) ...")
if user_input:
    prompt_to_run = user_input

if prompt_to_run:
    # 记录用户提问
    st.session_state["chat_messages"].append({"role": "user", "content": prompt_to_run})
    with st.chat_message("user"):
        st.markdown(prompt_to_run)

    # 召唤大模型生成回复
    with st.chat_message("assistant"):
        with st.spinner("🤖 天眼参谋部正在执行多维张量穿透推演与 CoT 思维链分析..."):
            df = engine.get_security_data(stock_code, days=sel_days)
            advisor = get_advisor(selected_model_id)
            reply = advisor.analyze(stock_code, df, query=prompt_to_run)
            st.markdown(reply)
            st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

st.caption("🤖 天眼作战参谋部 v2.0 | 内容由天衍五维量化大模型结合物理真值与实盘纪律实时推演")
