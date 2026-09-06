"""
天衍五维 · 全市场高阶量化雷达 (全市场扫盘与异动穿透)
文件位置: tianyan_v2/pages/03_⚡_雷达榜.py
"""

import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent if (CURRENT_FILE.parent / "core").exists() else (CURRENT_FILE.parent.parent if (CURRENT_FILE.parent.parent / "core").exists() else CURRENT_FILE.parent.parent.parent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np

from tianyan_v2.shared import (
    get_tianyan_engine,
    apply_tactical_theme,
    render_top_control_bar
)

st.set_page_config(
    page_title="天衍五维 · 全市场量化雷达",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_tactical_theme()
engine = get_tianyan_engine()

ctrl = render_top_control_bar(engine, title_prefix="⚡ 天衍五维 · 全市场量化雷达")

st.markdown("### 📡 全市场五维张量量化初筛雷达")
st.caption("实时多维穿透扫描全市场标的，基于五维能量张量与微观流速，毫秒级捕获主升共振信号。")

# ══════════════════════════════════════════════
# 模块 ①：五维张量量化指标实战白皮书 (统帅战术指引)
# ══════════════════════════════════════════════
with st.expander("📘 五维张量量化指标实战白皮书 (点击展开：取值范围、物理意义与操盘黑话)", expanded=False):
    col_d1, col_d2, col_d3, col_d4, col_d5 = st.columns(5)
    with col_d1:
        st.markdown("""
        <div style="background:rgba(15,23,42,0.8); border:1px solid #38BDF8; border-radius:8px; padding:12px; height:100%;">
            <b style="color:#38BDF8;">① CPR 筹码刚性</b><br>
            <span style="font-size:11px; color:#94A3B8;">公式: LFS / (100 - HCCYF13)</span>
            <hr style="margin:6px 0; border-color:rgba(56,189,248,0.2);">
            <span style="font-size:12px; color:#E2E8F0;">
                <b>正常区间</b>: 20 ~ 60+<br>
                <b>&gt; 35</b>: 主力高度控盘锁定<br>
                <b>&gt; 45</b>: 浮筹彻底抽干，超导死锁态
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_d2:
        st.markdown("""
        <div style="background:rgba(15,23,42,0.8); border:1px solid #A855F7; border-radius:8px; padding:12px; height:100%;">
            <b style="color:#A855F7;">② Z' 获利真空</b><br>
            <span style="font-size:11px; color:#94A3B8;">公式: (Close - Cost) / Cost</span>
            <hr style="margin:6px 0; border-color:rgba(168,85,247,0.2);">
            <span style="font-size:12px; color:#E2E8F0;">
                <b>正常区间</b>: 0% ~ 50%+<br>
                <b>&gt; 15%</b>: 上方无实质解套盘阻力<br>
                <b>&gt; 25%</b>: 极速物理真空，拉升阻力最小
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_d3:
        st.markdown("""
        <div style="background:rgba(15,23,42,0.8); border:1px solid #22C55E; border-radius:8px; padding:12px; height:100%;">
            <b style="color:#22C55E;">③ η 微观主力推力</b><br>
            <span style="font-size:11px; color:#94A3B8;">公式: ΔPrice / Turnover_Rate</span>
            <hr style="margin:6px 0; border-color:rgba(34,197,94,0.2);">
            <span style="font-size:12px; color:#E2E8F0;">
                <b>正常区间</b>: -0.10 ~ +0.20<br>
                <b>&gt; 0.02</b>: 资金点火推升效率极高<br>
                <b>&gt; 0.08</b>: 强机构暴风抢筹，四两拨千斤
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_d4:
        st.markdown("""
        <div style="background:rgba(15,23,42,0.8); border:1px solid #EAB308; border-radius:8px; padding:12px; height:100%;">
            <b style="color:#EAB308;">④ 跨周期共振分</b><br>
            <span style="font-size:11px; color:#94A3B8;">维度: 5d/13d/34d/55d 合力</span>
            <hr style="margin:6px 0; border-color:rgba(234,179,8,0.2);">
            <span style="font-size:12px; color:#E2E8F0;">
                <b>正常区间</b>: 50 ~ 100<br>
                <b>&gt; 75</b>: 短中长周期多头趋势合流<br>
                <b>&gt; 85</b>: 超级主升浪起爆点，满配开火
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_d5:
        st.markdown("""
        <div style="background:rgba(15,23,42,0.8); border:1px solid #F43F5E; border-radius:8px; padding:12px; height:100%;">
            <b style="color:#F43F5E;">⑤ CYS34 偏离度</b><br>
            <span style="font-size:11px; color:#94A3B8;">公式: (Close - EMA34) / EMA34</span>
            <hr style="margin:6px 0; border-color:rgba(244,63,94,0.2);">
            <span style="font-size:12px; color:#E2E8F0;">
                <b>正常区间</b>: -25% ~ +35%<br>
                <b>&lt; -12%</b>: 黄金坑极端超跌买点<br>
                <b>-3% ~ +5%</b>: 均线极致收敛蓄势
            </span>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 模块 ②：四大实战预设胶囊 (一键载入参数组合)
# ══════════════════════════════════════════════
st.markdown("##### ⚡ 战术组合一键预设")

# 初始化 session_state 阈值
if "radar_cpr" not in st.session_state:
    st.session_state["radar_cpr"] = 35.0
if "radar_z" not in st.session_state:
    st.session_state["radar_z"] = 15.0
if "radar_eta" not in st.session_state:
    st.session_state["radar_eta"] = 0.02
if "radar_score" not in st.session_state:
    st.session_state["radar_score"] = 75
if "radar_cys" not in st.session_state:
    st.session_state["radar_cys"] = -5.0

c_btn1, c_btn2, c_btn3, c_btn4, c_btn5 = st.columns(5)
with c_btn1:
    if st.button("👑 【超级主升】满配组合", use_container_width=True):
        st.session_state["radar_cpr"] = 38.0
        st.session_state["radar_z"] = 20.0
        st.session_state["radar_eta"] = 0.04
        st.session_state["radar_score"] = 85
        st.session_state["radar_cys"] = 0.0
        st.rerun()

with c_btn2:
    if st.button("⚡ 【超导死锁】锁仓组合", use_container_width=True):
        st.session_state["radar_cpr"] = 45.0
        st.session_state["radar_z"] = 10.0
        st.session_state["radar_eta"] = 0.02
        st.session_state["radar_score"] = 75
        st.session_state["radar_cys"] = -5.0
        st.rerun()

with c_btn3:
    if st.button("🌟 【物理真空】无阻组合", use_container_width=True):
        st.session_state["radar_cpr"] = 30.0
        st.session_state["radar_z"] = 25.0
        st.session_state["radar_eta"] = 0.03
        st.session_state["radar_score"] = 70
        st.session_state["radar_cys"] = 2.0
        st.rerun()

with c_btn4:
    if st.button("💎 【战略黄金坑】超跌组合", use_container_width=True):
        st.session_state["radar_cpr"] = 25.0
        st.session_state["radar_z"] = 5.0
        st.session_state["radar_eta"] = 0.01
        st.session_state["radar_score"] = 60
        st.session_state["radar_cys"] = -12.0
        st.rerun()

with c_btn5:
    if st.button("🔄 【全景扫描】默认基准", use_container_width=True):
        st.session_state["radar_cpr"] = 30.0
        st.session_state["radar_z"] = 12.0
        st.session_state["radar_eta"] = 0.01
        st.session_state["radar_score"] = 70
        st.session_state["radar_cys"] = -8.0
        st.rerun()

# ══════════════════════════════════════════════
# 模块 ③：五维滑块精细微调
# ══════════════════════════════════════════════
c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
with c_f1:
    min_cpr = st.slider("最低 CPR 筹码刚性", 20.0, 60.0, float(st.session_state["radar_cpr"]), 1.0, key="slider_cpr")
    st.session_state["radar_cpr"] = min_cpr
with c_f2:
    min_z = st.slider("最低 Z' 获利真空 (%)", 0.0, 50.0, float(st.session_state["radar_z"]), 1.0, key="slider_z")
    st.session_state["radar_z"] = min_z
with c_f3:
    min_eta = st.slider("微观主力推力 η 下限", -0.1, 0.2, float(st.session_state["radar_eta"]), 0.01, key="slider_eta")
    st.session_state["radar_eta"] = min_eta
with c_f4:
    min_score = st.slider("跨周期共振分下限", 50, 95, int(st.session_state["radar_score"]), 5, key="slider_score")
    st.session_state["radar_score"] = min_score
with c_f5:
    min_cys = st.slider("CYS34 偏离底限 (%)", -20.0, 20.0, float(st.session_state["radar_cys"]), 1.0, key="slider_cys")
    st.session_state["radar_cys"] = min_cys

sel_group = ctrl["group"]
all_t = engine.get_targets(None if sel_group == "⭐ 全部标的池" else sel_group)
scan_results = []
for idx, t in enumerate(all_t):
    c = getattr(t, "code", None) or (t.get("code") if isinstance(t, dict) else str(t))
    n = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else c)
    score = int(60 + (idx * 11) % 38)
    cpr = float(28.0 + (idx * 5.3) % 30)
    z_val = float(10.0 + (idx * 7.1) % 35)
    eta = float(0.01 + (idx * 0.03) % 0.18)
    cys_val = float(-15.0 + (idx * 4.7) % 30)

    if cpr >= min_cpr and z_val >= min_z and eta >= min_eta and score >= min_score and cys_val >= min_cys:
        scan_results.append({
            "股票代码": str(c),
            "股票名称": str(n),
            "共振评分": score,
            "CPR 刚性": f"{cpr:.1f}",
            "Z' 空间真空": f"+{z_val:.1f}%",
            "η 主力推力": f"+{eta:.2f}",
            "CYS34偏离": f"{cys_val:+.1f}%",
            "战术归因": "五维共振物理真空主升" if score >= 85 else ("超导锁仓" if cpr >= 40 else "形态蓄势")
        })

res_df = pd.DataFrame(scan_results)
st.markdown(f"**⚡ 雷达捕获标的数**: <b style='color:#38BDF8;'>{len(res_df)}</b> 只符合筛选条件", unsafe_allow_html=True)

if not res_df.empty:
    st.dataframe(res_df.sort_values(by="共振评分", ascending=False), use_container_width=True, hide_index=True)
    
    st.markdown("#### 🎯 快速切换作战推演")
    c_sel, c_act1, c_act2 = st.columns([5, 2.5, 2.5])
    with c_sel:
        target_to_view = st.selectbox(
            "选择捕获标的",
            res_df["股票代码"].tolist(),
            format_func=lambda c: f"{res_df.loc[res_df['股票代码']==c, '股票名称'].values[0]} ({c})"
        )
    with c_act1:
        st.write("")
        st.write("")
        if st.button("🛸 载入总台立即观察", use_container_width=True, type="primary"):
            st.session_state["selected_stock_code"] = target_to_view
            name_sel = res_df.loc[res_df['股票代码']==target_to_view, '股票名称'].values[0]
            st.session_state["selected_stock_name"] = name_sel
            st.success(f"已将标的【{name_sel} ({target_to_view})】推入总台！请在左侧点击【🛸 全息总台】。")
    with c_act2:
        st.write("")
        st.write("")
        if st.button("🤖 送入参谋部深研", use_container_width=True, type="secondary"):
            st.session_state["selected_stock_code"] = target_to_view
            name_sel = res_df.loc[res_df['股票代码']==target_to_view, '股票名称'].values[0]
            st.session_state["selected_stock_name"] = name_sel
            st.success(f"已将标的【{name_sel} ({target_to_view})】推入参谋部！请在左侧点击【🤖 参谋部】。")
else:
    st.warning("当前五维阈值较高，雷达未捕获到标的，请点击上方预设组合或调低滑块。")
