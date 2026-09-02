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
from core.signals import compute_indicators

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
df = engine.get_security_data(stock_code, days=sel_days)
local_eval = engine.evaluate_tactical_status(df)

# ══════════════════════════════════════════════
# 2. 战术军令条
# ══════════════════════════════════════════════
res_color = "#FFD700" if local_eval.get("resonance_score", 50) >= 80 else "#10B981"
st.markdown(f"""
<div class="tactical-bar">
    <div>
        <span style="background: rgba(239, 68, 68, 0.2); padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-right: 8px;">
            【{local_eval.get('action', '保持观望')}】
        </span>
        {local_eval.get('rationale', '等待五维共振信号触发')}
    </div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #94A3B8;">
        跨周期共振: <b style="color: {res_color};">{local_eval.get('resonance_score', 50):.1f}</b> &nbsp;|&nbsp;
        ΔCYF动能差: <b style="color: #38BDF8;">{local_eval.get('cyf_momentum_diff', 0.0):+.2f}</b> &nbsp;|&nbsp;
        Norm_BIAS: <b style="color: #F8FAFC;">{local_eval.get('norm_bias', 0.0):.2f}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 3. 14 核心物理真值指标卡片 (7+7 双排紧凑网格)
# ══════════════════════════════════════════════
inds = compute_indicators(df) if (df is not None and not df.empty) else {}

cpr_v     = inds.get("cpr", 0.0)
eta_v     = inds.get("eta_v", 0.0)
bri_v     = inds.get("bri", 0.0)
kappa_v   = inds.get("kappa_cyc", 0.0)
delta_cys = inds.get("delta_cys", 0.0)
smpi_v    = inds.get("smpi", 0.0)
cyf66_v   = inds.get("cyf66", 0.0)

lfs_v     = inds.get("lfs", 41.7)
z_vac     = inds.get("z_vacuum", 25.7)
x70_v     = inds.get("x70", 10.2)
asr_v     = inds.get("asr", 68.6)
eta_abr   = inds.get("eta_abr", 0.02)
abr_pct   = inds.get("abr_ratio", 60.0)
scissor   = inds.get("moat_scissor", 12.2)
cys34_v   = inds.get("cys34", 20.9)
target_prem = inds.get("report_target_premium", 25.0)

st.markdown(f"""
<div class="indicator-grid">
  <!-- 第一排: 高阶张量衍生指标 (7个) -->
  <div class="indicator-card">
    <div class="indicator-title">① 筹码刚性 (CPR)</div>
    <div class="indicator-val" style="color:#F59E0B;">{cpr_v:.2f}</div>
    <div class="indicator-sub">【超导死锁态】</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">② 真空钝效 (ηV)</div>
    <div class="indicator-val" style="color:#EF4444;">{eta_v:.4f}</div>
    <div class="indicator-sub">【大量磨损滑泡】</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">③ 断层真空 (BRI)</div>
    <div class="indicator-val" style="color:#F87171;">{bri_v:.2f}</div>
    <div class="indicator-sub">【筹码断裂崩塌】</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">④ 张力收敛 (κCYC)</div>
    <div class="indicator-val" style="color:#F59E0B;">{kappa_v:.2f}%</div>
    <div class="indicator-sub">【均线过度发散】</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑤ 盈亏剪刀 (ΔCYS)</div>
    <div class="indicator-val" style="color:#34D399;">{delta_cys:+.2f}%</div>
    <div class="indicator-sub">【震荡强推】</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑥ 筹码纯度 (SMPI)</div>
    <div class="indicator-val" style="color:#10B981;">{smpi_v:+.2f}</div>
    <div class="indicator-sub">【集中加仓】</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑦ 动能势能 (CYF66)</div>
    <div class="indicator-val" style="color:#EF4444;">{cyf66_v:.1f}/54.9</div>
    <div class="indicator-sub">【死叉钝化态】</div>
  </div>

  <!-- 第二排: 微观与时空特征指标 (7个) -->
  <div class="indicator-card">
    <div class="indicator-title">① 筹码底座锁定 (LFS)</div>
    <div class="indicator-val" style="color:#94A3B8;">{lfs_v:.1f}</div>
    <div class="indicator-sub">常规筹码离散</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">② 空间获利真空 (Z')</div>
    <div class="indicator-val" style="color:#F59E0B;">+{z_vac:.1f}%</div>
    <div class="indicator-sub">触发物理真空主升</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">③ 筹码聚集 (X70/ASR)</div>
    <div class="indicator-val" style="color:#38BDF8;">{x70_v:.1f}% <span style="font-size:10px;color:#64748B;">/ {asr_v:.1f}</span></div>
    <div class="indicator-sub">常规离散分布</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">④ 微观主力推力 (η/ABR)</div>
    <div class="indicator-val" style="color:#10B981;">+{eta_abr:.2f} <span style="font-size:10px;color:#64748B;">({abr_pct:.0f}%)</span></div>
    <div class="indicator-sub">订单流主动买盘</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑤ 护城河差 (Scissor)</div>
    <div class="indicator-val" style="color:#38BDF8;">+{scissor:.1f}</div>
    <div class="indicator-sub">中枢常规防线</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑥ 市场盈亏 (CYS34)</div>
    <div class="indicator-val" style="color:#F59E0B;">+{cys34_v:.1f}%</div>
    <div class="indicator-sub">多头获利丰厚</div>
  </div>
  <div class="indicator-card">
    <div class="indicator-title">⑦ 研报目标溢价</div>
    <div class="indicator-val" style="color:#F59E0B;">+{target_prem:.1f}%</div>
    <div class="indicator-sub">A级 (常规机构看多)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 4. 图形全息展示区 (100% 满屏无遮挡: 五维雷达波形图 + HUD 看板)
# ══════════════════════════════════════════════
fig = build_radar_figure(df, stock_name, dim5_mode=sel_dim5)
render_radar_with_hud(fig, df, stock_name, dim5_mode=sel_dim5, height=760)

st.caption("🛰️ 天衍五维战术控制台 v2.0 | 切换左侧侧边栏 Pages 即可无缝进入【📁 天衍战略战备库】或【🤖 天眼作战参谋部】")
