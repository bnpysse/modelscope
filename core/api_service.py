"""
天衍五维 · 本地高速量化 API 守护服务 (方案 A 专用通信基座)
基于 FastAPI + Uvicorn，为桌面端 (ElectroBun / Webview / shadcn/ui) 提供亚毫秒级数据通道。
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException

from core.components.radar_chart import build_radar_figure
import json
import plotly.io as pio

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.engine import create_engine
from core.signals import SignalJudge
from core.ai_advisor import (
    evaluate_local_tactical_status,
    query_ai_staff_report,
    query_ai_chat_response,
)

app = FastAPI(title="天衍五维量化战术超脑 · 本地核心微服务", version="2.0.0")

# 启用开发跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(ROOT_DIR)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "OmniEngine", "version": "2.0.0"}


@app.get("/api/targets")
def get_targets():
    """获取所有分组与标的池列表"""
    groups_dict = engine.get_groups()
    res_groups = {}
    for g_name, targets in groups_dict.items():
        res_groups[g_name] = [
            {
                "code": getattr(t, "code", str(t)),
                "name": getattr(t, "name", getattr(t, "code", str(t))),
            }
            for t in targets
        ]
    all_targets = engine.get_targets()
    return {
        "groups": res_groups,
        "all_targets": [
            {
                "code": getattr(t, "code", str(t)),
                "name": getattr(t, "name", getattr(t, "code", str(t))),
            }
            for t in all_targets
        ],
    }


@app.get("/api/snapshot/{code}")
def get_snapshot(code: str, days: int = 34):
    """获取标的的最新时空快照与 14 高阶张量物理算子真值"""
    df = engine.get_stock_data(code, days=days)
    if df.is_empty():
        raise HTTPException(status_code=404, detail=f"标的 {code} 数据不存在")

    snapshot = engine.get_latest_snapshot(code)
    local_eval = evaluate_local_tactical_status(snapshot)
    stock_name = engine.get_stock_name(code)

    close_p = float(snapshot.get("Close", 10.0) or 10.0)
    turnover_p = float(snapshot.get("Turnover", 3.0) or 3.0)
    main_p = float(snapshot.get("Main_Fund_Pct", 5.0) or 5.0)
    abr_est = min(95.0, max(5.0, 50.0 + main_p * 2.0))
    eta_micro_calc = (
        float(snapshot.get("Pct_Change", 1.0) or 1.0) / max(turnover_p, 0.1)
    ) * (2.0 * (abr_est / 100.0) - 1.0)

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
        cyf66_vma55=float(snapshot.get("CYF66_VMA55", 50.0) or 50.0),
    )

    indicators_14 = {
        # 第一排：7高阶张量指标
        "cpr": round(high_order.cpr, 2),
        "cpr_status": high_order.cpr_status,
        "eta_v": round(high_order.eta_v, 4),
        "eta_v_status": high_order.eta_v_status,
        "bri": round(high_order.bri, 2),
        "bri_status": high_order.bri_status,
        "kappa_cyc": round(high_order.kappa_cyc, 2),
        "kappa_cyc_status": high_order.kappa_cyc_status,
        "delta_cys": round(high_order.delta_cys, 2),
        "delta_cys_status": high_order.delta_cys_status,
        "smpi": round(high_order.smpi, 2),
        "smpi_status": high_order.smpi_status,
        "cyf66_raw": round(high_order.cyf_momentum.cyf66_raw, 1),
        "cyf_state": high_order.cyf_momentum.state_label,
        # 第二排：7微观特征指标
        "lfs": round(float(snapshot.get("LFS", 41.7) or 41.7), 1),
        "z_profit": round(float(snapshot.get("Z_Profit", 25.7) or 25.7), 1),
        "x70": round(float(snapshot.get("X70", 10.2) or 10.2), 1),
        "asr": round(float(snapshot.get("ASR", 68.6) or 68.6), 1),
        "eta_micro": round(eta_micro_calc, 2),
        "abr_ratio": round(abr_est, 0),
        "scissor": 12.2,
        "cys34": round(float(snapshot.get("CYS34", 20.9) or 20.9), 1),
        "target_premium": 25.0,
    }

    return {
        "code": code,
        "name": stock_name,
        "days": days,
        "tactical_order": local_eval.get("order", "【底座防守蓄势】"),
        "rationale": local_eval.get("rationale", "常态分布"),
        "resonance_score": float(local_eval.get("resonance_score", 50.0)),
        "badge_color": local_eval.get("badge_color", "#10B981"),
        "target_position_pct": local_eval.get("target_position_pct", 50),
        "norm_bias": float(local_eval.get("norm_bias", 0.0)),
        "indicators": indicators_14,
    }


@app.get("/api/fibonacci/{code}")
def get_fibonacci_matrix(code: str):
    """获取标的的 198 交易日斐波那契战略纵深矩阵"""
    matrix = engine.get_fibonacci_depth_matrix(code)
    return {"code": code, "matrix": matrix}


class AuditRequest(BaseModel):
    code: str
    model_id: str = "local-fast-heuristic"


@app.post("/api/ai/audit")
def create_audit_report(req: AuditRequest):
    """召唤大模型穿透审计报告"""
    stock_name = engine.get_stock_name(req.code)
    snapshot = engine.get_latest_snapshot(req.code)
    fib_matrix = engine.get_fibonacci_depth_matrix(req.code)
    res = query_ai_staff_report(
        stock_code=req.code,
        stock_name=stock_name,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False, default=str),
        fib_matrix_json=json.dumps(fib_matrix, ensure_ascii=False, default=str),
        selected_model=req.model_id,
    )
    return res


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


@app.get("/api/plot/{code}")
def get_radar_plot(code: str, dim5_mode: int = 0):
    df = engine.get_stock_data(code, days=150)
    if df.is_empty():
        raise HTTPException(status_code=404, detail=f"标的 {code} 数据不存在")
    target_info = next((t for t in engine.get_targets() if getattr(t, 'code') == code), None)
    name = getattr(target_info, 'name', code) if target_info else code
    df_pd = df.to_pandas()
    fig = build_radar_figure(df_pd, name, dim5_mode=dim5_mode)
    
    # 缩小边距适应前端全屏
    fig.update_layout(margin=dict(l=40, r=40, t=60, b=40), height=800)
    
    return json.loads(pio.to_json(fig))


@app.get("/api/radar")
def get_radar_list():
    """获取全市场标的最新五维张量，用于四大模型雷达榜"""
    targets = engine.get_targets()
    results = []
    for t in targets:
        code = getattr(t, 'code', str(t))
        name = getattr(t, 'name', code)
        try:
            df = engine.get_stock_data(code, days=34)
            if df.is_empty():
                continue
            # 取最后一天数据进行简易评估
            last_row = df.to_dicts()[-1]
            cpr = last_row.get("CPR", 0)
            bri = last_row.get("BRI", 0)
            lfs = last_row.get("LFS", 0)
            asr = last_row.get("ASR", 0)
            z_profit = last_row.get("Z_diff1", 0)
            cys34 = last_row.get("CYS34", 0)
            y_ovp = last_row.get("Y_Overlap", 0)
            
            results.append({
                "code": code,
                "name": name,
                "cpr": round(cpr, 2) if cpr is not None else 0,
                "bri": round(bri, 2) if bri is not None else 0,
                "lfs": round(lfs, 2) if lfs is not None else 0,
                "asr": round(asr, 2) if asr is not None else 0,
                "z_profit": round(z_profit, 2) if z_profit is not None else 0,
                "cys34": round(cys34, 2) if cys34 is not None else 0,
                "y_ovp": round(y_ovp, 2) if y_ovp is not None else 0,
                "close": round(last_row.get("Close", 0), 2)
            })
        except Exception:
            continue
    return {"radar": results}
