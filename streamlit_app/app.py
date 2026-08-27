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
from core.signals import SignalJudge
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

/* 指标卡片网格与 Hover 动效 */
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
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: help;
}
.metric-card:hover {
    border-color: #3B82F6 !important;
    background: linear-gradient(135deg, #1E293B, #0F172A) !important;
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.35) !important;
    transform: translateY(-1px);
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

/* 参谋部 AI 审计报告紧凑排版 */
.ai-report-box {
    background: linear-gradient(135deg, #090E1A 0%, #0F172A 100%);
    border: 1px solid #1E293B;
    border-left: 4px solid #3B82F6;
    border-radius: 6px;
    padding: 12px 16px;
    margin-top: 6px;
    color: #E2E8F0;
    font-size: 12px;
    line-height: 1.45;
}
.ai-report-box h1, .ai-report-box h2, .ai-report-box h3, .ai-report-box h4 {
    color: #F8FAFC !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    margin: 8px 0 3px 0 !important;
    padding-bottom: 2px !important;
    border-bottom: 1px dashed rgba(255,255,255,0.12) !important;
}
.ai-report-box ul {
    margin: 2px 0 4px 0 !important;
    padding-left: 16px !important;
}
.ai-report-box li {
    margin-bottom: 2px !important;
    line-height: 1.4 !important;
}
.ai-report-box p {
    margin: 2px 0 !important;
    line-height: 1.4 !important;
}
.ai-report-box strong {
    color: #FCD34D !important;
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

sel_group = st.session_state["selected_group"]
sel_code = st.session_state["selected_code"]
sel_days = st.session_state["selected_days"]
sel_dim5 = st.session_state["selected_dim5"]

quota = modelscope_client.get_quota_status()
ratio_pct = round(quota["remaining_ratio"] * 100, 1)

# ==========================================
# 1. 自选股票池与多分组管理紧凑抽屉
# ==========================================
with st.expander("⚙️ 自选股票池与多分组管理 (自主新建分组 / 全市场标的动态入池)", expanded=False):
    tab_m1, tab_m2 = st.tabs(["➕ 添加标的到分组", "📁 新建/管理自选分组"])
    
    with tab_m1:
        c_in1, c_in2, c_in3, c_in4 = st.columns([2.0, 2.2, 2.2, 1.2], gap="small")
        with c_in1:
            target_group = st.selectbox("归属分组", [g for g in group_names if g != "⭐ 全部标的池"], 0, label_visibility="collapsed")
        with c_in2:
            new_code = st.text_input("股票代码", key="add_stock_code", placeholder="股票代码 (如 600519)", label_visibility="collapsed")
        with c_in3:
            new_name = st.text_input("股票名称 (可选)", key="add_stock_name", placeholder="股票名称 (如 贵州茅台)", label_visibility="collapsed")
        with c_in4:
            add_btn = st.button("➕ 加入分组", use_container_width=True)
            if add_btn and new_code:
                code_c = new_code.strip()
                name_c = new_name.strip()
                engine.add_custom_target(code_c, name_c, group_name=target_group)
                st.success(f"标的 {name_c or code_c} ({code_c}) 已成功归入【{target_group}】！")
                st.rerun()

    with tab_m2:
        c_g1, c_g2 = st.columns([6.4, 1.4], gap="small")
        with c_g1:
            new_group_name = st.text_input("新建分组名称", placeholder="新建分组名称 (例如：度小满观察池、战略核心持仓组)", label_visibility="collapsed")
        with c_g2:
            create_g_btn = st.button("📁 立即创建分组", use_container_width=True)
            if create_g_btn and new_group_name:
                engine.create_custom_group(new_group_name.strip())
                st.success(f"分组【{new_group_name.strip()}】已成功创建！")
                st.rerun()

# ==========================================
# 3. DuckDB 全市场五维筹码毫秒级战术初筛雷达榜 (移至上部，方便全市场选股)
# ==========================================
with st.expander("🔍 DuckDB 全市场五维筹码毫秒级初筛雷达榜 (超导死锁 / 真空走廊 / 黄金坑 / 主升浪 · 一键建池)", expanded=False):
    tab0, tab1, tab2, tab3 = st.tabs(["⚡ 超导死锁与真空跃迁 (CPR/BRI)", "🌟 物理真空走廊 + 极度单峰", "💎 战略黄金坑逆向超卖", "👑 超级主升浪筹码多头金叉"])
    
    with tab0:
        try:
            cpr_df = screener.scan_cpr_superconductor()
            st.dataframe(cpr_df.to_pandas(), use_container_width=True, hide_index=True)
            if st.button("📥 一键将【超导真龙 Top 15】加入「⚡ 超导死锁真空跃迁池」", key="import_cpr"):
                records = cpr_df.select(["code", "name"]).to_dicts()
                engine.create_custom_group("⚡ 超导死锁真空跃迁池")
                engine.add_stocks_to_group("⚡ 超导死锁真空跃迁池", records)
                st.success("✅ 超导真龙标的已全部自动同步至「⚡ 超导死锁真空跃迁池」！")
                st.rerun()
        except Exception as e:
            st.info(f"全市场初筛载入中: {e}")

    with tab1:
        try:
            vac_df = screener.scan_vacuum_corridor()
            st.dataframe(vac_df.to_pandas(), use_container_width=True, hide_index=True)
            if st.button("📥 一键将【真空走廊 Top 15】加入「🚀 物理真空走廊突击组」", key="import_vac"):
                records = vac_df.select(["code", "name"]).to_dicts()
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
                records = pit_df.select(["code", "name"]).to_dicts()
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
                records = res_df.select(["code", "name"]).to_dicts()
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

# 核心六大高阶衍生量化张量计算 (CPR / ηV / BRI / κCYC / ΔCYS / SMPI)
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
    d_pos=float(snapshot.get("D_Pos", 35.0))
)

# ==========================================
# 4. 指标分析类核心内容 (战术军令条 + 六大高阶指标 + 五维指标穿透卡片 + 斐波那契矩阵 + AI参谋部)
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
        <span>Norm_BIAS: <b style="color:#E5E7EB;">{snapshot.get('Norm_BIAS_5_20', 0):.2f}</b></span>
        <span>微观推升: <b style="color:#10B981;">{micro_order.get('eta_micro_thrust', 0):+.2f}</b></span>
    </div>
</div>
""", unsafe_allow_html=True)

# 渲染六大高阶衍生量化指标 (CPR / ηV / BRI / κCYC / ΔCYS / SMPI)
st.markdown(f"""
<div class="high-order-grid" style="display:grid; grid-template-columns:repeat(6, 1fr); gap:6px; margin:2px 0 5px 0;">
    <div class="metric-card" style="padding:4px 6px;" title="【① 筹码刚性度 (CPR)】&#10;📐 微积分物理公式: CPR = (LFS × HCCYF13) / [ASR × (1 + Turnover/100)]&#10;🔬 物理场含义: 底座战略势能与动态摩擦耗散之比。衡量主力死锁筹码对盘口的引力束缚强度。&#10;⚡ 多维共振判定:&#10;• CPR ≥ 20.0 且 BRI ≥ 30.0 ➔ 【超导死锁态】主力绝对控盘，零换手跃迁！&#10;• CPR < 5.0 ➔ 【筹码溃散态】底座松动，谨防对倒出货！">
        <div class="metric-card-title">① 筹码刚性度 (CPR)</div>
        <div class="metric-card-value" style="color:{high_order.cpr_color}; font-size:12.5px;">{high_order.cpr:.2f}</div>
        <div class="metric-card-sub" style="color:{high_order.cpr_color}; font-size:9.5px;">{high_order.cpr_status}</div>
    </div>
    <div class="metric-card" style="padding:4px 6px;" title="【② 真空推升能效比 (ηV)】&#10;📐 微积分物理公式: ηV = (ΔP% × 100) / (Turnover × ASR) = (dP/dt) / (dVol/dt ⊗ ASR)&#10;🔬 物理场含义: 价格一阶跃升梯度与动能损耗之比。代表克服上方筹码阻力所需的能效转化率。&#10;⚡ 多维共振判定:&#10;• ηV ≥ 0.02 ➔ 【高能真空跃迁】上方无套牢阻力，光速主升浪！&#10;• ηV < 0.005 且 换手 > 10% ➔ 【天量磨损滞涨】假突破真出货，警惕诱多！">
        <div class="metric-card-title">② 真空推升能效比 (ηV)</div>
        <div class="metric-card-value" style="color:{high_order.eta_v_color}; font-size:12.5px;">{high_order.eta_v:.4f}</div>
        <div class="metric-card-sub" style="color:{high_order.eta_v_color}; font-size:9.5px;">{high_order.eta_v_status}</div>
    </div>
    <div class="metric-card" style="padding:4px 6px;" title="【③ 断层真空指数 (BRI)】&#10;📐 微积分物理公式: BRI = [(100 - Y_Overlap) × Z_Profit] / (X70 × ASR)&#10;🔬 物理场含义: 哑铃双峰撕裂度与断层真空通道宽度。∫ (1 - P(x)) dx 阻力为零。&#10;⚡ 多维共振判定:&#10;• BRI ≥ 30.0 且 X70 ≤ 10% ➔ 【绝对哑铃真空走廊】上无套牢盘阻击，磁吸暴拉！&#10;• BRI < 10.0 ➔ 【筹码散乱崩塌】多峰堆叠，向上摩擦阻力极大！">
        <div class="metric-card-title">③ 断层真空指数 (BRI)</div>
        <div class="metric-card-value" style="color:{high_order.bri_color}; font-size:12.5px;">{high_order.bri:.2f}</div>
        <div class="metric-card-sub" style="color:{high_order.bri_color}; font-size:9.5px;">{high_order.bri_status}</div>
    </div>
    <div class="metric-card" style="padding:4px 6px;" title="【④ 斐波那契均线张力收敛度 (κCYC)】&#10;📐 微积分物理公式: κCYC = [max(CYC5, CYC13, CYC34) - min(CYC5, CYC13, CYC34)] / CYC_inf × 100%&#10;🔬 物理场含义: 斐波那契多尺度引力中枢坍缩率。均线曲率张量收敛至奇点。&#10;⚡ 多维共振判定:&#10;• κCYC ≤ 3.0% 且 LFS ≥ HCCYF13 ➔ 【奇点爆发区 (Big Bang)】多周期共振点火，暴风雨前夜！&#10;• κCYC > 15.0% ➔ 【均线过度发散】短线乖离过大，谨防反向对冲回调！">
        <div class="metric-card-title">④ 均线张力收敛 (κCYC)</div>
        <div class="metric-card-value" style="color:{high_order.kappa_cyc_color}; font-size:12.5px;">{high_order.kappa_cyc:.2f}%</div>
        <div class="metric-card-sub" style="color:{high_order.kappa_cyc_color}; font-size:9.5px;">{high_order.kappa_cyc_status}</div>
    </div>
    <div class="metric-card" style="padding:4px 6px;" title="【⑤ 盈亏剪刀差 (ΔCYS)】&#10;📐 微积分物理公式: ΔCYS = CYS13 - CYS34 = d(CYS)/d(Fib_scale)&#10;🔬 物理场含义: 短周期 vs 中周期浮盈梯度差分。反映多头攻击动能的二阶加速度。&#10;⚡ 多维共振判定:&#10;• ΔCYS > +5.0% 且 CYS34 > 0 ➔ 【多头攻击加速】短线动能超越中线，主升浪主攻态！&#10;• CYS34 < -8.0% 且 ΔCYS 向上金叉 ➔ 【战略黄金坑点火】逆向超卖反转第一买点！">
        <div class="metric-card-title">⑤ 盈亏剪刀差 (ΔCYS)</div>
        <div class="metric-card-value" style="color:{high_order.delta_cys_color}; font-size:12.5px;">{high_order.delta_cys:+.2f}%</div>
        <div class="metric-card-sub" style="color:{high_order.delta_cys_color}; font-size:9.5px;">{high_order.delta_cys_status}</div>
    </div>
    <div class="metric-card" style="padding:4px 6px;" title="【⑥ 主力筹码纯度 (SMPI)】&#10;📐 微积分物理公式: SMPI = (Main% - Dare%) / Turnover × (1 - D_Pos/100)&#10;🔬 物理场含义: 剥离游资对倒虚假换手，提取机构真实净吸筹内驱力。&#10;⚡ 多维共振判定:&#10;• SMPI ≥ +0.3 ➔ 【机构高纯度扫盘】主力真实进场，锁仓吸筹！&#10;• SMPI ≤ -0.2 且 换手 > 15% ➔ 【游资倒沫子预警】对倒出货诱多，坚决清仓！">
        <div class="metric-card-title">⑥ 主力筹码纯度 (SMPI)</div>
        <div class="metric-card-value" style="color:{high_order.smpi_color}; font-size:12.5px;">{high_order.smpi:+.2f}</div>
        <div class="metric-card-sub" style="color:{high_order.smpi_color}; font-size:9.5px;">{high_order.smpi_status}</div>
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
    <div class="metric-card" title="【① 筹码底座锁定度 (LFS)】&#10;📐 数学微积分公式: LFS = ∫_{{底座价格区间}} P(x, t) dx&#10;🔬 物理时空场含义: 绝对底座战略锁仓能量。LFS ≥ HCCYF13 代表长线多头底座未破，持股装死不败基石！">
        <div class="metric-card-title">① 筹码底座锁定 (LFS)</div>
        <div class="metric-card-value" style="color:{'#10B981' if lfs_val >= 55 else '#94A3B8'};">{lfs_val:.1f}</div>
        <div class="metric-card-sub">{'主力高锁仓防线' if lfs_val >= 55 else '常规筹码离散'}</div>
    </div>
    <div class="metric-card" title="【② 空间获利真空一阶导 (Z\')】&#10;📐 数学微积分公式: Z\' = lim_{{Δt→0}} ΔZ / Δt&#10;🔬 物理时空场含义: 获利盘突变速度梯度。Z\' > 3.0 代表突破历史密集峰，进入物理抛压真空主升区！">
        <div class="metric-card-title">② 空间获利真空 (Z')</div>
        <div class="metric-card-value" style="color:{'#F59E0B' if z_val >= 10 else '#3B82F6'};">{z_val:+.1f}%</div>
        <div class="metric-card-sub">{'触发物理真空主升' if z_val >= 10 else '中枢箱体蓄势'}</div>
    </div>
    <div class="metric-card" title="【③ 筹码聚集度 (X70/ASR)】&#10;📐 数学微积分公式: X70 = 70% 筹码集中带宽 / ASR = 活跃筹码跨度&#10;🔬 物理时空场含义: 筹码单峰密集度。X70 ≤ 10% 代表主力绝对高度控盘，洗盘彻底无杂质！">
        <div class="metric-card-title">③ 筹码聚集度 (X70/ASR)</div>
        <div class="metric-card-value" style="color:#8B5CF6;">{x70_val:.1f}% <span style="font-size:9.5px; color:#94A3B8;">/ {asr_val:.1f}</span></div>
        <div class="metric-card-sub">{'超级单峰聚集' if x70_val <= 10 else '常规分布'}</div>
    </div>
    <div class="metric-card" title="【④ 微观主力推力 (η/ABR)】&#10;📐 数学微积分公式: η = (主动买单量 - 主动卖单量) / 总成交量&#10;🔬 物理时空场含义: Level-2 逐笔 Tick 订单流内驱力。主动买盘占比 > 60% 代表盘口真实扫单吸筹！">
        <div class="metric-card-title">④ 微观主力推力 (η/ABR)</div>
        <div class="metric-card-value" style="color:#10B981;">{micro_order.get('eta_micro_thrust', 0):+.2f} <span style="font-size:9.5px; color:#94A3B8;">({micro_order.get('active_buy_ratio_%', 50):.0f}%)</span></div>
        <div class="metric-card-sub">订单流主动买盘主导</div>
    </div>
    <div class="metric-card" title="【⑤ 券商研报目标溢价】&#10;📐 计算公式: 目标溢价% = (券商一致目标价 - 当前现价) / 当前现价 × 100%&#10;🔬 基本面价值中枢: 顶级券商金工与行业分析师公允估值锚，提供基本面重估上涨空间天花板！">
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

# 连续微积分数学物理底座教义 (Mathematical Physics Engine)
with st.expander("🔬 天衍数理底座 · 连续微积分时空场与筹码守恒反解方程", expanded=False):
    st.markdown("""
    <div style="font-size:11.5px; color:#94A3B8; margin-bottom:8px; line-height:1.5;">
        本系统彻底摒弃传统商业软件的离散切片与简陋等腰三角假设，采用<b>连续时空偏微分方程</b>与<b>筹码质心质量守恒律</b>，实现全天候无噪反解与机构拆单穿透。
    </div>
    """, unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns(2, gap="medium")
    with col_p1:
        st.markdown("**① 主力增仓与拆单穿透反解方程 (Main% Inversion)**")
        st.latex(r"Main\%_{\text{物理反解}} = \alpha \cdot \frac{\partial LFS}{\partial t} + \beta \cdot \text{Turnover} \cdot \left( \frac{\text{Close} - \text{VWAP}}{\text{High} - \text{Low}} \right) \cdot (1 - \text{ASR}_{\text{散度}})")
        st.markdown(r"<span style='font-size:10.5px; color:#64748B;'>💡 <b>穿透机构算法拆单</b>：无论主力如何使用 TWAP/VWAP 碎单拆分，底层锁仓能量 $\partial LFS/\partial t$ 与散度收敛必将真实暴露其净买入内驱力。</span>", unsafe_allow_html=True)
        
        st.markdown("**② 连续高斯卷积微积分场 (Continuous Density Field)**")
        st.latex(r"\frac{\partial P(x,t)}{\partial t} = -\alpha \cdot \text{Turnover}(t) \cdot P(x,t) + V(t) \cdot \frac{1}{\sigma \sqrt{2\pi}} e^{-\frac{(x - \text{VWAP})^2}{2\sigma^2}}")
        st.markdown(r"<span style='font-size:10.5px; color:#64748B;'>💡 <b>平滑连续质量守恒</b>：$\int_{-\infty}^{+\infty} P(x,t) dx = 100\%$，彻底消除传统软件 1 分钱离散阶梯伪影。</span>", unsafe_allow_html=True)

    with col_p2:
        st.markdown("**③ 真空推升能效比张量 (Vacuum Thrust Efficiency)**")
        st.latex(r"\eta_V = \frac{\partial P / \partial t}{\partial \text{Vol} / \partial t \otimes \text{ASR}} = \frac{\Delta P_{\%} \times 100}{\text{Turnover} \times \text{ASR}}")
        st.markdown(r"<span style='font-size:10.5px; color:#64748B;'>💡 <b>超导主升浪判定</b>：价格一阶梯度与动能摩擦之比。$\eta_V \ge 0.02$ 判定为上方零阻力光速真空跃迁。</span>", unsafe_allow_html=True)

        st.markdown("**④ 断层真空走廊积分与筹码刚性度 (BRI & CPR)**")
        st.latex(r"BRI = \frac{(100 - Y) \cdot Z}{X_{70} \cdot \text{ASR}} \propto \int_{P_{\text{当前}}}^{P_{\text{目标}}} [1 - P(x)] \, dx, \quad CPR = \frac{LFS \cdot HCCYF13}{\text{ASR} \cdot (1 + \text{Turnover}/100)}")
        st.markdown(r"<span style='font-size:10.5px; color:#64748B;'>💡 <b>双峰撕裂与超导死锁</b>：哑铃走廊真空磁吸暴拉，底座势能与动态耗散之比 $CPR \ge 20.0$ 触发死锁锁仓。</span>", unsafe_allow_html=True)


# 参谋部全息战术控制台与 AI 深度穿透审计 (图一图表设定与图二大模型审计合并)
with st.expander("🤖 天眼参谋部 · 全息图表战术设定与 AI 深度穿透审计", expanded=True):
    # 第一排：图表控制四大金刚 (分组 / 标的 / 周期 / 维五)
    t0, t1, t2, t3 = st.columns([2.4, 3.2, 2.0, 2.4], gap="small")
    with t0:
        sel_group = st.selectbox("g", group_names, 
                                 index=group_names.index(st.session_state["selected_group"]) if st.session_state["selected_group"] in group_names else 0,
                                 key="group_selector", label_visibility="collapsed")
        if sel_group != st.session_state["selected_group"]:
            st.session_state["selected_group"] = sel_group
            new_targets = engine.get_targets(sel_group)
            st.session_state["selected_code"] = new_targets[0].code if new_targets else ""
            st.rerun()

    targets = engine.get_targets(st.session_state["selected_group"])
    tgt_opts = {f"{t.name} ({t.code})": t.code for t in targets}
    if not tgt_opts:
        tgt_opts = {"暂无标的 (请在下方添加)": ""}
    tgt_codes = list(tgt_opts.values())
    curr_tgt_idx = tgt_codes.index(st.session_state["selected_code"]) if st.session_state["selected_code"] in tgt_codes else 0
    with t1:
        sel_label = st.selectbox("t", list(tgt_opts.keys()), index=curr_tgt_idx, key="target_selector", label_visibility="collapsed")
        sel_code = tgt_opts[sel_label]
        if sel_code != st.session_state["selected_code"]:
            st.session_state["selected_code"] = sel_code
            st.rerun()

    with t2:
        fib_l = [n for n, _ in FIB_PERIODS]
        fib_v = [v for _, v in FIB_PERIODS]
        curr_fib_idx = fib_v.index(st.session_state.get("selected_days", 34)) if st.session_state.get("selected_days", 34) in fib_v else 3
        fi = st.selectbox("f", range(len(fib_l)), index=curr_fib_idx,
                          format_func=lambda i: fib_l[i], key="period_selector", label_visibility="collapsed")
        sel_days = fib_v[fi]
        if sel_days != st.session_state.get("selected_days"):
            st.session_state["selected_days"] = sel_days
            st.rerun()

    with t3:
        d5_opts = {
            "🌊 5+20日多维共振": 0,
            "⚡ 5日短线游资": 5,
            "📊 10日波段中枢": 10,
            "🛡️ 20日标准月线": 20,
        }
        d5_vals = list(d5_opts.values())
        curr_d5_idx = d5_vals.index(st.session_state.get("selected_dim5", 0)) if st.session_state.get("selected_dim5", 0) in d5_vals else 0
        sel_d5_label = st.selectbox("d5", list(d5_opts.keys()), index=curr_d5_idx, key="dim5_selector", label_visibility="collapsed")
        sel_dim5 = d5_opts[sel_d5_label]
        if sel_dim5 != st.session_state.get("selected_dim5"):
            st.session_state["selected_dim5"] = sel_dim5
            st.rerun()

    # 第二排：大模型选择 / 召唤审计按钮 / 免费配额水库
    c_mod, c_btn, c_quota = st.columns([4.2, 3.2, 2.6], gap="small")
    with c_mod:
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
        sel_m_label = st.selectbox("选择金融大模型", list(model_map.keys()), 0, label_visibility="collapsed")
        selected_model_id = model_map[sel_m_label]
    with c_btn:
        run_ai = st.button("⚡ 召唤大模型执行穿透审计", type="primary", use_container_width=True)
    with c_quota:
        st.markdown(f"""
        <div class="quota-badge" style="height:28px; margin:0;" title="ModelScope 官方每日 2,000 次免费配额，安全硬顶 1,800 次，每日 00:00 重置">
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
            
            if res.get("thinking"):
                with st.expander("💡 参谋部 CoT 思考推演链 (大模型内生逻辑)", expanded=False):
                    st.markdown(f"```text\n{res['thinking']}\n```")
            
            st.markdown('<div class="ai-report-box">', unsafe_allow_html=True)
            st.markdown(res["content"])
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption(f"⚡ 审计模型: `{res.get('model_used')}` | 耗时: `{res.get('duration_seconds')}s` | 状态: `{res.get('status')}`")

# ==========================================
# 5. 图形全息展示区 (全息五维雷达图 + HUD 右侧实时战术看板)
# ==========================================
fig = build_radar_figure(df, stock_name, dim5_mode=sel_dim5)
render_radar_with_hud(fig, df, stock_name, dim5_mode=sel_dim5, height=750)
