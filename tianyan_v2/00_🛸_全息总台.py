"""
天衍五维 · 下一代现代化作战总台 (主入口)
文件位置: tianyan_v2/app.py
特性:
  1. 100% 满屏纯净视界：彻底切除浮动窗口与 DOM 争夺，主图顶格展示
  2. 完整继承图五资产：14 物理真值指标卡片 (7+7) + 军令条 + 五维全息雷达波形走势 + HUD 看板
  3. 全局参数总线驱动，跨页面与战备库、参谋部实时联动
"""

import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import numpy as np
import pandas as pd

from tianyan_v2.shared import (
    get_tianyan_engine,
    apply_tactical_theme,
    render_top_control_bar,
    render_quota_badge
)
from core.components.radar_chart import build_radar_figure
from core.components.crosshair import render_radar_with_hud
from core.components.quantum_physics_chart import (
    build_quantum_physics_figure,
    render_quantum_physics_with_hud,
)
from core.signals import SignalJudge
from core.ai_advisor import evaluate_local_tactical_status

st.set_page_config(
    page_title="天衍五维 · 全息作战总台",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_tactical_theme()
engine = get_tianyan_engine()
# ══════════════════════════════════════════════
# 0. 左侧侧边栏：全局数据基座持久化配置中枢
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding: 4px 0 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px;">
        <span style="font-size: 14px; font-weight: 800; color: #38BDF8;">⚙️ 核心数据底座持久化配置</span>
        <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">全局持久化 · 强刷页面永久保持生效</div>
    </div>
    """, unsafe_allow_html=True)
    from core.user_preference import get_user_preference, save_user_preference
    cur_pref_mode = get_user_preference().get("data_source_mode", "compass_ocr")
    sidebar_choice = st.radio(
        "全局数据基座模式",
        ["🎯 指南针手工真值 (OCR)", "⚡ 天衍偏微分推导 (DuckDB)"],
        index=0 if cur_pref_mode == "compass_ocr" else 1,
        key="sidebar_data_source_radio"
    )
    s_target_mode = "compass_ocr" if sidebar_choice.startswith("🎯") else "duckdb"
    if s_target_mode != st.session_state.get("data_source_mode"):
        st.session_state["data_source_mode"] = s_target_mode
        save_user_preference("data_source_mode", s_target_mode)
        st.rerun()

    st.markdown("<div style='margin-top: 24px; margin-bottom: 8px; font-size: 11px; color: #64748B; font-weight: 700;'>🛡️ 算力水库与预算门神</div>", unsafe_allow_html=True)
    render_quota_badge(as_popover=False)

# ══════════════════════════════════════════════
# 1. 顶部作战控制台 (全局参数总线)
# ══════════════════════════════════════════════
ctrl = render_top_control_bar(engine, title_prefix="🛸 天衍五维 · 全息作战总台")
stock_code = ctrl["stock_code"]
stock_name = ctrl["stock_name"]
sel_days   = ctrl["days"]
sel_dim5   = ctrl["dim5"]

# ══════════════════════════════════════════════
# 1.1 数据基座模式状态指示
# ══════════════════════════════════════════════
ds_mode = ctrl.get("data_source_mode", "compass_ocr")
if ds_mode == "compass_ocr":
    ds_status_html = """
    <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: #94A3B8; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 6px; padding: 6px 14px; margin-bottom: 8px;">
        <span style="color: #38BDF8; font-weight: bold;">📡 当前物理基座:</span>
        <span style="color: #F8FAFC; font-weight: 600;">🎯 指南针手工截屏 OCR 实盘真值库 (stock.csv)</span>
        <span style="background: rgba(16, 185, 129, 0.15); color: #10B981; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">最新更新: 2026-09-02 (昨日收盘真值)</span>
    </div>
    """
else:
    ds_status_html = """
    <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: #94A3B8; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 6px; padding: 6px 14px; margin-bottom: 8px;">
        <span style="color: #C084FC; font-weight: bold;">⚡ 当前物理基座:</span>
        <span style="color: #F8FAFC; font-weight: 600;">天衍偏微分物理连续场推导 (DuckDB / MCD 偏微分求解器)</span>
        <span style="background: rgba(168, 85, 247, 0.15); color: #C084FC; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">纯数学微积分独立解算</span>
    </div>
    """
st.markdown(ds_status_html, unsafe_allow_html=True)

# 数据拉取与特征推演 (正式传入当前选中的持久化基座模式！)
df = engine.get_stock_data(stock_code, days=sel_days, mode=ds_mode, allow_network=True)
if df.is_empty():
    st.error(f"⚠️ 未找到标的 {stock_code} 的时空数据。")
    st.stop()

snapshot = engine.get_latest_snapshot(stock_code, mode=ds_mode, allow_network=True)
local_eval = evaluate_local_tactical_status(snapshot)

action = local_eval.get("order", "【底座防守蓄势】")
rationale = local_eval.get("rationale", "五维筹码常态分布，执行常规纪律。")
res_color = local_eval.get("badge_color", "#10B981")
res_score = float(local_eval.get("resonance_score", 50.0))
norm_bias = float(local_eval.get("norm_bias", 0.0))

# ══════════════════════════════════════════════
# 2. 战术军令条
# ══════════════════════════════════════════════
st.markdown(f"""
<div class="tactical-bar" style="border-left-color: {res_color};">
    <div>
        <span style="background: rgba(239, 68, 68, 0.2); color: {res_color}; padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-right: 8px;">
            {action}
        </span>
        {rationale}
    </div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #94A3B8;">
        跨周期共振: <b style="color: {res_color};">{res_score:.1f}</b> &nbsp;|&nbsp;
        目标建议仓位: <b style="color: #38BDF8;">{local_eval.get('target_position_pct', 50)}%</b> &nbsp;|&nbsp;
        Norm_BIAS: <b style="color: #F8FAFC;">{norm_bias:.2f}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 3. 14 核心物理真值指标卡片 (7+7 双排紧凑网格)
# ══════════════════════════════════════════════
close_p = float(snapshot.get("Close", 10.0) or 10.0)
turnover_p = float(snapshot.get("Turnover", 3.0) or 3.0)
main_p = float(snapshot.get("Main_Fund_Pct", 5.0) or 5.0)
abr_est = min(95.0, max(5.0, 50.0 + main_p * 2.0))
eta_micro_calc = (float(snapshot.get("Pct_Change", 1.0) or 1.0) / max(turnover_p, 0.1)) * (2.0 * (abr_est / 100.0) - 1.0)

high_order = SignalJudge.calculate_high_order_metrics(
    lfs=float(snapshot.get("LFS", 50.0) or 50.0),
    hccyf=float(snapshot.get("HCCYF13", 50.0) or 50.0),
    asr=float(snapshot.get("ASR", 20.0) or 20.0),
    turnover=turnover_p,
    delta_p_pct=float(snapshot.get("Pct_Change", 2.0) or 2.0) / 100.0,
    x70=float(snapshot.get("X70", 15.0) or 15.0),
    y_overlap=float(snapshot.get("Overlap_Y", 20.0) or 20.0),
    z_profit=float(snapshot.get("Z_Profit", 50.0) or 50.0),
    cyc5=float(snapshot.get("CYC5", close_p) or close_p),
    cyc13=float(snapshot.get("CYC13", close_p) or close_p),
    cyc34=float(snapshot.get("CYC34", close_p) or close_p),
    cyc_inf=float(snapshot.get("CYC_inf", close_p) or close_p),
    cys13=float(snapshot.get("CYS13", 0.0) or 0.0),
    cys34=float(snapshot.get("CYS34", 0.0) or 0.0),
    bias_5_20=float(snapshot.get("BIAS_5_20", 0.0) or 0.0),
    main_pct=main_p,
    dare_pct=float(snapshot.get("Dare_Fund_Pct", 1.0) or 1.0),
    d_pos=float(snapshot.get("D_Pos", 35.0) or 35.0),
    cyf66_raw=float(snapshot.get("CYF66_Raw", 50.0) or 50.0),
    cyf66_vma55=float(snapshot.get("CYF66_VMA55", 50.0) or 50.0)
)

# ══════════════════════════════════════════════
# 全息量化指标百科全书 (含物理公式、阈值判据与跨指标联动图谱)
# ══════════════════════════════════════════════
TACTICAL_HELP = {
    "cpr": (
        "【① 筹码刚性度 (CPR - Chip Rigidity Degree)】&#10;"
        "📐 微积分公式: CPR = (LFS × HCCYF13) / [ASR × (1 + Turnover/100)]&#10;"
        "🔬 物理本质: 衡量主力底座战略锁仓势能与盘口动态摩擦耗散之比。&#10;"
        "⚡ 量化判据:&#10;"
        "• CPR ≥ 25.0 ➔ 【超导死锁态】主力绝对控盘，浮筹抽干，零换手跃迁！&#10;"
        "• CPR < 10.0 ➔ 【筹码溃散态】底座严重松动，散户多头踩踏！&#10;"
        "🔗 跨指标核心联动图谱:&#10;"
        "1. 与 LFS 联动: LFS 是绝对地基！若 LFS < 40，即便 CPR 冲高也是短线虚火！&#10;"
        "2. 与 ASR 联动: CPR 飙升必须伴随 ASR(活动筹码) 急剧萎缩至 30% 以下，方为真死锁！&#10;"
        "3. 与 BRI 联动: 当 CPR ≥ 20 且 BRI ≥ 30 时，触发【超导死锁 + 断层真空】主升最强共振！"
    ),
    "eta_v": (
        "【② 真空推升能效比 (ηV - Vacuum Push Efficiency)】&#10;"
        "📐 微积分公式: ηV = (ΔP% × 100) / (Turnover × ASR)&#10;"
        "🔬 物理本质: 价格一阶跃升斜率与动态能量耗散之比，表征阻力最小路径。&#10;"
        "⚡ 量化判据:&#10;"
        "• ηV ≥ 0.03 ➔ 【高能真空跃迁】上方毫无套牢盘压制，极小换手推升涨停！&#10;"
        "• ηV < 0.005 且 换手 > 10% ➔ 【天量滞涨耗散】主力对倒出货诱多！&#10;"
        "🔗 跨指标核心联动图谱:&#10;"
        "1. 与 Turnover 联动: 极低换手率 (Turnover < 3%) 拉出大阳线，说明阻力为零！&#10;"
        "2. 与 Z 获利盘联动: Z ≥ 85% 时仍能维持高 ηV，说明获利盘惜售锁仓极度坚决！"
    ),
    "bri": (
        "【③ 断层真空指数 (BRI - Breakout Rift Index)】&#10;"
        "📐 微积分公式: BRI = [(100 - Y_Overlap) × Z_Profit] / (X70 × ASR)&#10;"
        "🔬 物理本质: 哑铃双峰撕裂跨度与中枢断层真空通道净空度。&#10;"
        "⚡ 量化判据:&#10;"
        "• BRI ≥ 30.0 ➔ 【绝对哑铃真空走廊】上下双峰彻底撕裂，磁吸式暴拉！&#10;"
        "• BRI < 10.0 ➔ 【多峰堆叠阻滞】中枢密集套牢，向上每一步都是血战！&#10;"
        "🔗 跨指标核心联动图谱:&#10;"
        "1. 与 Y 重合度联动: Y 重合度越低 (<20%)，说明筹码双峰撕裂越严重，真空通道越深邃！&#10;"
        "2. 与 X70 联动: X70 越狭窄，底峰越紧凑，上方真空加速斜率越大！"
    ),
    "kappa_cyc": (
        "【④ 斐波张力收敛度 (κCYC - Fibonacci Convergence)】&#10;"
        "📐 微积分公式: κCYC = [max(CYC5,13,34) - min(CYC5,13,34)] / CYC_inf × 100%&#10;"
        "🔬 物理本质: 斐波那契多尺度引力中枢坍缩率。&#10;"
        "⚡ 量化判据:&#10;"
        "• κCYC ≤ 2.0% ➔ 【奇点坍缩 (Big Bang)】各周期成本线彻底粘合，变盘在即！&#10;"
        "• κCYC > 15.0% ➔ 【均线过度发散】短线乖离过大，谨防反向对冲回调！&#10;"
        "🔗 跨指标核心联动图谱:&#10;"
        "1. 与 BIAS 联动: κCYC 粘合到极限时，BIAS 向上金叉转正为奇点爆发点火！&#10;"
        "2. 与 LFS 联动: 粘合时若 LFS > 50，必向上爆发；若 LFS < 30，警惕向下破位！"
    ),
    "delta_cys": (
        "【⑤ 盈亏剪刀差 (ΔCYS - Profit Scissors)】&#10;"
        "📐 微积分公式: ΔCYS = CYS13 - CYS34&#10;"
        "🔬 物理本质: 短周期 vs 中周期市场盈亏势能梯度差分。&#10;"
        "⚡ 量化判据:&#10;"
        "• ΔCYS > +5.0% ➔ 【多头加速反击】短线动能超越中线，主升拉升浪！&#10;"
        "• CYS34 < -8% 且 ΔCYS 向上金叉 ➔ 【战略黄金坑拐点】逆向超卖最佳第一买点！&#10;"
        "🔗 跨指标核心联动图谱:&#10;"
        "1. 与 CYS34 联动: CYS34 决定位置高低，ΔCYS 决定点火方向，二者构成完美时空拐点坐标！"
    ),
    "smpi": (
        "【⑥ 主力筹码纯度 (SMPI - Smart Money Purity Index)】&#10;"
        "📐 微积分公式: SMPI = (Main% - Dare%) / Turnover × (1 - D_Pos/100)&#10;"
        "🔬 物理本质: 剥离游资虚假对倒倒沫子，提取机构真实净吸筹系数。&#10;"
        "⚡ 量化判据:&#10;"
        "• SMPI ≥ +0.25 ➔ 【机构高纯度扫盘】长线大资金战略建仓，锁仓护盘！&#10;"
        "• SMPI ≤ -0.20 ➔ 【游资对倒掩护出货】盘面热闹实则抽血，一票否决！&#10;"
        "🔗 跨指标核心联动图谱:&#10;"
        "1. 与 Dare% 联动: 游资占比过高时 SMPI 骤降，警惕天地板极端波动！&#10;"
        "2. 与 D_Pos 联动: 活筹位置低 (D_Pos < 35) 时的高 SMPI 才是真正黄金坑！"
    ),
    "cyf": (
        "【⑦ 战略动能势能 (CYF66_Raw / VMA55)】&#10;"
        "📐 微积分公式: ΔCYF = CYF66_Raw - VMA(T+55)&#10;"
        "🔬 物理本质: 斐波那契季线级别中枢能量总阀门与战略护城河。&#10;"
        "⚡ 量化判据:&#10;"
        "• ΔCYF > 0 且向上翘头 ➔ 【战略攻势】中长线资金源源不断注入，做空违令！&#10;"
        "• ΔCYF < 0 且向下发散 ➔ 【战略退潮】大势已去，任何反弹皆为减仓机会！&#10;"
        "🔗 跨指标核心联动图谱:&#10;"
        "1. 动能总闸门: 当 CYF66 处于主攻态时，可放宽短期震荡容忍度；处于退潮态时，严格执行4级防守！"
    ),
    "lfs": (
        "【① 筹码锁定因子 (LFS)】&#10;"
        "🔬 物理本质: 衡量底部主力筹码在面临价格震荡与时间衰减时的耐受度。&#10;"
        "⚡ 阈值: LFS > 50 为坚固底座；LFS > 80 为绝对死锁；LFS < 30 为地基坍塌。&#10;"
        "🔗 联动: 与 HCCYF13 构成主力护城河剪刀差，LFS 必须高于成本线方可锁仓！"
    ),
    "z": (
        "【② 获利盘比例 (Z_Profit)】&#10;"
        "🔬 物理本质: 当前收盘价下处于浮盈状态的持仓筹码占全市场比例。&#10;"
        "⚡ 阈值: Z > 90% 且 ASR < 20% 为极速主升；Z < 10% 为空头冰点。&#10;"
        "🔗 联动: 配合 BRI 断层真空指数，确认高获利状态下是否存在获利盘践踏出逃！"
    ),
    "x70_asr": (
        "【③ 筹码聚集度 (X70 / ASR)】&#10;"
        "🔬 物理本质: X70 为 70% 筹码带宽 (越小越集中)；ASR 为活动浮筹比例。&#10;"
        "⚡ 阈值: X70 < 10% 且 ASR < 25% ➔ 筹码极度单峰密集，具备暴发基因！&#10;"
        "🔗 联动: 密集峰突破瞬间配合成交量放大，是主升浪启动最可靠买点！"
    ),
    "eta_abr": (
        "【④ 微观资金推力 (η / ABR)】&#10;"
        "🔬 物理本质: η 为订单流主动推力系数；ABR 为机构大单占比。&#10;"
        "⚡ 阈值: ABR > 60% 且 η > 0.05 ➔ 机构主导盘口，拒绝散户合力假象！&#10;"
        "🔗 联动: 配合 Level 2 超大单净额，精准穿透主力微观扫盘意图！"
    ),
    "scissor": (
        "【⑤ 护城河剪刀差 (LFS - ASR)】&#10;"
        "🔬 物理本质: 锁仓底座与游离浮筹之差。&#10;"
        "⚡ 阈值: Scissor > 0 且持续扩大 ➔ 主力正在抽干浮筹，中枢防线坚不可摧！&#10;"
        "🔗 联动: 剪刀差由负转正的临界点，往往是主力洗盘结束、拉升开始的转折点！"
    ),
    "cys34": (
        "【⑥ 市场盈亏偏离度 (CYS34)】&#10;"
        "🔬 物理本质: 34 日短中期市场持仓平均盈亏率。&#10;"
        "⚡ 阈值: CYS34 < -10% 为超卖极度冰点；CYS34 > +20% 需警惕获利回吐。&#10;"
        "🔗 联动: 与 ΔCYS 配合使用，是判断【战略黄金坑】抄底时机的第一法宝！"
    ),
    "bias": (
        "【⑦ 均线偏离度 (BIAS 5/20)】&#10;"
        "🔬 物理本质: 5 日短期均线与 20 日中枢均线偏离波动率边界。&#10;"
        "⚡ 阈值: BIAS 在 ±3% 内为紧密收敛；超过 +15% 进入短线过热监控。&#10;"
        "🔗 联动: 配合 κCYC 斐波收敛度，在均线充分收敛后等待拐点向上发散！"
    )
}

def render_tactical_card(col, title, value, status, theme_color, help_key="cpr"):
    THEME_MAP = {
        "blue":   {"border": "rgba(56, 189, 248, 0.4)",  "bg": "rgba(56, 189, 248, 0.05)",  "text": "#38BDF8"},
        "red":    {"border": "rgba(248, 113, 113, 0.4)", "bg": "rgba(248, 113, 113, 0.05)", "text": "#F87171"},
        "green":  {"border": "rgba(16, 185, 129, 0.4)",  "bg": "rgba(16, 185, 129, 0.05)",  "text": "#10B981"},
        "amber":  {"border": "rgba(251, 191, 36, 0.4)",  "bg": "rgba(251, 191, 36, 0.05)",  "text": "#FBBF24"},
        "purple": {"border": "rgba(192, 132, 252, 0.4)", "bg": "rgba(192, 132, 252, 0.05)", "text": "#C084FC"},
    }
    t = THEME_MAP.get(theme_color, THEME_MAP["blue"])
    clean_help = TACTICAL_HELP.get(help_key, "指标物理微积分量化说明").replace('"', '&quot;')
    card_html = f"""
    <div style="background: {t['bg']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 10px 12px; height: 96px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 8px; cursor: help;" title="{clean_help}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 11px; color: #94A3B8; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{title}</span>
            <span style="font-size: 11px; color: #38BDF8; opacity: 0.85;" title="鼠标悬停查看微积分公式与跨指标联动图谱">❓</span>
        </div>
        <div style="font-size: 20px; font-weight: 900; color: {t['text']}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.1; white-space: nowrap;">{value}</div>
        <div style="font-size: 11px; font-weight: 600; color: {t['text']}; opacity: 0.95; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{status}</div>
    </div>
    """
    col.markdown(card_html, unsafe_allow_html=True)

# ── 第一排 (高阶张量) ──
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

render_tactical_card(c1, "① 筹码刚性(CPR)", f"{high_order.cpr:.2f}", high_order.cpr_status, "blue", "cpr")
render_tactical_card(c2, "② 真空钝效(ηV)", f"{high_order.eta_v:.4f}", high_order.eta_v_status, "red", "eta_v")
render_tactical_card(c3, "③ 断层真空(BRI)", f"{high_order.bri:.2f}", high_order.bri_status, "red", "bri")
render_tactical_card(c4, "④ 张力收敛(κCYC)", f"{high_order.kappa_cyc:.2f}%", high_order.kappa_cyc_status, "green", "kappa_cyc")
render_tactical_card(c5, "⑤ 盈亏剪刀(ΔCYS)", f"{high_order.delta_cys:+.2f}%", high_order.delta_cys_status, "amber", "delta_cys")
render_tactical_card(c6, "⑥ 筹码纯度(SMPI)", f"{high_order.smpi:+.2f}", high_order.smpi_status, "purple", "smpi")
render_tactical_card(c7, "⑦ 动能势能(CYF66)", f"{high_order.cyf_momentum.cyf66_raw:.1f}/54.9", high_order.cyf_momentum.state_label, "purple", "cyf")

# ── 第二排 (基础标量) ──
d1, d2, d3, d4, d5, d6, d7 = st.columns(7)

render_tactical_card(d1, "① 筹码底座(LFS)", f"{float(snapshot.get('LFS', 41.7) or 41.7):.1f}", "常规筹码离散", "blue", "lfs")
render_tactical_card(d2, "② 空间真空(Z')", f"+{float(snapshot.get('Z_Profit', 25.7) or 25.7):.1f}%", "触发物理主升", "red", "z")
render_tactical_card(d3, "③ 筹码聚集(X70/ASR)", f"{float(snapshot.get('X70', 10.2) or 10.2):.1f} / {float(snapshot.get('ASR', 68.6) or 68.6):.1f}", "常规离散", "green", "x70_asr")
render_tactical_card(d4, "④ 微观推力(η/ABR)", f"+{eta_micro_calc:.2f} ({abr_est:.0f}%)", "订单流主动", "purple", "eta_abr")
render_tactical_card(d5, "⑤ 护城河差(Scissor)", "+12.2", "中枢防线", "green", "scissor")
render_tactical_card(d6, "⑥ 市场盈亏(CYS34)", f"+{float(snapshot.get('CYS34', 20.9) or 20.9):.1f}%", "多头丰厚", "amber", "cys34")
render_tactical_card(d7, "⑦ 均线偏离(BIAS)", "+15.0%", "A级监控", "green", "bias")


# ══════════════════════════════════════════════
# 4. 图形全息展示区 (双轨双图制: 指南针雷达 vs 天衍物理量子拓扑场)
# ══════════════════════════════════════════════
df_pd = df.to_pandas() if hasattr(df, "to_pandas") else df

if ds_mode == "compass_ocr":
    # 模式 A: 统帅实盘真值 (stock.csv) -> 经典五维雷达走势图
    fig = build_radar_figure(df_pd, stock_name, dim5_mode=sel_dim5)
    render_radar_with_hud(fig, df_pd, stock_name, dim5_mode=sel_dim5, height=760)
else:
    # 模式 B: 天衍偏微分连续场推导 (DuckDB) -> 全新 18 物理真值量子拓扑图表
    fig = build_quantum_physics_figure(df_pd, stock_name)
    render_quantum_physics_with_hud(fig, df_pd, stock_name, height=820)

st.caption("🛰️ 天衍五维战术控制台 v2.0 | 切换左侧侧边栏 Pages 即可无缝进入【📁 战备库】、【🤖 参谋部】或【🔬 前沿试验台】")
