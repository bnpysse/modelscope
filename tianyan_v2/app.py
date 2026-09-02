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
    render_top_control_bar
)
from core.components.radar_chart import build_radar_figure
from core.components.crosshair import render_radar_with_hud
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
# 1. 顶部作战控制台 (全局参数总线)
# ══════════════════════════════════════════════
ctrl = render_top_control_bar(engine, title_prefix="🛸 天衍五维 · 全息作战总台")
stock_code = ctrl["stock_code"]
stock_name = ctrl["stock_name"]
sel_days   = ctrl["days"]
sel_dim5   = ctrl["dim5"]

# 数据拉取与特征推演
df = engine.get_stock_data(stock_code, days=sel_days)
if df.is_empty():
    st.error(f"⚠️ 未找到标的 {stock_code} 的时空数据。")
    st.stop()

snapshot = engine.get_latest_snapshot(stock_code)
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

st.markdown(f"""
<div class="indicator-grid">
  <!-- 第一排: 高阶张量衍生指标 (7个) -->
  <div class="indicator-card">
    <div class="indicator-title">① 筹码刚性 (CPR)</div>
    <div class="indicator-val" style="color:#F59E0B;">{high_order.cpr:.2f}</div>
    <div class="indicator-sub">{high_order.cpr_state}</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">② 真空钝效 (ηV)</div>
    <div class="indicator-val" style="color:#EF4444;">{high_order.eta_v:.4f}</div>
    <div class="indicator-sub">{high_order.eta_v_state}</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">③ 断层真空 (BRI)</div>
    <div class="indicator-val" style="color:#F87171;">{high_order.bri:.2f}</div>
    <div class="indicator-sub">{high_order.bri_state}</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">④ 张力收敛 (κCYC)</div>
    <div class="indicator-val" style="color:#F59E0B;">{high_order.kappa_cyc:.2f}%</div>
    <div class="indicator-sub">{high_order.kappa_state}</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑤ 盈亏剪刀 (ΔCYS)</div>
    <div class="indicator-val" style="color:#34D399;">{high_order.delta_cys:+.2f}%</div>
    <div class="indicator-sub">{high_order.delta_cys_state}</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑥ 筹码纯度 (SMPI)</div>
    <div class="indicator-val" style="color:#10B981;">{high_order.smpi:+.2f}</div>
    <div class="indicator-sub">{high_order.smpi_state}</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑦ 动能势能 (CYF66)</div>
    <div class="indicator-val" style="color:#EF4444;">{high_order.cyf_momentum.cyf66_raw:.1f}/54.9</div>
    <div class="indicator-sub">{high_order.cyf_momentum.state_label}</div>
  </div>

  <!-- 第二排: 微观与时空特征指标 (7个) -->
  <div class="indicator-card">
    <div class="indicator-title">① 筹码底座锁定 (LFS)</div>
    <div class="indicator-val" style="color:#94A3B8;">{float(snapshot.get("LFS", 41.7) or 41.7):.1f}</div>
    <div class="indicator-sub">常规筹码离散</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">② 空间获利真空 (Z')</div>
    <div class="indicator-val" style="color:#F59E0B;">+{float(snapshot.get("Z_Profit", 25.7) or 25.7):.1f}%</div>
    <div class="indicator-sub">触发物理真空主升</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">③ 筹码聚集 (X70/ASR)</div>
    <div class="indicator-val" style="color:#38BDF8;">{float(snapshot.get("X70", 10.2) or 10.2):.1f}% <span style="font-size:10px;color:#64748B;">/ {float(snapshot.get("ASR", 68.6) or 68.6):.1f}</span></div>
    <div class="indicator-sub">常规离散分布</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">④ 微观主力推力 (η/ABR)</div>
    <div class="indicator-val" style="color:#10B981;">+{eta_micro_calc:.2f} <span style="font-size:10px;color:#64748B;">({abr_est:.0f}%)</span></div>
    <div class="indicator-sub">订单流主动买盘</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑤ 护城河差 (Scissor)</div>
    <div class="indicator-val" style="color:#38BDF8;">+12.2</div>
    <div class="indicator-sub">中枢常规防线</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑥ 市场盈亏 (CYS34)</div>
    <div class="indicator-val" style="color:#F59E0B;">+{float(snapshot.get("CYS34", 20.9) or 20.9):.1f}%</div>
    <div class="indicator-sub">多头获利丰厚</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑦ 研报目标溢价</div>
    <div class="indicator-val" style="color:#F59E0B;">+25.0%</div>
    <div class="indicator-sub">A级 (常规机构看多)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 4. 图形全息展示区 (100% 满屏无遮挡: 五维雷达波形图 + HUD 看板)
# ══════════════════════════════════════════════
df_pd = df.to_pandas() if hasattr(df, "to_pandas") else df
fig = build_radar_figure(df_pd, stock_name, dim5_mode=sel_dim5)
render_radar_with_hud(fig, df_pd, stock_name, dim5_mode=sel_dim5, height=760)

st.caption("🛰️ 天衍五维战术控制台 v2.0 | 切换左侧侧边栏 Pages 即可无缝进入【📁 天衍战略战备库】或【🤖 天眼作战参谋部】")
