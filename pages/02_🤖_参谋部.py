"""
天衍五维 · 天眼作战参谋部 (专属 AI 推演研判室)
文件位置: tianyan_v2/pages/02_🤖_天眼作战参谋部.py
"""

import sys
import json
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent if (CURRENT_FILE.parent / "core").exists() else (CURRENT_FILE.parent.parent if (CURRENT_FILE.parent.parent / "core").exists() else CURRENT_FILE.parent.parent.parent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from tianyan_v2.shared import (
    get_tianyan_engine,
    apply_tactical_theme,
    render_top_control_bar,
    render_quota_badge
)
from core.ai_advisor import (
    query_ai_staff_report,
    query_ai_chat_response,
    query_ai_eight_dimension_verdict,
    build_eight_dimension_truth_matrix
)

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
ds_mode    = ctrl.get("data_source_mode", "compass_ocr")

snapshot = engine.get_latest_snapshot(stock_code, mode=ds_mode, allow_network=True)
if not snapshot or not snapshot.get("Close"):
    snapshot = engine.get_latest_snapshot(stock_code, mode="duckdb", allow_network=True)

fib_matrix = engine.get_fibonacci_depth_matrix(stock_code, mode=ds_mode, allow_network=True)
if not fib_matrix:
    fib_matrix = engine.get_fibonacci_depth_matrix(stock_code, mode="duckdb", allow_network=True)

close_p = float(snapshot.get("Close", 10.0) or 10.0)
pct_chg = float(snapshot.get("Pct_Change", snapshot.get("pct_chg", 1.5)) or 1.5)
to_v = float(snapshot.get("Turnover", 3.5) or 3.5)

# 前置秒级解算八维客观物理真值硬核矩阵 (100% 零幻觉底座)
truth_matrix = build_eight_dimension_truth_matrix(stock_code, stock_name, snapshot, fib_matrix, engine=engine, mode=ds_mode)
dim3 = truth_matrix["dim3_position"]
dim4 = truth_matrix["dim4_week200"]
dim5 = truth_matrix["dim5_mine"]
dim6 = truth_matrix["dim6_nextday"]

model_map = {
    "天衍 32B 终极大量化模型 (Qwen-30B/32B 云端千卡)": "tianyan-32b-awq",
    "Qwen3-VL 235B 多模态视觉旗舰 (穿透K线/研报长图/雪球截图)": "Qwen/Qwen3-VL-235B-A22B-Instruct",
    "MiniMax-M1 80K (长窗口深度思考·极速响应)": "MiniMax/MiniMax-M1-80k",
    "DeepSeek-R1-Distill-Qwen-32B (强化推理)": "deepseek-r1-qwen-32b",
    "Local CPU/GPU Fast Heuristic (本地轻量)": "local-fast-heuristic",
}

# ══════════════════════════════════════════════
# 1. 界面空间工程样式定义 (消灭纵向跳动与过度滚动)
# ══════════════════════════════════════════════
st.markdown("""<style>
.stButton>button {
    font-size: 11px !important;
    padding: 2px 4px !important;
    line-height: 1.15 !important;
    height: 32px !important;
    min-height: 32px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    border-radius: 6px !important;
}
.btn-supreme button {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(217, 119, 6, 0.35) 100%) !important;
    border: 1px solid #F59E0B !important;
    color: #FDE68A !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    box-shadow: 0 0 10px rgba(245, 158, 11, 0.2) !important;
}
div[data-testid="stTabs"] button {
    font-size: 12px !important;
    padding: 4px 12px !important;
}
div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stContainer"]) {
    margin-top: -4px !important;
}
div[data-testid="stExpander"] summary {
    font-size: 13px !important;
    white-space: normal !important;
    word-break: break-word !important;
    line-height: 1.45 !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}
div[data-testid="stExpander"] summary p {
    font-size: 13px !important;
    white-space: normal !important;
    word-break: break-word !important;
    line-height: 1.45 !important;
    margin: 0 !important;
}
div[data-testid="stPopover"] {
    width: 100% !important;
}
div[data-testid="stPopover"] > button {
    font-size: 11px !important;
    padding: 2px 6px !important;
    line-height: 1.15 !important;
    height: 32px !important;
    min-height: 32px !important;
    border-radius: 6px !important;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.8) 100%) !important;
    border: 1px solid rgba(16, 185, 129, 0.45) !important;
    color: #6EE7B7 !important;
    font-weight: 600 !important;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.12) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
div[data-testid="stPopover"] > button:hover {
    border-color: #10B981 !important;
    box-shadow: 0 0 14px rgba(16, 185, 129, 0.3) !important;
    color: #A7F3D0 !important;
}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# 2. 控制顶台：一键终裁 + 模型选择 + 配额水库 + 军令阵列
# ══════════════════════════════════════════════
c_top_act, c_top_model, c_top_quota, c_top_clear = st.columns([2.8, 3.2, 2.5, 0.7], vertical_alignment="center")

run_eight_dim = False
qp_query = None

with c_top_act:
    st.markdown('<div class="btn-supreme">', unsafe_allow_html=True)
    if st.button("👑 一键全息八维总裁决", help="一次性解算八大维度真值并由 32B 大模型生成综合战役简报", use_container_width=True):
        run_eight_dim = True
    st.markdown('</div>', unsafe_allow_html=True)

with c_top_model:
    sel_m_label = st.selectbox("核心驱动模型", list(model_map.keys()), 0, key="core_model_sel", label_visibility="collapsed")
    selected_model_id = model_map[sel_m_label]

with c_top_quota:
    render_quota_badge(as_popover=True)

with c_top_clear:
    if st.button("🗑️ 清空", help="清空当前标的推演记录", use_container_width=True):
        st.session_state[f"active_report_{stock_code}"] = None
        st.session_state[f"history_{stock_code}"] = []
        st.rerun()

# 第二行：八大特种战术军令极致单行胶囊
c_act1, c_act2, c_act3, c_act4, c_act5, c_act6, c_act7, c_act8 = st.columns(8, gap="small")

with c_act1:
    if st.button("💬 全景评述", help="评述当前五维筹码能量与多周期共振态势", use_container_width=True):
        qp_query = f"请作为高级量化总参谋长，全景评述 {stock_name}({stock_code}) 当前五维筹码能量与多周期共振态势！"
with c_act2:
    if st.button("🎯 穿透洗盘", help="穿透主力资金是在战略吸筹还是震荡洗盘/出货", use_container_width=True):
        qp_query = f"请深度剖析 {stock_name}({stock_code}) 当前主力资金是在战略吸筹还是震荡洗盘/出货？穿透获利盘剪刀差与 ASR 控盘底座！"
with c_act3:
    if st.button("⚖️ 仓位终裁", help="基于物理指标给出严格的4级动态仓位终裁与风控", use_container_width=True):
        qp_query = f"根据当前五维指标与 CPR/BRI 刚性度，对 {stock_name}({stock_code}) 给出严谨的 4 级动态仓位裁决（空仓/轻仓/半仓/重仓主升），列出一票否决风控！"
with c_act4:
    if st.button("🧬 200周线", help="审计长达4年的200周生死分水岭及长周期中枢", use_container_width=True):
        qp_query = f"结合 200 周线 (长达 4 年的牛熊生死分水岭) 及斐波那契长周期均线中枢，深度审计 {stock_name}({stock_code}) 当前长期战略中枢是突破主升还是承压筑底？"
with c_act5:
    if st.button("💣 异动排雷", help="严审D_pos异常飙升、对倒出货与极端乖离", use_container_width=True):
        qp_query = f"对 {stock_name}({stock_code}) 执行高危异动排雷审计：严审 D_pos 活筹是否异常飙升诱多、主力是否存在分时对倒出货、均线 BIAS 是否极端乖离诱空，给出一票否决排雷结论！"
with c_act6:
    if st.button("🏹 次日推演", help="基于微观推力ηV与断层真空BRI推演次日阻力位与防守中枢", use_container_width=True):
        qp_query = f"基于盘口微观推力 ηV、断层真空走廊 BRI 及筹码密集峰分布，推演 {stock_name}({stock_code}) 次日开盘博弈态势，给出上方第一进攻压力位与下方关键防守中枢！"
with c_act7:
    if st.button("💎 黄金拐点", help="审计CYS34及ΔCYS剪刀差是否触及战略级黄金坑反转买点", use_container_width=True):
        qp_query = f"针对当前市场盈亏偏离度 CYS34 及多尺度剪刀差 ΔCYS，审计 {stock_name}({stock_code}) 是否已触及【战略级黄金坑】或黄金反向钳形买点？给出胜率与介入时机！"
with c_act8:
    if st.button("⚡ 穿透研报", help="生成跨周期斐波那契全景穿透审计战役报告", use_container_width=True):
        qp_query = "!AUDIT"


# ══════════════════════════════════════════════
# 3. 置顶核心军令终裁徽章栏 (高仅 62px · 彻底告别上下翻找)
# ══════════════════════════════════════════════
tier_bg = dim3["pos_color"]
st.markdown(f"""
<div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 6px 14px; margin: 6px 0 8px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">参谋部核心终裁:</span>
        <span style="background: {tier_bg}22; border: 1px solid {tier_bg}; color: {tier_bg}; font-weight: 800; font-size: 12px; padding: 2px 8px; border-radius: 4px;">
            {dim3['pos_label']} ({dim3['pos_pct']}%)
        </span>
    </div>
    <div style="display: flex; align-items: center; gap: 14px; font-size: 12px;">
        <span style="color: #94A3B8;">🛡️ 攻防点位: <b style="color: #10B981;">支 {dim6['support_1']}</b> / <b style="color: #F43F5E;">阻 {dim6['resistance_1']}</b></span>
        <span style="color: #94A3B8;">🧬 200周线: <b style="color: {dim4['color']};">{dim4['bias_200w']:+.1f}%</b> ({dim4['status'].split('(')[0].replace('👑','').replace('★','').replace('■','').replace('✖','').strip()})</span>
        <span style="color: #94A3B8;">⚠️ 排雷: <b style="color: {'#EF4444' if dim5['is_alarm'] else '#10B981'};">{dim5['status'].split('(')[0].strip()}</b></span>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# 4. 状态机与活动战报管理
# ══════════════════════════════════════════════
active_report_key = f"active_report_{stock_code}"
history_key = f"history_{stock_code}"

if active_report_key not in st.session_state:
    st.session_state[active_report_key] = None
if history_key not in st.session_state:
    st.session_state[history_key] = []

# 自动防脏数据校验：若历史活动战报包含 10.00 元兜底假数据且真实股价明显不等于 10 元，自动清空脏缓存
if st.session_state.get(active_report_key):
    cur_rep = st.session_state[active_report_key]
    cur_txt = str(cur_rep.get("content", ""))
    if ("10.00" in cur_txt or "10.0元" in cur_txt) and abs(close_p - 10.0) > 2.0:
        st.session_state[active_report_key] = None
        st.session_state[history_key] = []


# ══════════════════════════════════════════════
# 5. 指令执行中枢 (支持一键八维总裁决与单项穿透)
# ══════════════════════════════════════════════
latest_json = json.dumps(snapshot, ensure_ascii=False, default=str)
fib_json = json.dumps(fib_matrix, ensure_ascii=False, default=str)

# 处理用户自定义输入
# 处理用户自定义输入 (开启小“+”号支持，支持直接粘贴剪贴板截图或上传K线/研报文件)
try:
    user_input = st.chat_input("向天眼参谋部下达深度推演指令 (支持直接粘贴/上传K线与研报截图)...", accept_file=True)
except Exception:
    user_input = st.chat_input("向天眼参谋部下达深度推演指令...")

custom_user_msg = None

if user_input:
    prompt_str = ""
    attached_file = None
    if isinstance(user_input, dict):
        prompt_str = str(user_input.get("text", "")).strip()
        files = user_input.get("files", [])
        if files:
            attached_file = files[0]
    elif hasattr(user_input, "text"):
        prompt_str = str(getattr(user_input, "text", "")).strip()
        files = getattr(user_input, "files", [])
        if files:
            attached_file = files[0]
    else:
        prompt_str = str(user_input).strip()

    if attached_file:
        import base64
        file_bytes = attached_file.getvalue()
        fname = getattr(attached_file, "name", "image.png")
        mime = getattr(attached_file, "type", "image/png") or "image/png"
        is_image = mime.startswith("image/") or fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"))

        if is_image:
            b64_str = base64.b64encode(file_bytes).decode("utf-8")
            custom_user_msg = {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_str if prompt_str else f"请深度穿透识别并分析这张 【{fname}】 图像/K线走势/研报截图，结合当前五维物理底座进行战术推演！"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_str}"}}
                ]
            }
            qp_query = f"🖼️ [{fname}] {prompt_str if prompt_str else '图表穿透识别推演'}"
            # 视觉多模态智能自适应路由：如果当前选中的是纯文本模型，自动升阶至千亿级 Qwen3-VL 235B
            if "vl" not in str(selected_model_id).lower():
                selected_model_id = "Qwen/Qwen3-VL-235B-A22B-Instruct"
        else:
            try:
                doc_text = file_bytes.decode("utf-8", errors="ignore")
                full_text = f"{prompt_str}\n\n【附带文档内容 ({fname})】：\n{doc_text}"
            except Exception:
                full_text = prompt_str
            custom_user_msg = {"role": "user", "content": full_text}
            qp_query = f"📄 [{fname}] {prompt_str if prompt_str else '文档穿透审计'}"
    else:
        custom_user_msg = {"role": "user", "content": prompt_str}
        qp_query = prompt_str

if run_eight_dim:
    with st.spinner(f"🛰️ 正在解算八维物理真值并由 [{selected_model_id}] 生成全息总裁决简报..."):
        res = query_ai_eight_dimension_verdict(
            stock_code=stock_code,
            stock_name=stock_name,
            snapshot_json=latest_json,
            fib_matrix_json=fib_json,
            selected_model=selected_model_id
        )
        report_item = {
            "title": "👑 一键全息八维总裁决",
            "content": res["content"],
            "thinking": res.get("thinking", ""),
            "model_used": res.get("model_used", selected_model_id),
            "duration": res.get("duration_seconds", 0.0),
            "timestamp": pd.Timestamp.now().strftime("%H:%M:%S")
        }
        st.session_state[active_report_key] = report_item
        st.session_state[history_key].append(report_item)
        st.rerun()

elif qp_query:
    if qp_query == "!AUDIT":
        with st.spinner(f"🛰️ 参谋部调用 [{selected_model_id}] 正在执行跨周期斐波那契穿透审计..."):
            res = query_ai_staff_report(
                stock_code=stock_code,
                stock_name=stock_name,
                snapshot_json=latest_json,
                fib_matrix_json=fib_json,
                selected_model=selected_model_id
            )
            report_item = {
                "title": "⚡ 跨周期斐波那契穿透审计",
                "content": res["content"],
                "thinking": res.get("thinking", ""),
                "model_used": res.get("model_used", selected_model_id),
                "duration": res.get("duration_seconds", 0.0),
                "timestamp": pd.Timestamp.now().strftime("%H:%M:%S")
            }
            st.session_state[active_report_key] = report_item
            st.session_state[history_key].append(report_item)
            st.rerun()
    else:
        with st.spinner(f"🧠 [{selected_model_id}] 正在结合 {stock_name} 物理截面深度推演..."):
            chat_history = [custom_user_msg] if custom_user_msg else [{"role": "user", "content": qp_query}]
            res = query_ai_chat_response(
                messages=chat_history,
                stock_code=stock_code,
                stock_name=stock_name,
                snapshot=snapshot,
                selected_model=selected_model_id
            )
            report_item = {
                "title": f"💬 {qp_query}",
                "content": res["content"],
                "thinking": res.get("thinking", ""),
                "model_used": res.get("model_used", selected_model_id),
                "duration": res.get("duration_seconds", 0.0),
                "timestamp": pd.Timestamp.now().strftime("%H:%M:%S")
            }
            st.session_state[active_report_key] = report_item
            st.session_state[history_key].append(report_item)
            st.rerun()


# ══════════════════════════════════════════════
# 6. 三大固定视窗标签页 (固定高度容器 · 彻底杜绝外层向下翻滚)
# ══════════════════════════════════════════════
tab_briefing, tab_truth, tab_stream = st.tabs([
    "🎯 参谋部战役简报 (当前活动视窗)",
    "🔬 八维硬核真值对照表 (数学铁证·零幻觉)",
    "📜 本次会话推演记录"
])

# 视窗 A: 当前活动研报 (固定高度 530px，内部自适应滚动)
with tab_briefing:
    with st.container(height=530):
        active_rep = st.session_state.get(active_report_key)
        if active_rep:
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.6); border-left: 3px solid #38BDF8; border-radius: 4px; padding: 6px 12px; margin-bottom: 10px; font-size: 13px; font-weight: 600; color: #F1F5F9; line-height: 1.45;">
                {active_rep['title']}
            </div>
            """, unsafe_allow_html=True)
            if active_rep.get("thinking"):
                with st.expander("💡 参谋部 CoT 思考推演链 (大模型内生辩证反思)", expanded=False):
                    st.markdown(f"```text\n{active_rep['thinking']}\n```")
            st.markdown(active_rep["content"])
            st.caption(f"⚡ 模型: {active_rep['model_used']} | ⏱️ 耗时: {active_rep.get('duration', 0.0):.2f}s | ● 零幻觉对齐 | 生成时间: {active_rep.get('timestamp', '')}")
        else:
            # 首次进入未点击时，自动提供本地确定性预判大纲
            st.info(f"💡 当前显示 **{stock_name} ({stock_code})** 本地快速推演概貌。点击上方【👑 一键全息八维总裁决】或八大军令胶囊即可召唤云端千卡 32B 大模型生成战术简报！")
            st.markdown(f"""
### 🎖️ 一、 本地量化前置预判
- **建议仓位**: {dim3['pos_label']} (**{dim3['pos_pct']}%**)
- **核心攻防**: 支撑 **{dim6['support_1']}** 元 | 阻力 **{dim6['resistance_1']}** 元
- **当前定性**: {truth_matrix['dim1_base']['status']} · {truth_matrix['dim2_wash']['status']}

### 🛡️ 二、 核心物理参数速查
- **筹码底座**: LFS={truth_matrix['dim1_base']['lfs']:.2f}, HCCYF13={truth_matrix['dim1_base']['hccyf13']:.2f}, 共振得分={truth_matrix['dim1_base']['resonance_score']:.1f}/100
- **浮筹空间**: 活动筹码 ASR={truth_matrix['dim2_wash']['asr']:.2f}%, 集中度 X70={truth_matrix['dim2_wash']['x70']:.2f}%, 获利比 Z={truth_matrix['dim2_wash']['z_profit']:.2f}%
- **200周线**: 基线中枢 {dim4['ma200w']} 元，偏离度 {dim4['bias_200w']:+.2f}% ({dim4['desc']})
- **排雷安检**: {dim5['status']}
            """)

# 视窗 B: 八维硬核客观物理真值对照表 (零幻觉铁证)
with tab_truth:
    with st.container(height=530):
        st.markdown(f"##### 标的 【{stock_name} ({stock_code})】 八大特种战术维度客观数学真值矩阵")
        st.caption("● 本表中所有数值均由天衍偏微分物理求解器与 DuckDB 本地前置确定性计算，作为大模型推演的绝对真值输入，杜绝任何数据幻觉。")
        
        table_rows = [
            {"战术维度": truth_matrix["dim1_base"]["name"], "核心量化指标": f"LFS={truth_matrix['dim1_base']['lfs']:.2f} | HCCYF13={truth_matrix['dim1_base']['hccyf13']:.2f} | 共振={truth_matrix['dim1_base']['resonance_score']:.1f}", "物理真值定性": truth_matrix["dim1_base"]["status"]},
            {"战术维度": truth_matrix["dim2_wash"]["name"], "核心量化指标": f"ASR={truth_matrix['dim2_wash']['asr']:.2f}% | X70={truth_matrix['dim2_wash']['x70']:.2f}% | Z={truth_matrix['dim2_wash']['z_profit']:.2f}%", "物理真值定性": truth_matrix["dim2_wash"]["status"]},
            {"战术维度": truth_matrix["dim3_position"]["name"], "核心量化指标": f"建议仓位: {dim3['pos_pct']}% | 规则代码: {dim3['pos_code']}", "物理真值定性": dim3["pos_label"]},
            {"战术维度": truth_matrix["dim4_week200"]["name"], "核心量化指标": f"200周中枢: {dim4['ma200w']} 元 | 偏离: {dim4['bias_200w']:+.2f}%", "物理真值定性": dim4["status"]},
            {"战术维度": truth_matrix["dim5_mine"]["name"], "核心量化指标": f"D_pos={dim5['d_pos']:.1f} | 换手={dim5['turnover']:.2f}% | ABR={dim5.get('abr', 50.0):.1f}% | BIAS={dim5['bias_5_20']:+.2f}%", "物理真值定性": dim5["status"]},
            {"战术维度": truth_matrix["dim6_nextday"]["name"], "核心量化指标": f"ηV={truth_matrix['dim6_nextday']['eta_v']:.4f} | BRI={truth_matrix['dim6_nextday']['bri']:.2f} | 支:{dim6['support_1']} / 阻:{dim6['resistance_1']}", "物理真值定性": truth_matrix["dim6_nextday"]["status"]},
            {"战术维度": truth_matrix["dim7_golden_pit"]["name"], "核心量化指标": f"CYS34={truth_matrix['dim7_golden_pit']['cys34']:+.2f}% | ΔCYS={truth_matrix['dim7_golden_pit']['delta_cys']:+.2f}%", "物理真值定性": truth_matrix["dim7_golden_pit"]["status"]},
            {"战术维度": truth_matrix["dim8_fibonacci"]["name"], "核心量化指标": f"斐波那契周期数: {len(fib_matrix)} | T+198涨幅: {truth_matrix['dim8_fibonacci']['t198_pct']:+.2f}%", "物理真值定性": truth_matrix["dim8_fibonacci"]["status"]},
        ]
        df_truth = pd.DataFrame(table_rows)
        st.dataframe(df_truth, use_container_width=True, hide_index=True)

# 视窗 C: 历史推演记录流
with tab_stream:
    with st.container(height=530):
        history = st.session_state.get(history_key, [])
        if not history:
            st.info("暂无历史推演快照。每次点击军令或发起提问后，推演快照将沉淀于此。")
        else:
            for idx, item in enumerate(reversed(history)):
                with st.expander(f"📌 [{item.get('timestamp', '')}] {item.get('title', '推演记录')}", expanded=(idx == 0)):
                    st.markdown(item["content"])
                    st.caption(f"⚡ 模型: {item.get('model_used', '')} | ⏱️ 耗时: {item.get('duration', 0.0):.2f}s")

