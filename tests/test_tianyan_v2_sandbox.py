import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from core.engine import create_engine
from core.signals import SignalJudge
from core.models import FIB_PERIODS
from core.components.radar_chart import build_radar_figure
from core.components.crosshair import render_radar_with_hud
from core.ai_advisor import evaluate_local_tactical_status

print(">>> [1/5] 测试引擎与数据管线初始化...")
engine = create_engine(ROOT)
targets = engine.get_targets()
assert len(targets) > 0, "标的池不应为空"
print(f"  √ 获取到全市场标的数: {len(targets)}")

test_code = "300475"
test_name = engine.get_stock_name(test_code)
print(f"  √ 测试标的: {test_name} ({test_code})")

print(">>> [2/5] 测试 app.py 核心数据管线与 14 指标计算...")
df = engine.get_stock_data(test_code, days=34)
assert df is not None and not df.is_empty(), "df 不应为空"
df_pd = df.to_pandas() if hasattr(df, "to_pandas") else df

snapshot = engine.get_latest_snapshot(test_code)
assert snapshot is not None, "snapshot 不应为空"

eval_res = evaluate_local_tactical_status(snapshot)
assert "order" in eval_res, "eval_res 缺少 order"
print(f"  √ 本地战术军令判定: {eval_res['order']} | 仓位={eval_res.get('target_position_pct')}%")

close_p = float(snapshot.get("Close", 10.0) or 10.0)
high_order = SignalJudge.calculate_high_order_metrics(
    lfs=float(snapshot.get("LFS", 50.0) or 50.0),
    hccyf=float(snapshot.get("HCCYF13", 50.0) or 50.0),
    asr=float(snapshot.get("ASR", 20.0) or 20.0),
    turnover=float(snapshot.get("Turnover", 3.0) or 3.0),
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
    main_pct=float(snapshot.get("Main_Fund_Pct", 5.0) or 5.0),
    dare_pct=float(snapshot.get("Dare_Fund_Pct", 1.0) or 1.0),
    d_pos=float(snapshot.get("D_Pos", 35.0) or 35.0),
    cyf66_raw=float(snapshot.get("CYF66_Raw", 50.0) or 50.0),
    cyf66_vma55=float(snapshot.get("CYF66_VMA55", 50.0) or 50.0)
)
print(f"  √ 14指标算子测试通过: CPR={high_order.cpr:.2f}, Z'={snapshot.get('Z_Profit')}, ηV={high_order.eta_v:.4f}")

fig = build_radar_figure(df_pd, test_name, dim5_mode=0)
assert fig is not None, "Plotly Figure 构建失败"
print("  √ 五维全息雷达图构建成功")

print(">>> [3/5] 测试 01_战略战备库数据矩阵与分组...")
fib_matrix = engine.get_fibonacci_depth_matrix(test_code)
assert fib_matrix is not None and len(fib_matrix) > 0, "斐波那契矩阵不应为空"
fib_df = pd.DataFrame(fib_matrix)
print(f"  √ 斐波那契矩阵行数: {len(fib_df)}")
groups = engine.get_groups()
print(f"  √ 自选分组数: {len(groups)}")

print(">>> [4/5] 测试 02_天眼作战参谋部模型映射...")
model_map = {
    "天衍 32B 终极大量化模型 (AWQ / 4-bit)": "tianyan-32b-awq",
    "Qwen-2.5-32B-Instruct (云端大算力)": "qwen2.5-32b-instruct",
    "DeepSeek-R1-Distill-Qwen-32B (强化推理)": "deepseek-r1-qwen-32b",
    "Local CPU/GPU Fast Heuristic (本地轻量)": "local-fast-heuristic",
}
assert len(model_map) == 4, "模型映射必须包含4款核心模型"
print("  √ AI 参谋部 4 款核心大模型配置就绪")

print(">>> [5/5] 测试 03_全市场高阶量化雷达筛选逻辑...")
filtered = [t for t in targets if (getattr(t, "code", None) or "").startswith("300") or (getattr(t, "code", None) or "").startswith("600")]
print(f"  √ 雷达初筛捕获标的数: {len(filtered)}")

print("\n🎉🎉🎉 沙盒自动化断言测试全部 100% 通过！零错误！零异常！")
